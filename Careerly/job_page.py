"""
job_page.py - detail page shown when a user selects one of their top career matches.

What happens here:
- Job title and description are shown alongside a bar chart of all career match scores
- Salary data is fetched from the Adzuna API and displayed as a range bar
- Skill gaps are calculated by comparing the CV against ESCO skill keywords
- Recommended HSG courses are matched to those skill gaps
- Career twin popup shows a well-known professional in that field
- User can confirm or reject the match, which feeds back into the model

SKILLS_FROM_EXCEL is imported by careerly.py and ml_model.py to run the scoring.
Descriptions come from translations.xlsx via t_job_detail().
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
try:
    ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID") or os.getenv("ADZUNA_APP_ID")
    ADZUNA_APP_KEY = st.secrets.get("ADZUNA_APP_KEY") or os.getenv("ADZUNA_APP_KEY")
except Exception:
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

@st.cache_data(show_spinner=False)
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
            df = pd.read_csv(full_path, encoding='utf-8-sig')
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

    skills = SKILLS_FROM_EXCEL.get(job_name, [])
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
    """Renders the career twin popup with light green bubble design."""
    name = twin['name']
    fact = t_twin_fact(job_name)

    # Load image as base64
    img_src = ""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_dir, twin["image"])
        with open(img_path, "rb") as img_file:
            ext = twin["image"].split(".")[-1].replace("jpg", "jpeg")
            img_b64 = base64.b64encode(img_file.read()).decode()
            img_src = f"data:image/{ext};base64,{img_b64}"
    except Exception:
        pass

    img_tag = f"<img src='{img_src}' style='width:80px; height:80px; border-radius:50%; object-fit:cover; flex-shrink:0;'/>" if img_src else ""

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
    skills = SKILLS_FROM_EXCEL.get(job_name, [])
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

    profile = st.session_state.get("profile", {})
    cv_text = profile.get("cv_text", "")

    # Section 1 & 2: Job title + description (left) and career match overview chart (right).
    # Both start at the same vertical position so the chart aligns with the job title.
    st.markdown(f"<h2 style='color:#0d542b;'>{job_name}</h2>", unsafe_allow_html=True)
    st.markdown(t("job_description_title"))
    st.write(t_job_detail(job_name))

    # Section 2: Why this career matches your interests
    interests = profile.get("interests", [])
    if interests:
        from shared_data import INTEREST_SPREAD

        # Get raw scores — these already sum to ~100 per job
        # so we use them directly as percentages
        # Translate interest names for display
        from translations import get_interests_display
        interests_display = get_interests_display(interests)

        interest_data = []
        for interest, interest_label in zip(interests, interests_display):
            spread = INTEREST_SPREAD.get(interest, {})
            raw = spread.get(job_name, 0)
            interest_data.append((interest_label, raw))

        interest_data.sort(key=lambda x: x[1], reverse=True)

        pills = []
        for interest, raw in interest_data:
            if raw >= 7:
                bg, color, border = "#0d542b", "white", "#0d542b"
            elif raw > 0:
                bg, color, border = "#d4edda", "#0d542b", "#0d542b"
            else:
                bg, color, border = "#f5f5f5", "#999", "#ddd"
            pills.append(
                f"<span style='background:{bg}; color:{color}; border:1.5px solid {border}; "
                f"border-radius:999px; padding:6px 16px; font-size:0.85rem; font-weight:600; "
                f"display:inline-block; margin:4px;'>{interest}</span>"
            )

        legend = (
            "<div style='margin-top:12px; font-size:0.8rem; color:#666; display:flex; gap:16px; flex-wrap:wrap;'>"
            "<span><span style='display:inline-block; width:10px; height:10px; background:#0d542b; border-radius:50%; margin-right:4px;'></span>" + t("interest_strong") + "</span>"
            "<span><span style='display:inline-block; width:10px; height:10px; background:#d4edda; border:1px solid #0d542b; border-radius:50%; margin-right:4px;'></span>" + t("interest_moderate") + "</span>"
            "<span><span style='display:inline-block; width:10px; height:10px; background:#f5f5f5; border:1px solid #ddd; border-radius:50%; margin-right:4px;'></span>" + t("interest_not_relevant") + "</span>"
            "</div>"
        )

        st.markdown(f"### {t('interest_match_title')}")
        st.markdown(
            "<div style='display:flex; flex-wrap:wrap; gap:4px;'>" + "".join(pills) + "</div>",
            unsafe_allow_html=True
        )
        st.markdown(legend, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

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
