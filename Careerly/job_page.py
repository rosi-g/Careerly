"""
job_page.py - detail page shown when a user selects one of their top career matches.

What happens here:
- Job title and description are shown alongside a bar chart of all career match scores
- Salary data is fetched from the Adzuna API and displayed as a range bar
- Skill gaps are calculated by comparing the CV against ESCO skill keywords
- Recommended HSG courses are matched to those skill gaps
- Career twin popup shows a well-known professional in that field
- User can confirm or reject the match, which feeds back into the model

JOB_DETAILS and SKILLS_FROM_EXCEL are imported by careerly.py to run the scoring,
so this file doubles as the data layer for the whole app.
"""

import streamlit as st
import base64
import pandas as pd
import os
import requests
import plotly.graph_objects as go
from dotenv import load_dotenv
from translations import t, language_toggle, t_job_detail, t_twin_fact, t_skill

load_dotenv()
from feedback import record_helpful_click, get_click_boost, record_cv_match
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Map job names to search terms for Adzuna
JOB_SEARCH_TERMS = {
    "Financial Analyst": "financial analyst",
    "Corporate Investment Banker": "investment banker",
    "Business Consultant": "management consultant",
    "Marketing Manager": "marketing manager",
    "Data Analyst": "data analyst",
    "ICT Application Developer": "software engineer",
    "Corporate Lawyer": "corporate lawyer",
    "Tax Advisor": "tax lawyer",
    "Human Resources Manager": "human resources manager",
    "Strategic Planning Manager": "operations manager",
    "Product Manager": "product manager",
    "Brand Manager": "brand manager",
    "Supply Chain Manager": "supply chain manager",
    "Entrepreneur": "entrepreneur",
}

@st.cache_data(show_spinner=False, ttl=3600)
def get_swiss_salary(job_name):
    """
    Fetches salary data from Adzuna across 7 Western European countries and converts to CHF.
    Results are cached for 1 hour. Returns a dict with avg, min, max, and count, or None.
    Salaries below 10,000 are filtered out to remove obviously bad data points.
    """
    try:
        search_term = JOB_SEARCH_TERMS.get(job_name, job_name)

        # High-salary Western European countries, converted to CHF
        EUROPEAN_COUNTRIES = {
            "de": 1.05,   # Germany - EUR to CHF
            "at": 1.05,   # Austria - EUR to CHF
            "fr": 1.05,   # France - EUR to CHF
            "nl": 1.05,   # Netherlands - EUR to CHF
            "be": 1.05,   # Belgium - EUR to CHF
            "se": 0.089,  # Sweden - SEK to CHF
            "no": 0.087,  # Norway - NOK to CHF
        }

        all_salaries_chf = []

        for country, rate in EUROPEAN_COUNTRIES.items():
            try:
                url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
                params = {
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_APP_KEY,
                    "what": search_term,
                    "results_per_page": 50,
                }
                response = requests.get(url, params=params, timeout=5)
                data = response.json()
                results = data.get("results", [])
                salaries = [
                    r["salary_max"] * rate for r in results
                    if r.get("salary_max") and r.get("salary_max") > 10000
                ]
                all_salaries_chf.extend(salaries)
            except Exception:
                continue

        if all_salaries_chf:
            avg = round(sum(all_salaries_chf) / len(all_salaries_chf) / 1000) * 1000
            min_s = round(min(all_salaries_chf) / 1000) * 1000
            max_s = round(max(all_salaries_chf) / 1000) * 1000
            return {"avg": avg, "min": min_s, "max": max_s, "count": len(all_salaries_chf)}

        return None
    except Exception:
        return None

def load_skills_from_excel(path="skills_database.xlsx"):
    """
    Loads skill keywords from the Excel database into a dict of job -> list of skills.
    The Job column only appears in the first row of each block, so we forward-fill it.
    Handles both old and new ESCO column naming conventions.
    """
    try:
        df = pd.read_excel(path)
        df["Job"] = df["Job"].ffill()
        skill_col = "Skill Name (ESCO)" if "Skill Name (ESCO)" in df.columns else "Skill Name"
        kw_col = "Keywords" if "Keywords" in df.columns else "Keywords (comma separated)"
        skills_map = {}
        for _, row in df.iterrows():
            job = str(row["Job"]).strip()
            skill = str(row[skill_col]).strip()
            kw_raw = str(row[kw_col]).strip()
            if job and job != "nan" and skill and skill != "nan" and kw_raw != "nan":
                keywords = [kw.strip() for kw in kw_raw.split(",") if kw.strip()]
                if job not in skills_map:
                    skills_map[job] = []
                skills_map[job].append({"name": skill, "keywords": keywords})
        return skills_map
    except Exception as e:
        return {}

SKILLS_FROM_EXCEL = load_skills_from_excel()

@st.cache_data(show_spinner=False)
def load_courses(path="combined clean CSV eco + ba supabase.csv"):
    """Loads the HSG course database from CSV. Returns a DataFrame or None if not found."""
    try:
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, path)
        if os.path.exists(full_path):
            df = pd.read_csv(full_path)
            df["skills_tags"] = df["skills_tags"].fillna("")
            return df
        return None
    except Exception as e:
        return None

def get_recommended_courses(job_name, gaps, max_courses=15):
    """
    Finds HSG courses that match the user's skill gaps.
    Builds a keyword set from the skill gaps, then scores each course by
    how many of its tags overlap with those keywords.
    Courses marked helpful by past users get a score boost via get_click_boost.
    Returns up to max_courses unique courses sorted by score.
    """
    df = load_courses()
    if df is None or not gaps:
        return []

    skills = SKILLS_FROM_EXCEL.get(job_name) or JOB_DETAILS.get(job_name, {}).get("skills", [])
    gap_keywords = set()
    for skill in skills:
        if skill["name"] in gaps:
            for kw in skill["keywords"]:
                kw = kw.lower().strip()
                if len(kw) > 3:
                    gap_keywords.add(kw)
            for word in skill["name"].lower().split():
                if len(word) > 4:
                    gap_keywords.add(word)

    # fallback: use words from gap names directly if no keywords were found
    if not gap_keywords:
        for gap in gaps:
            for word in gap.lower().split():
                if len(word) > 4:
                    gap_keywords.add(word)

    # language courses match generic keywords but are not career skill courses
    EXCLUDE_KEYWORDS = ["french", "german", "spanish", "italian", "chinese", "arabic", "japanese",
                        "english c1", "english c2", "english b", "language course", "beginner language",
                        "advanced language", "basic writing", "alphabet"]

    matched = []
    for _, row in df.iterrows():
        course_tags = [tag.strip().lower() for tag in str(row["skills_tags"]).split(",")]
        if not any(tag for tag in course_tags if tag):
            continue

        # Skip language courses
        if any(excl in course_tags for excl in EXCLUDE_KEYWORDS):
            continue
        score = sum(
            1 for kw in gap_keywords
            for tag in course_tags
            if tag and kw and (kw == tag or (len(kw) > 4 and kw in tag) or (len(tag) > 4 and tag in kw))
        )
        if score >= 5:
            matched.append({
                "title": row["title"],
                "code": row["course_code"],
                "program": row["program"],
                "credits": row["credits"],
                "language": row["language"],
                "semester": row["semester"],
                "url": row["course_url"],
                "score": score,
                "skill_gap": ", ".join(gaps),
            })
            
    for course in matched:
        boost = get_click_boost(course["skill_gap"], course["title"])
        course["score"] += boost * 2 

    matched.sort(key=lambda x: x["score"], reverse=True)
    seen = set()
    unique = []
    for c in matched:
        if c["title"] not in seen:
            seen.add(c["title"])
            unique.append(c)
    return unique[:max_courses]

JOB_DETAILS = {
    "Financial Analyst": {
        "description": """
Financial analysts conduct economic research and elicit valuable analyses on financial matters such as profitability, liquidity, solvency, and asset management. 
They provide recommendations on financial matters for decision-making processes. 
Financial analysts work in both the public and the private sector.
        """,
        "skills": [
            {"name": "Financial data analysis", "keywords": ["financial analysis", "financial data", "financial statement", "balance sheet", "income statement", "cash flow", "valuation", "dcf"]},
            {"name": "Economics & accounting knowledge", "keywords": ["economics", "accounting", "finance", "financial markets", "banking", "audit", "bookkeeping"]},
            {"name": "Quantitative & statistical skills", "keywords": ["statistics", "quantitative", "statistical analysis", "econometrics", "mathematical", "modeling"]},
            {"name": "Excel & analytical tools", "keywords": ["excel", "microsoft office", "bloomberg", "spreadsheet", "financial modeling"]},
            {"name": "Written & oral communication", "keywords": ["writing", "written", "report", "presentation", "published", "article", "editor"]},
            {"name": "Critical thinking & research", "keywords": ["critical thinking", "research", "market research", "investment research", "case study"]},
        ],
    },
    "Corporate Investment Banker": {
        "description": """
Corporate investment bankers offer strategic advice on financial services to companies 
and other institutions. They ensure that legal regulations are being followed by their 
clients in their efforts of raising any capital. They provide technical expertise and 
information on mergers and acquisitions, bonds and shares, privatisations and 
reorganisation, raising capital and security underwriting, including equity and debt markets.
        """,
        "skills": [
            {"name": "Financial modeling & valuation", "keywords": ["financial model", "valuation", "dcf", "financial modeling", "financial analysis"]},
            {"name": "Capital markets & investment knowledge", "keywords": ["capital markets", "equity", "investment banking", "debt financing", "securities", "ipo"]},
            {"name": "M&A & deal structuring", "keywords": ["m&a", "merger", "acquisition", "deal structuring", "transaction", "due diligence"]},
            {"name": "Client & business development", "keywords": ["client relationship", "business development", "stakeholder", "networking", "client management"]},
            {"name": "Presentation & communication", "keywords": ["pitch", "presentation", "presented", "powerpoint", "public speaking", "published", "writing"]},
            {"name": "Economics & accounting", "keywords": ["economics", "accounting", "finance", "excel", "bloomberg", "quantitative"]},
        ],
    },
    "Business Consultant": {
        "description": """
Management consultants analyse the position, structure and processes of businesses and 
companies and offer services or advice to improve them. They research and identify 
business processes such as financial inefficiencies or employee management and devise 
strategical plans to overcome these difficulties. They work in external consulting firms 
where they provide an objective view on a business and or company's structure and 
methodological processes.
        """,
        "skills": [
            {"name": "Critical thinking & problem solving", "keywords": ["critical thinking", "problem solving", "problem-solving", "case study", "case competition", "analytical"]},
            {"name": "Data analysis & systems thinking", "keywords": ["data analysis", "systems analysis", "excel", "python", "tableau", "power bi"]},
            {"name": "Oral & written communication", "keywords": ["writing", "written", "report", "article", "published", "edited", "editor", "presentation", "presented"]},
            {"name": "Project & time management", "keywords": ["project management", "coordinated", "coordination", "managed a team", "led a team", "time management"]},
            {"name": "Business & strategy knowledge", "keywords": ["strategy", "strategic", "consulting", "business strategy", "economics", "management"]},
            {"name": "Persuasion & negotiation", "keywords": ["negotiation", "persuasion", "stakeholder", "leadership", "president", "director", "represented"]},
        ],
    },
    "Marketing Manager": {
        "description": """
Marketing managers carry out the implementation of efforts related to the marketing 
operations in a company. They develop marketing strategies and plans by detailing cost 
and resources needed. They analyse the profitability of these plans, develop pricing 
strategies, and strive to raise awareness on products and companies among targeted customers.
        """,
        "skills": [
            {"name": "Marketing strategy & knowledge", "keywords": ["marketing", "branding", "brand strategy", "advertising", "marketing strategy", "campaign"]},
            {"name": "Digital marketing & analytics", "keywords": ["digital marketing", "seo", "google analytics", "social media", "online marketing", "analytics", "kpi"]},
            {"name": "Creative & content development", "keywords": ["content creation", "creative", "canva", "adobe", "photoshop", "design", "storytelling"]},
            {"name": "Written & oral communication", "keywords": ["writing", "written", "article", "published", "editor", "edited", "copywriting", "presentation", "presented"]},
            {"name": "Market research & consumer insights", "keywords": ["market research", "consumer research", "consumer insights", "survey", "research"]},
            {"name": "Budget & resource management", "keywords": ["budget", "budgeting", "expenses", "financial planning", "resource management", "coordinated"]},
        ],
    },
    "Data Analyst": {
        "description": """
Data analysts import, inspect, clean, transform, validate, model, or interpret 
collections of data with regard to the business goals of the company. They ensure that 
the data sources and repositories provide consistent and reliable data. Data analysts 
use different algorithms and IT tools as demanded by the situation and the current data. 
They might prepare reports in the form of visualisations such as graphs, charts, and dashboards.
        """,
        "skills": [
            {"name": "Programming & scripting", "keywords": ["python", "r programming", "r studio", "coding", "programming", "javascript", "sql"]},
            {"name": "Database querying (SQL)", "keywords": ["sql", "mysql", "postgresql", "database querying", "database"]},
            {"name": "Statistics & mathematical reasoning", "keywords": ["statistics", "statistical analysis", "probability", "econometrics", "quantitative", "mathematics", "mathematical"]},
            {"name": "Data visualization tools", "keywords": ["tableau", "power bi", "data visualization", "dashboard", "spss", "matlab"]},
            {"name": "Analytical & research thinking", "keywords": ["data analysis", "quantitative research", "market research", "financial analysis", "research"]},
            {"name": "Written communication & reporting", "keywords": ["report", "writing", "written", "article", "published", "documentation"]},
        ],
    },
    "ICT Application Developer": {
        "description": """
ICT application developers implement the ICT (software) applications based on the 
designs provided using application domain specific languages, tools, platforms and 
experience. They analyse user needs, design software solutions, write and test code, 
and maintain applications across web, mobile, and enterprise environments.
        """,
        "skills": [
            {"name": "Programming languages", "keywords": ["python", "java", "javascript", "c++", "swift", "coding", "programming", "software development"]},
            {"name": "Version control & collaboration", "keywords": ["git", "github", "gitlab", "version control", "bitbucket"]},
            {"name": "Database management", "keywords": ["sql", "mysql", "postgresql", "mongodb", "database"]},
            {"name": "Systems design & analysis", "keywords": ["systems analysis", "software engineering", "system design", "architecture", "web development", "app development"]},
            {"name": "Agile & project methodology", "keywords": ["agile", "scrum", "sprint", "kanban", "jira", "devops"]},
            {"name": "Problem solving & debugging", "keywords": ["algorithm", "data structures", "debugging", "testing", "critical thinking", "problem solving"]},
        ],
    },
    "Corporate Lawyer": {
        "description": """
Corporate lawyers provide legal consulting services and representation to corporations 
and organisations. They give advice on matters relating to taxes, legal rights and 
patents, international trade, trademarks, and legal financial issues arising from 
operating a business.
        """,
        "skills": [
            {"name": "Law & government knowledge", "keywords": ["law", "corporate law", "contract law", "business law", "commercial law", "legal", "legislation", "government"]},
            {"name": "Legal research & writing", "keywords": ["legal research", "legal writing", "moot court", "law review", "published", "writing", "written", "report"]},
            {"name": "Compliance & regulation", "keywords": ["compliance", "regulatory", "gdpr", "legal compliance", "regulation", "policy"]},
            {"name": "Negotiation & persuasion", "keywords": ["negotiation", "negotiated", "mediation", "dispute resolution", "persuasion"]},
            {"name": "Critical thinking & judgement", "keywords": ["critical thinking", "judgement", "analysis", "case study", "research", "problem solving"]},
            {"name": "Attention to detail & accuracy", "keywords": ["proofreading", "proofread", "edited", "editing", "detail-oriented", "accuracy"]},
        ],
    },
    "Tax Advisor": {
        "description": """
Tax advisors use their expertise in tax legislation to provide commercially-focused 
advisory and consultancy services to a wide range of clients from all economic sectors. 
They explain complicated tax-related legislation to their clients and assist them in 
ensuring the most efficient and beneficial payment of taxes by devising tax-efficient 
strategies. They also inform them of fiscal changes and developments and may specialise 
in tax strategies concerning mergers or multinational reconstruction for business clients, 
trust and estate taxes for individual clients.
        """,
        "skills": [
            {"name": "Tax & fiscal law knowledge", "keywords": ["tax law", "fiscal", "taxation", "vat", "tax planning", "tax", "law"]},
            {"name": "Economics & accounting basics", "keywords": ["accounting", "economics", "finance", "financial statement", "audit", "excel"]},
            {"name": "Legal research & writing", "keywords": ["legal research", "legal writing", "moot court", "published", "law review", "writing", "written"]},
            {"name": "Compliance & regulation", "keywords": ["compliance", "regulatory", "gdpr", "legal compliance", "regulation", "policy"]},
            {"name": "Critical thinking & analysis", "keywords": ["critical thinking", "analysis", "case study", "research", "quantitative", "problem solving"]},
            {"name": "Attention to detail", "keywords": ["proofreading", "proofread", "edited", "editing", "detail-oriented", "accuracy"]},
        ],
    },
    "Human Resources Manager": {
        "description": """
Human resources managers plan, design and implement processes related to the human 
capital of companies. They develop programs for recruiting, interviewing, and selecting 
employees based on a previous assessment of the profile and skills required in the 
company. Moreover, they manage compensation and development programs for the company's 
employees comprising trainings, skill assessment and yearly evaluations, promotion, 
expat programs, and general assurance of the well-being of the employees in the workplace.
        """,
        "skills": [
            {"name": "Recruitment & talent management", "keywords": ["recruitment", "recruiting", "hiring", "interviewing", "talent acquisition", "onboarding", "training"]},
            {"name": "Labor law & HR knowledge", "keywords": ["labor law", "employment law", "hr law", "human resources", "personnel", "compensation", "benefits"]},
            {"name": "Interpersonal & communication skills", "keywords": ["communication", "interpersonal", "mediation", "conflict resolution", "counselling", "coaching"]},
            {"name": "Event & people coordination", "keywords": ["coordinated", "event organisation", "event organization", "organised events", "organized events", "community"]},
            {"name": "Leadership & management", "keywords": ["led a team", "managed a team", "team leader", "captain", "president", "director", "head of", "represented", "member of", "leadership"]},
            {"name": "Psychology & organizational behavior", "keywords": ["psychology", "organizational behavior", "wellbeing", "motivation", "diversity", "inclusion"]},
        ],
    },
    "Strategic Planning Manager": {
        "description": """
Strategic planning managers create, together with a team of managers, the strategic plans of the company as a whole, and provide coordination in the implementation per 
department. They help to interpret the overall plan and create a detailed plan for each 
one of the departments and branches. They ensure consistency in the implementation.
        """,
        "skills": [
            {"name": "Operations & process management", "keywords": ["operations", "process management", "workflow", "front-desk operations", "daily operations", "efficiency"]},
            {"name": "Budget & resource management", "keywords": ["budget", "budgeting", "expenses", "cost management", "financial planning", "resource allocation"]},
            {"name": "Team leadership & coordination", "keywords": ["coordinated", "led a team", "managed a team", "team leader", "captain", "head of", "leadership", "represented"]},
            {"name": "Data analysis & reporting", "keywords": ["excel", "reporting", "dashboard", "kpi", "data analysis", "microsoft office"]},
            {"name": "Project & time management", "keywords": ["project management", "agile", "scrum", "time management", "planning", "scheduling"]},
            {"name": "Logistics & supply chain basics", "keywords": ["supply chain", "logistics", "procurement", "inventory management", "sourcing", "distribution"]},
        ],
    },
    "Product Manager": {
        "description": """
Product managers are responsible for managing the lifecycle of a product. They research 
and develop new products in addition to managing existing ones through market research 
and strategic planning. Product managers perform marketing and planning activities 
to increase profits.
        """,
        "skills": [
            {"name": "User research & UX", "keywords": ["user research", "ux", "figma", "user testing", "wireframe", "prototyping", "design"]},
            {"name": "Agile & project management", "keywords": ["agile", "scrum", "jira", "sprint", "product roadmap", "project management", "coordinated"]},
            {"name": "Data analysis & metrics", "keywords": ["data analysis", "excel", "python", "sql", "tableau", "kpi", "metrics", "reporting"]},
            {"name": "Written & oral communication", "keywords": ["writing", "written", "report", "article", "published", "edited", "editor", "presentation", "presented"]},
            {"name": "Innovation & creative thinking", "keywords": ["startup", "hackathon", "innovation", "side project", "founded", "creative", "initiative"]},
            {"name": "Technical literacy", "keywords": ["programming", "coding", "python", "software", "javascript", "engineering", "technology"]},
        ],
    },
    "Brand Manager": {
        "description": """
Brand managers analyse and plan the way a brand is positioned on the market. They 
develop brand strategies, oversee the execution of marketing campaigns, manage brand 
guidelines, and work to build a consistent and recognisable identity across all 
customer touchpoints.
        """,
        "skills": [
            {"name": "Marketing & brand strategy", "keywords": ["branding", "brand strategy", "brand management", "brand identity", "marketing", "advertising"]},
            {"name": "Creative & design tools", "keywords": ["canva", "adobe", "photoshop", "illustrator", "indesign", "figma", "design", "creative"]},
            {"name": "Social media & digital marketing", "keywords": ["social media", "instagram", "content creation", "community management", "digital marketing", "seo"]},
            {"name": "Writing & storytelling", "keywords": ["writing", "article", "published", "editor", "edited", "copywriting", "storytelling"]},
            {"name": "Consumer & market research", "keywords": ["market research", "consumer research", "consumer insights", "survey", "research", "analytics"]},
            {"name": "Campaign & event coordination", "keywords": ["campaign", "event organisation", "event organization", "organised events", "coordinated events", "coordinated"]},
        ],
    },
    "Supply Chain Manager": {
        "description": """
Supply chain managers plan, manage and coordinate all activities related to the 
sourcing and procurement of supplies needed to run manufacturing operations from the 
acquisition of raw materials to the distribution of finished products. The supplies 
can be raw materials or finished products, and it can be for internal or external use. 
Moreover, they plan and commission all the activities needed to be performed in 
manufacturing plants and adjust operations to changing levels of demand for a 
company's products.
        """,
        "skills": [
            {"name": "Supply chain & logistics knowledge", "keywords": ["supply chain", "logistics", "distribution", "warehouse management", "transportation", "procurement"]},
            {"name": "Procurement & negotiation", "keywords": ["procurement", "negotiation", "negotiated", "sourcing", "vendor management", "purchasing"]},
            {"name": "ERP & technology systems", "keywords": ["sap", "erp", "oracle", "microsoft dynamics", "inventory management system", "technology"]},
            {"name": "Data analysis & reporting", "keywords": ["excel", "data analysis", "reporting", "spreadsheet", "microsoft office", "kpi"]},
            {"name": "Operations & process management", "keywords": ["operations", "process management", "front-desk operations", "daily operations", "workflow", "efficiency"]},
            {"name": "Project & team coordination", "keywords": ["coordinated", "coordination", "project management", "led a team", "managed a team", "leadership"]},
        ],
    },
    "Entrepreneur": {
        "description": """
Social entrepreneurs create innovative products or service models to tackle social 
and environmental challenges, pursuing through their profits a social mission that 
benefits a wider community or the environment. They often use a more democratic 
decision-making system by involving closely their stakeholders, and strive to achieve 
change at a systems level, by influencing policies, market evolutions and even mentalities.
        """,
        "skills": [
            {"name": "Initiative & self-direction", "keywords": ["independently", "founded", "started", "launched", "built", "created", "side project", "freelance", "initiative"]},
            {"name": "Innovation & creative thinking", "keywords": ["startup", "hackathon", "innovation", "side project", "app", "founded", "new concept", "creative"]},
            {"name": "Leadership & team building", "keywords": ["led a team", "managed a team", "team leader", "captain", "president", "director", "head of", "represented", "member of", "organised events", "organized events", "editor", "leadership"]},
            {"name": "Communication & networking", "keywords": ["pitch", "pitching", "presentation", "presented", "public speaking", "networking", "writing", "published"]},
            {"name": "Financial & business literacy", "keywords": ["budget", "budgeting", "expenses", "financial planning", "accounting", "finance", "economics", "business"]},
            {"name": "Resilience & adaptability", "keywords": ["adaptability", "adaptable", "new environments", "challenges", "gap year", "travelled", "traveled", "independently"]},
        ],
    },
}

CAREER_TWINS = {
    "Financial Analyst":            {"name": "Warren Buffett",    "image": "images/warren_buffett.jpg"},
    "Corporate Investment Banker":  {"name": "Michael Milken",    "image": "images/michael_milken.jpg"},
    "Business Consultant":          {"name": "Peter Drucker",     "image": "images/peter_drucker.jpg"},
    "Marketing Manager":            {"name": "David Ogilvy",      "image": "images/david_ogilvy.jpg"},
    "Data Analyst":                 {"name": "Nate Silver",       "image": "images/nate_silver.jpg"},
    "ICT Application Developer":    {"name": "Steve Wozniak",     "image": "images/steve_wozniak.jpg"},
    "Corporate Lawyer":             {"name": "Joseph Flom",       "image": "images/joseph_flom.jpg"},
    "Tax Advisor":                  {"name": "Arthur Laffer",     "image": "images/arthur_laffer.jpg"},
    "Human Resources Manager":      {"name": "Laszlo Bock",       "image": "images/laszlo_bock.jpg"},
    "Strategic Planning Manager":   {"name": "Michael Porter",    "image": "images/michael_porter.jpg"},
    "Product Manager":              {"name": "Steve Jobs",        "image": "images/steve_jobs.jpg"},
    "Brand Manager":                {"name": "Morgan Flatley",    "image": "images/morgan_flatley.jpg"},
    "Supply Chain Manager":         {"name": "Tim Cook",          "image": "images/tim_cook.jpg"},
    "Entrepreneur":                 {"name": "Elon Musk",         "image": "images/elon_musk.jpg"},
}
# dialogs must be defined at module level to work as overlays in Streamlit
@st.dialog("Recommended HSG Courses | Empfohlene HSG-Kurse", width="large")
def show_courses_dialog(courses):
    """Renders the course recommendations popup. Shows a card per course with a helpful button."""
    if not courses:
        st.info(t("no_courses_found"))
        return
    st.markdown(t("courses_dialog_intro"))
    st.markdown("<br>", unsafe_allow_html=True)
    for course in courses:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            <div style='background:#f9f9f9; border:1px solid #c8e6c9; border-radius:12px; padding:16px 20px; margin-bottom:8px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='flex:1;'>
                        <div style='font-weight:600; color:#0d542b; font-size:1rem;'>{course['title']}</div>
                        <div style='color:#666; font-size:0.83rem; margin-top:4px;'>{course['program']} &nbsp;·&nbsp; {course['credits']} ECTS &nbsp;·&nbsp; {course['language']} &nbsp;·&nbsp; {course['semester']}</div>
                    </div>
                    <a href='{course['url']}' target='_blank' style='background:#0d542b; color:white; padding:7px 16px; border-radius:8px; font-size:0.83rem; text-decoration:none; white-space:nowrap; margin-left:16px; font-weight:600;'>{t("view_course_button")}</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("<div style='margin-top:18px;'>", unsafe_allow_html=True)
            if st.button((t("helpful_button")), key=f"helpful_{course['title']}_{course['skill_gap']}"):
                record_helpful_click(course["skill_gap"], course["title"])
                st.success(t("helpful_thanks"))
            st.markdown("</div>", unsafe_allow_html=True)
    
@st.dialog("Career Twin | Karriere-Zwilling")
def show_twin_dialog(twin, job_name):
    """Renders the career twin popup with photo, name, and fun fact."""
    img_src = ""
    try:
        with open(twin["image"], "rb") as img_file:
            ext = twin["image"].split(".")[-1].replace("jpg", "jpeg")
            img_b64 = base64.b64encode(img_file.read()).decode()
            img_src = f"data:image/{ext};base64,{img_b64}"
    except Exception:
        img_src = ""

    img_tag = f"<img src='{img_src}' style='width:80px; height:80px; border-radius:50%; object-fit:cover; flex-shrink:0;'/>" if img_src else ""
    name = twin['name']
    fact = t_twin_fact(job_name)
    st.markdown(f"""
    <div style='
        background:#f0faf4;
        border: 2px solid #0d542b;
        border-radius:16px;
        padding:20px;
        display:flex;
        align-items:center;
        gap:20px;
    '>
        {img_tag}
        <div>
            <div style='color:#0d542b; font-weight:700; font-size:1.1rem; margin-bottom:8px;'>{name}</div>
            <div style='color:#333; font-size:0.88rem; line-height:1.6;'>{fact}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_skill_gaps(cv_text, job_name, min_keywords=2):
    """
    Splits a job's skills into two lists: skills the user has and skills they're missing.
    A skill counts as present if at least min_keywords of its keywords appear in the CV.
    """
    skills = SKILLS_FROM_EXCEL.get(job_name) or JOB_DETAILS.get(job_name, {}).get("skills", [])
    cv_lower = cv_text.lower() if cv_text else ""
    has = []
    gaps = []
    for skill in skills:
        matches = sum(1 for kw in skill["keywords"] if kw.lower() in cv_lower)
        if matches >= min_keywords:
            has.append(skill["name"])
        else:
            gaps.append(skill["name"])
    return has, gaps

def show_job_page(job_name):
    """
    Main render function for a job detail page. Called by Details.py/2/3.
    Sections: job description + match chart, salary, skill profile, courses, career twin, feedback.
    """
    st.set_page_config(page_title=f"{job_name} | Careerly", page_icon="🧩", layout="wide")
    language_toggle()

    st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #0d542b !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0a3d1f !important;
        color: white !important;
    }
    .gap-item {
        background: #fff3f3;
        border-left: 4px solid #c0392b;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 8px;
        color: #c0392b;
        font-size: 0.95rem;
    }
    .has-item {
        background: #f0faf4;
        border-left: 4px solid #0d542b;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 8px;
        color: #0d542b;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)
    st.markdown("""
<style>
/* hide sidebar and its toggle button */
[data-testid="stSidebar"] {
    display: none;
}
[data-testid="collapsedControl"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)
    
    if st.button(t("back_to_results"), type="primary"):
        st.switch_page("pages/Results.py")

    job = JOB_DETAILS.get(job_name, {})
    profile = st.session_state.get("profile", {})
    cv_text = profile.get("cv_text", "")

    # Section 1 & 2: Job title + description (left) and career match overview chart (right).
    # Both start at the same vertical position so the chart aligns with the job title.
    col_desc, col_chart = st.columns([1, 1])

    with col_desc:
        st.markdown(f"<h2 style='color:#0d542b;'>{job_name}</h2>", unsafe_allow_html=True)
        st.markdown(t("job_description_title"))
        st.write(t_job_detail(job_name))

    # Section 2: Horizontal bar chart of all 14 jobs sitting next to the description.
    # The currently viewed job is highlighted in dark green; all others use a
    # translucent fill so the user can instantly see where this role ranks.
    combined_scores = profile.get("combined_scores", {})
    with col_chart:
        if combined_scores:
            # Sort descending and take only the top 10 so the chart stays readable
            sorted_jobs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:10]
            jobs_list   = [j for j, _ in sorted_jobs]
            scores_list = [s for _, s in sorted_jobs]

            # Dark green for the selected job, light transparent green for everything else
            colors = [
                "#0d542b" if job == job_name else "rgba(13, 84, 43, 0.18)"
                for job in jobs_list
            ]
            # Match the text color to the bar so it stays readable on both fills
            text_colors = [
                "white" if job == job_name else "#0d542b"
                for job in jobs_list
            ]

            fig = go.Figure(go.Bar(
                x=scores_list,
                y=jobs_list,
                orientation="h",
                marker_color=colors,
                text=[f"{s}%" for s in scores_list],
                textposition="inside",
                insidetextanchor="end",
                textfont=dict(color=text_colors, size=13),
                hovertemplate="%{y}: %{x}%<extra></extra>",
            ))
            fig.update_layout(
                # Leave a little headroom to the right so labels don't clip
                xaxis=dict(range=[0, 108], showgrid=False, zeroline=False, showticklabels=False),
                # reversed so rank #1 appears at the top (sorted_jobs[0] = highest)
                yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
                margin=dict(l=10, r=10, t=10, b=10),
                height=340,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, key="match_overview_chart")

    # Section 3: Salary in Switzerland
    st.markdown(f"### {t('salary_title')}")
    with st.spinner("Fetching salary data..."):
        salary = get_swiss_salary(job_name)
    if salary:
        min_s = salary['min']
        max_s = salary['max']
        avg_s = salary['avg']
        # Calculate position of average on the range bar (0-100%)
        range_span = max_s - min_s if max_s != min_s else 1
        avg_pct = round((avg_s - min_s) / range_span * 100)
        avg_pct = max(5, min(95, avg_pct))  # keep within visible range

        st.markdown(f"""
        <div style='padding: 8px 0 16px 0;'>
            <!-- Min and Max labels -->
            <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                <div>
                    <div style='color:#666; font-size:0.78rem;'>{t("salary_min")}</div>
                    <div style='color:#333; font-weight:600; font-size:1rem;'>CHF {min_s:,}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='color:#666; font-size:0.78rem;'>{t("salary_max")}</div>
                    <div style='color:#333; font-weight:600; font-size:1rem;'>CHF {max_s:,}</div>
                </div>
            </div>
            <!-- Range bar -->
            <div style='position:relative; height:10px; background:#e8f5e9; border-radius:999px;'>
                <div style='position:absolute; left:0; right:0; height:100%; background:linear-gradient(90deg, #c8e6c9, #0d542b); border-radius:999px;'></div>
                <!-- Average dot -->
                <div style='position:absolute; left:{avg_pct}%; transform:translateX(-50%); top:-4px; width:18px; height:18px; background:#0d542b; border-radius:50%; border:3px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.2);'></div>
            </div>
            <!-- Average label below the bar, aligned to dot position -->
            <div style='position:relative; height:36px; margin-top:6px;'>
                <div style='position:absolute; left:{avg_pct}%; transform:translateX(-50%); text-align:center; white-space:nowrap;'>
                    <div style='color:#666; font-size:0.78rem;'>{t("salary_avg")}</div>
                    <div style='color:#333; font-weight:600; font-size:1rem;'>CHF {avg_s:,}</div>
                </div>
            </div>
            <div style='color:#999; font-size:0.78rem; margin-top:4px;'>
                {t("salary_source")}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.info(t("salary_unavailable"))

    # Section 4: Skill Profile
    has, gaps = get_skill_gaps(cv_text, job_name)
    st.markdown(f" {t('skill_profile_title')}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(t("skills_you_have"))
        if has:
            for skill in has:
                st.markdown(f"<div class='has-item'>{t_skill(skill)}</div>", unsafe_allow_html=True)
        elif not cv_text:
            st.markdown(f"<div class='has-item'>{t('upload_cv_prompt')}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='has-item'>{t('no_skills_detected')}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(t("skills_gaps"))
        if gaps:
            for skill in gaps:
                st.markdown(f"<div class='gap-item'>{t_skill(skill)}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='has-item'>{t('all_skills_present')}</div>", unsafe_allow_html=True)

    # Section 4b: Recommended HSG Courses
    if gaps:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### {t('courses_section_title')}")
        st.write(t("skill_gap_intro"))
        recommended = get_recommended_courses(job_name, gaps)
        col_btn, _ = st.columns([2, 1])
        with col_btn:
            if st.button((t("courses_button")), type="primary", use_container_width=True):
                show_courses_dialog(recommended)

    # Section 5: Career Twin button
    twin = CAREER_TWINS.get(job_name)
    if twin:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### {t('career_twin_title')}")
        st.write(t("career_twin_intro"))
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button((t("meet_twin_button")), type="primary", use_container_width=True):
                show_twin_dialog(twin, job_name)

    # Section 6: Match feedback
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"### {t('match_feedback_title')}")
    st.write(t("match_feedback_body"))
    col_yes, col_no, _ = st.columns([1, 1, 3])
    with col_yes:
        if st.button(t("match_feedback_yes"), use_container_width=True, key="match_yes"):
            cv_text = st.session_state.get("profile", {}).get("cv_text", "")
            record_cv_match(job_name, cv_text)
            st.success(t("match_feedback_yes_thanks"))
    with col_no:
        if st.button(t("match_feedback_no"), use_container_width=True, key="match_no"):
            st.info(t("match_feedback_no_thanks"))
