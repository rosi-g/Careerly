import streamlit as st
import PyPDF2
import nltk
import sys
import os
nltk.download('stopwords', quiet=True)

# Import from job_page.py so keywords are always in sync
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from job_page import JOB_DETAILS, SKILLS_FROM_EXCEL

JOBS = list(JOB_DETAILS.keys())

INTERESTS = [
    "Numbers", "Creativity", "People", "Languages", "Writing",
    "Technology", "Detail & Precision", "Leadership", "Problem Solving",
    "Research", "Law & Justice", "International", "Entrepreneurship",
    "Strategy", "Sustainability", "Communication", "Mathematics",
    "Culture", "Organisation", "Innovation", "Data", "Finance",
    "Design", "Negotiation",
]

INTEREST_SPREAD = {
    "Numbers": {
        "Financial Analyst": 100, "Investment Banker": 90,
        "Data Analyst": 80, "Tax Lawyer": 60,
        "Management Consultant": 40, "Strategy Consultant": 40,
    },
    "Creativity": {
        "Marketing Manager": 100, "Brand Manager": 100,
        "Product Manager": 70, "Entrepreneur": 60,
        "Software Engineer": 30,
    },
    "People": {
        "HR Manager": 100, "Management Consultant": 70,
        "Marketing Manager": 60, "Operations Manager": 50,
        "Entrepreneur": 50, "Brand Manager": 40,
    },
    "Languages": {
        "Corporate Lawyer": 70, "HR Manager": 60,
        "Marketing Manager": 60, "Management Consultant": 50,
        "Strategy Consultant": 50, "Brand Manager": 40,
    },
    "Writing": {
        "Marketing Manager": 100, "Brand Manager": 90,
        "Management Consultant": 60, "Strategy Consultant": 60,
        "Corporate Lawyer": 50, "HR Manager": 40,
    },
    "Technology": {
        "Software Engineer": 100, "Data Analyst": 90,
        "Product Manager": 80, "Operations Manager": 40,
        "Management Consultant": 30,
    },
    "Detail & Precision": {
        "Tax Lawyer": 100, "Corporate Lawyer": 90,
        "Financial Analyst": 90, "Data Analyst": 70,
        "Supply Chain Manager": 60, "Operations Manager": 50,
    },
    "Leadership": {
        "Management Consultant": 100, "Strategy Consultant": 90,
        "Operations Manager": 80, "HR Manager": 70,
        "Entrepreneur": 70, "Product Manager": 60,
    },
    "Problem Solving": {
        "Management Consultant": 100, "Strategy Consultant": 90,
        "Software Engineer": 80, "Data Analyst": 70,
        "Financial Analyst": 60, "Entrepreneur": 60,
    },
    "Research": {
        "Data Analyst": 100, "Management Consultant": 80,
        "Strategy Consultant": 80, "Corporate Lawyer": 70,
        "Financial Analyst": 60, "Marketing Manager": 50,
    },
    "Law & Justice": {
        "Corporate Lawyer": 100, "Tax Lawyer": 100,
        "Management Consultant": 40, "HR Manager": 30,
        "Financial Analyst": 20,
    },
    "International": {
        "Management Consultant": 80, "Strategy Consultant": 80,
        "Corporate Lawyer": 70, "Investment Banker": 70,
        "Marketing Manager": 60, "HR Manager": 50,
    },
    "Entrepreneurship": {
        "Entrepreneur": 100, "Product Manager": 80,
        "Marketing Manager": 60, "Strategy Consultant": 50,
        "Management Consultant": 40, "Software Engineer": 40,
    },
    "Strategy": {
        "Strategy Consultant": 100, "Management Consultant": 90,
        "Investment Banker": 60, "Financial Analyst": 50,
        "Operations Manager": 50, "Product Manager": 50,
    },
    "Sustainability": {
        "Operations Manager": 70, "Supply Chain Manager": 70,
        "Management Consultant": 60, "Strategy Consultant": 60,
        "HR Manager": 50, "Entrepreneur": 50,
    },
    "Communication": {
        "Marketing Manager": 100, "HR Manager": 90,
        "Management Consultant": 80, "Brand Manager": 80,
        "Strategy Consultant": 70, "Corporate Lawyer": 60,
    },
    "Mathematics": {
        "Financial Analyst": 100, "Data Analyst": 100,
        "Investment Banker": 80, "Software Engineer": 70,
        "Tax Lawyer": 60, "Management Consultant": 40,
    },
    "Culture": {
        "HR Manager": 90, "Marketing Manager": 80,
        "Brand Manager": 80, "Management Consultant": 60,
        "Strategy Consultant": 50, "Corporate Lawyer": 40,
    },
    "Organisation": {
        "Operations Manager": 100, "Supply Chain Manager": 90,
        "HR Manager": 70, "Management Consultant": 60,
        "Project Manager": 60, "Financial Analyst": 40,
    },
    "Innovation": {
        "Entrepreneur": 100, "Product Manager": 90,
        "Software Engineer": 70, "Marketing Manager": 60,
        "Strategy Consultant": 50, "Management Consultant": 40,
    },
    "Data": {
        "Data Analyst": 100, "Software Engineer": 80,
        "Financial Analyst": 70, "Management Consultant": 60,
        "Strategy Consultant": 60, "Operations Manager": 50,
    },
    "Finance": {
        "Financial Analyst": 100, "Investment Banker": 100,
        "Tax Lawyer": 70, "Management Consultant": 50,
        "Strategy Consultant": 50, "Entrepreneur": 40,
    },
    "Design": {
        "Brand Manager": 100, "Marketing Manager": 90,
        "Product Manager": 80, "Software Engineer": 50,
        "Entrepreneur": 40,
    },
    "Negotiation": {
        "Corporate Lawyer": 100, "Tax Lawyer": 90,
        "Investment Banker": 80, "Supply Chain Manager": 70,
        "Management Consultant": 60, "Entrepreneur": 50,
    },
}

# -------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def calculate_cv_scores(cv_text, min_keywords=2):
    scores = {}
    cv_lower = cv_text.lower()
    for job in JOBS:
        skills = SKILLS_FROM_EXCEL.get(job) or JOB_DETAILS.get(job, {}).get("skills", [])
        total = len(skills)
        matched = sum(
            1 for skill in skills
            if sum(1 for kw in skill["keywords"] if kw.lower() in cv_lower) >= min_keywords
        )
        scores[job] = round((matched / max(total, 1)) * 100)
    return scores

def calculate_interest_scores(interests):
    scores = {job: 0 for job in JOBS}
    if not interests:
        return scores
    for interest in interests:
        spread = INTEREST_SPREAD.get(interest, {})
        for job, points in spread.items():
            if job in scores:
                scores[job] = min(scores[job] + points, 100)
    max_score = max(scores.values()) if max(scores.values()) > 0 else 1
    scores = {j: round((s / max_score) * 100) for j, s in scores.items()}
    return scores

# -------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------
st.set_page_config(page_title="Careerly", page_icon="🧩", layout="wide")

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
/* Selected pill — green */
div[data-testid="stPills"] button[aria-selected="true"],
div[data-testid="stPills"] button[aria-pressed="true"],
div[data-testid="stPills"] span[data-selected="true"],
.stPills button[kind="pillsActive"],
button[data-testid="stPillsButton"][aria-pressed="true"] {
    background-color: #0d542b !important;
    color: white !important;
    border-color: #0d542b !important;
}
div[data-testid="stPills"] button:hover {
    border-color: #0d542b !important;
    color: #0d542b !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)
st.subheader("Find your ideal career path!")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("1. Upload your CV *(optional but improves results)*")
    uploaded_file = st.file_uploader("", type=["pdf", "docx"], label_visibility="collapsed")

    cv_text = ""
    if uploaded_file is not None:
        try:
            cv_text = extract_text_from_pdf(uploaded_file)
            st.success("CV uploaded successfully!")
        except Exception:
            st.warning("Could not read CV. Continuing with interests only.")

    st.markdown("2. Select your interests")
    interests = st.pills(
        "Select your interests", INTERESTS,
        selection_mode="multi", label_visibility="collapsed")

    st.divider()

    if st.button("Analyze my profile", type="primary", width="stretch"):
        cv_scores = calculate_cv_scores(cv_text) if cv_text else {j: 0 for j in JOBS}
        interest_scores = calculate_interest_scores(interests)

        combined_scores = {}
        for job in JOBS:
            if cv_text:
                # 70% CV, 30% interests
                combined_scores[job] = round(0.7 * cv_scores[job] + 0.3 * interest_scores[job])
            else:
                # No CV: 100% interests
                combined_scores[job] = interest_scores[job]

        st.session_state["profile"] = {
            "interests": interests,
            "cv_uploaded": uploaded_file is not None,
            "cv_text": cv_text,
            "cv_scores": cv_scores,
            "interest_scores": interest_scores,
            "combined_scores": combined_scores,
        }
        st.switch_page("page1.py")

with col2:
    st.markdown("### What's next?")
    st.write("""
**Careerly will:**
- Match you to top careers
- Identify skill gaps
- Suggest courses
""")
    st.markdown("### Tips")
    st.write("""
- Select multiple interests
- Upload your CV for better results
""")
