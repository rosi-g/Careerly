import streamlit as st
import base64
import pandas as pd
import os

def load_skills_from_excel(path="skills_database.xlsx"):
    """Load skill keywords from Excel database.
    Job name only appears in first row of each block — forward fill to fix empty cells.
    Handles both old and new ESCO column naming.
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

JOB_DETAILS = {
    "Financial Analyst": {
        "description": """
A Financial Analyst evaluates financial data to help businesses and individuals make investment decisions. 
They build financial models, analyze market trends, prepare reports, and support budgeting and forecasting processes. 
Financial Analysts work in banks, consulting firms, corporations, and investment funds.
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
    "Investment Banker": {
        "description": """
Investment Bankers help companies raise capital, execute mergers and acquisitions, and advise on complex financial transactions. 
The work is fast-paced, analytical, and highly competitive. 
You'll spend time building financial models, preparing pitch books, and presenting to clients.
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
    "Management Consultant": {
        "description": """
Management Consultants help organizations solve complex business problems and improve performance. 
They work across industries, analyzing data, developing strategies, and presenting recommendations to senior executives. 
Strong problem-solving, communication, and presentation skills are essential.
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
Marketing Managers develop and execute strategies to promote products or services, grow brand awareness, and acquire customers. 
They work with creative teams, manage budgets, analyze campaign performance, and stay on top of digital trends.
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
Data Analysts collect, clean, and interpret large datasets to help businesses make better decisions. 
They use tools like Python, SQL, and Tableau to find patterns and build dashboards. 
Strong statistical thinking and curiosity are key.
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
    "Software Engineer": {
        "description": """
Software Engineers design, build, and maintain software systems and applications. 
They work in teams using agile methodologies, write clean code, and solve technical problems. 
A strong foundation in programming and logical thinking is essential.
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
Corporate Lawyers advise businesses on legal matters including contracts, mergers, compliance, and regulatory issues. 
They need strong analytical and writing skills, deep legal knowledge, and the ability to explain complex issues clearly.
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
    "Tax Lawyer": {
        "description": """
Tax Lawyers specialize in tax planning, compliance, and disputes for individuals and businesses. 
They need deep knowledge of tax codes, strong analytical skills, and the ability to advise on complex financial structures.
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
    "HR Manager": {
        "description": """
HR Managers attract, develop, and retain talent while building a positive company culture. 
They handle recruitment, onboarding, performance management, and employee wellbeing. 
Strong interpersonal and organizational skills are key.
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
    "Operations Manager": {
        "description": """
Operations Managers oversee the day-to-day running of a business, ensuring processes are efficient and goals are met. 
They coordinate teams, manage budgets, and continuously look for ways to improve how things work.
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
Product Managers define what gets built and why. They work at the intersection of business, technology, and design — 
gathering user insights, writing product specs, and working with engineers and designers to ship great products.
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
    "Strategy Consultant": {
        "description": """
Strategy Consultants help companies define their long-term direction and competitive positioning. 
They analyze markets, benchmark competitors, and build strategic roadmaps. 
Strong analytical thinking and executive communication are essential.
        """,
        "skills": [
            {"name": "Strategic thinking & frameworks", "keywords": ["strategy", "strategic planning", "swot", "porter", "bcg matrix", "case competition", "consulting"]},
            {"name": "Market & competitive analysis", "keywords": ["market analysis", "competitive analysis", "benchmarking", "market research", "economics"]},
            {"name": "Oral & written communication", "keywords": ["powerpoint", "presentation", "presented", "pitch", "public speaking", "writing", "written", "published", "editor"]},
            {"name": "Data analysis & systems thinking", "keywords": ["data analysis", "excel", "python", "tableau", "systems analysis", "power bi"]},
            {"name": "Persuasion & leadership", "keywords": ["led a team", "managed a team", "captain", "president", "director", "head of", "founded", "represented", "member of", "leadership", "independently"]},
            {"name": "Project & time management", "keywords": ["project management", "coordinated", "coordination", "time management", "organised events", "organized events"]},
        ],
    },
    "Brand Manager": {
        "description": """
Brand Managers build and protect a company's brand identity. 
They develop creative campaigns, manage agencies, track brand health, and ensure consistent messaging across all channels.
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
Supply Chain Managers oversee the flow of goods from suppliers to customers. 
They handle procurement, logistics, inventory, and vendor relationships — always looking to reduce costs and improve efficiency.
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
Entrepreneurs identify opportunities, take risks, and build something from scratch. 
It requires creativity, resilience, and a wide range of skills from finance to marketing to leadership. 
There's no single path — but curiosity and initiative are the starting point.
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
    "Financial Analyst": {
        "name": "Warren Buffett",
        "image": "images/warren_buffett.jpg",
        "fun_fact": "Warren started analysing stocks at age 11 and filed his first tax return at 13. He turned a love of numbers into a $100+ billion fortune. Not bad for someone who just really liked reading financial reports.",
    },
    "Investment Banker": {
        "name": "Jamie Dimon",
        "image": "images/jamie_dimon.jpg",
        "fun_fact": "Jamie Dimon went from Harvard Business School straight into banking and never looked back. He's now the CEO of JPMorgan Chase, the largest bank in the US. He once said 'banking is very good work if you can get it.'",
    },
    "Management Consultant": {
        "name": "Sheryl Sandberg",
        "image": "images/sheryl_sandberg.jpg",
        "fun_fact": "Before becoming COO of Facebook, Sheryl worked at McKinsey as a management consultant. She used those problem-solving skills to help scale one of the biggest companies in the world.",
    },
    "Marketing Manager": {
        "name": "Gary Vaynerchuk",
        "image": "images/gary_vaynerchuk.jpg",
        "fun_fact": "Gary V turned his family wine business into a $60M empire just by doing marketing online before anyone else did. He basically invented social media marketing — and never stops talking about it.",
    },
    "Data Analyst": {
        "name": "DJ Patil",
        "image": "images/dj_patil.jpg",
        "fun_fact": "DJ Patil was the first ever Chief Data Scientist of the United States under Obama. He literally helped coin the job title 'Data Scientist' — so if you become one, you can thank him.",
    },
    "Software Engineer": {
        "name": "Bill Gates",
        "image": "images/bill_gates.jpg",
        "fun_fact": "Bill Gates wrote his first software program at age 13. He dropped out of Harvard to start Microsoft — which turned out okay. He's now one of the richest people in history and spends his time saving the world.",
    },
    "Corporate Lawyer": {
        "name": "Michelle Obama",
        "image": "images/michelle_obama.jpg",
        "fun_fact": "Before becoming First Lady, Michelle Obama was a corporate lawyer at Sidley Austin in Chicago. That's also where she met Barack — she was assigned as his mentor. Best networking story ever.",
    },
    "Tax Lawyer": {
        "name": "Judge Judy",
        "image": "images/judge_judy.jpg",
        "fun_fact": "Before Judge Judy became a TV icon, she worked her way up through the legal system as a family court judge. She now earns $47 million a year. Law clearly pays off.",
    },
    "HR Manager": {
        "name": "Arianna Huffington",
        "image": "images/arianna_huffington.jpg",
        "fun_fact": "Arianna Huffington built her empire around people and culture. She founded Thrive Global to revolutionise workplace wellbeing — basically telling the world to sleep more and stress less. As an HR career, that's pretty iconic.",
    },
    "Operations Manager": {
        "name": "Tim Cook",
        "image": "images/tim_cook.jpg",
        "fun_fact": "Tim Cook joined Apple not as a tech genius but as an operations expert. He rebuilt Apple's supply chain into the most efficient in the world. Steve Jobs once said hiring Tim was his best ever decision.",
    },
    "Product Manager": {
        "name": "Steve Jobs",
        "image": "images/steve_jobs.jpg",
        "fun_fact": "Steve Jobs was the ultimate product manager — he obsessed over every detail down to the screws inside the Mac. He once delayed a product launch because he didn't like the shade of beige. Perfectionism at its finest.",
    },
    "Strategy Consultant": {
        "name": "Marvin Bower",
        "image": "images/marvin_bower.jpg",
        "fun_fact": "Marvin Bower invented modern strategy consulting when he built McKinsey into the powerhouse it is today. He believed consultants should always tell clients the truth — even when they really don't want to hear it.",
    },
    "Brand Manager": {
        "name": "Virgil Abloh",
        "image": "images/virgil_abloh.jpg",
        "fun_fact": "Virgil Abloh studied architecture but became one of the most iconic brand builders of his generation. He founded Off-White and became Louis Vuitton's artistic director — proving that brand vision matters more than the 'right' degree.",
    },
    "Supply Chain Manager": {
        "name": "Elon Musk",
        "image": "images/elon_musk.jpg",
        "fun_fact": "Elon Musk built Tesla and SpaceX by obsessing over supply chains and manufacturing. He once slept on the factory floor to fix production problems. Say what you want about him — the man knows how to ship a product.",
    },
    "Entrepreneur": {
        "name": "Sara Blakely",
        "image": "images/sara_blakely.jpg",
        "fun_fact": "Sara Blakely started Spanx with $5,000 in savings, no business degree, and no investors. She wrote her own patent, cold-called manufacturers, and built a billion-dollar company from scratch. She became the world's youngest self-made female billionaire.",
    },
}

# -------------------------------------------------------
# st.dialog defined at MODULE LEVEL so it works as overlay
# -------------------------------------------------------
@st.dialog("Your Career Twin")
def show_twin_dialog(twin):
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
    fact = twin['fun_fact']
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

# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def get_skill_gaps(cv_text, job_name, min_keywords=2):
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

# -------------------------------------------------------
# MAIN PAGE FUNCTION
# -------------------------------------------------------
def show_job_page(job_name):
    st.set_page_config(page_title=f"{job_name} | Careerly", page_icon="🧩", layout="wide")

    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #0d542b !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
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
    .section-box {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)

    if st.button("Back to results"):
        st.switch_page("pages/page2.py")

    st.markdown(f"<h2 style='color:#0d542b;'>{job_name}</h2>", unsafe_allow_html=True)

    job = JOB_DETAILS.get(job_name, {})
    profile = st.session_state.get("profile", {})
    cv_text = profile.get("cv_text", "")

    # Section 1: Job Description
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### What does this career look like?")
    st.write(job.get("description", "").strip())
    st.markdown("</div>", unsafe_allow_html=True)

    # Section 2: Skill Profile
    has, gaps = get_skill_gaps(cv_text, job_name)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### Your Skill Profile")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**What you already have:**")
        if has:
            for skill in has:
                st.markdown(f"<div class='has-item'>{skill}</div>", unsafe_allow_html=True)
        elif not cv_text:
            st.markdown("<div class='has-item'>Upload your CV to see what you already have!</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='has-item'>None detected yet — try adding more detail to your CV!</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("**Your skill gaps:**")
        if gaps:
            for skill in gaps:
                st.markdown(f"<div class='gap-item'>{skill}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='has-item'>You already have all the key skills!</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Section 3: Recommended Courses (placeholder)
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("### Recommended HSG Courses")
    st.info("Course recommendations coming soon! Your team is currently building the HSG course database.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Section 4: Career Twin button
    twin = CAREER_TWINS.get(job_name)
    if twin:
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("Meet your Career Twin", type="primary", use_container_width=True):
                show_twin_dialog(twin)
