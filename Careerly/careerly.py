"""
careerly.py - main entry point for the Careerly app.

What happens here:
- User uploads a CV (PDF) and selects interests
- Three scores are calculated per job: ESCO keyword match, interest match, TF-IDF match
- The Random Forest model combines them into a final match percentage
- Everything is stored in session state and the user is redirected to the results page
"""

import streamlit as st
import PyPDF2
import nltk
import sys
import os
from translations import t, language_toggle, get_interests_display, map_interests_to_en

nltk.download('stopwords', quiet=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from job_page import JOB_DETAILS, SKILLS_FROM_EXCEL
from ml_model import calculate_tfidf_scores, combine_scores

JOBS = list(JOB_DETAILS.keys())

# 24 interest categories shown to the user as selectable pills
INTERESTS = [
    "Numbers", "Creativity", "People", "Languages", "Writing",
    "Technology", "Detail & Precision", "Leadership", "Problem Solving",
    "Research", "Law & Justice", "International", "Entrepreneurship",
    "Strategy", "Sustainability", "Communication", "Mathematics",
    "Culture", "Organisation", "Innovation", "Data", "Finance",
    "Design", "Negotiation",
]

# How much each interest contributes to each job's interest score.
# Based on ESCO v1.2 skill profiles. Each job's values across all 24 interests sum to 100.
INTEREST_SPREAD = {
    "Numbers": {
        'Financial Analyst': 39.2, 'Corporate Investment Banker': 33.1, 'Tax Advisor': 30.4,
        'Supply Chain Manager': 14.8, 'Marketing Manager': 14.5, 'Product Manager': 13.2,
        'Entrepreneur': 13.0, 'Business Consultant': 12.2, 'Brand Manager': 7.5,
        'Strategic Planning Manager': 3.9, 'Human Resources Manager': 2.4,
        'Data Analyst': 1.5, 'ICT Application Developer': 1.4,
    },
    "Creativity": {
        'Brand Manager': 26.4, 'Marketing Manager': 10.5, 'Product Manager': 7.9,
        'ICT Application Developer': 7.2, 'Data Analyst': 4.9, 'Entrepreneur': 4.1,
        'Supply Chain Manager': 1.1, 'Financial Analyst': 1.7,
    },
    "People": {
        'Human Resources Manager': 19.7, 'Corporate Lawyer': 19.0, 'Brand Manager': 15.1,
        'Product Manager': 13.2, 'Marketing Manager': 10.5, 'Supply Chain Manager': 10.2,
        'Business Consultant': 7.8, 'Tax Advisor': 7.1, 'Data Analyst': 2.4,
        'Corporate Investment Banker': 2.3, 'Entrepreneur': 4.1,
        'ICT Application Developer': 1.4, 'Strategic Planning Manager': 0.8, 'Financial Analyst': 0.8,
    },
    "Languages": {
        'Data Analyst': 1.9, 'ICT Application Developer': 1.4, 'Marketing Manager': 1.3,
        'Entrepreneur': 0.8, 'Human Resources Manager': 0.8, 'Strategic Planning Manager': 0.8,
        'Corporate Investment Banker': 0.8,
    },
    "Writing": {
        'Marketing Manager': 2.6, 'Product Manager': 1.8, 'Tax Advisor': 1.8,
        'Corporate Investment Banker': 1.5, 'ICT Application Developer': 1.4,
        'Supply Chain Manager': 1.1, 'Data Analyst': 1.0, 'Brand Manager': 0.9,
        'Entrepreneur': 0.8, 'Human Resources Manager': 0.8,
    },
    "Technology": {
        'ICT Application Developer': 55.1, 'Data Analyst': 9.2, 'Supply Chain Manager': 4.5,
        'Financial Analyst': 2.5, 'Brand Manager': 1.9,
        'Entrepreneur': 1.6, 'Human Resources Manager': 0.8, 'Strategic Planning Manager': 0.8,
    },
    "Detail & Precision": {
        'Supply Chain Manager': 11.4, 'Corporate Investment Banker': 9.8, 'Data Analyst': 8.3,
        'Product Manager': 5.3, 'Human Resources Manager': 5.5, 'Strategic Planning Manager': 4.7,
        'Entrepreneur': 4.9, 'ICT Application Developer': 4.3, 'Tax Advisor': 1.8,
        'Business Consultant': 1.7, 'Marketing Manager': 1.3,
    },
    "Leadership": {
        'Strategic Planning Manager': 12.4, 'Business Consultant': 11.3, 'Supply Chain Manager': 9.1,
        'Entrepreneur': 4.9, 'Human Resources Manager': 5.5, 'Financial Analyst': 3.3,
        'ICT Application Developer': 2.9, 'Corporate Lawyer': 2.4, 'Corporate Investment Banker': 1.5,
        'Brand Manager': 0.9,
    },
    "Problem Solving": {
        'Supply Chain Manager': 8.0, 'Business Consultant': 7.8, 'Human Resources Manager': 7.1,
        'Corporate Lawyer': 6.0, 'ICT Application Developer': 5.8, 'Entrepreneur': 5.7,
        'Marketing Manager': 5.9, 'Financial Analyst': 4.2, 'Data Analyst': 4.4,
        'Strategic Planning Manager': 4.7, 'Brand Manager': 2.8, 'Product Manager': 1.8,
        'Corporate Investment Banker': 1.5, 'Tax Advisor': 0.0,
    },
    "Research": {
        'Marketing Manager': 7.9, 'Product Manager': 7.9, 'Financial Analyst': 4.2,
        'Tax Advisor': 3.6, 'Brand Manager': 3.8, 'Data Analyst': 2.9,
        'Strategic Planning Manager': 1.6, 'ICT Application Developer': 1.4, 'Entrepreneur': 0.8,
    },
    "Law & Justice": {
        'Corporate Lawyer': 47.6, 'Tax Advisor': 25.0, 'Human Resources Manager': 15.0,
        'Strategic Planning Manager': 3.1, 'Business Consultant': 0.9, 'Product Manager': 0.9,
        'Entrepreneur': 1.6, 'Financial Analyst': 0.8,
    },
    "International": {
        'Product Manager': 3.5, 'Marketing Manager': 3.9, 'Tax Advisor': 3.6,
        'Strategic Planning Manager': 2.3, 'Brand Manager': 1.9, 'Entrepreneur': 0.8,
        'Supply Chain Manager': 1.1, 'Business Consultant': 0.9, 'Financial Analyst': 0.8,
    },
    "Entrepreneurship": {
        'Entrepreneur': 3.3, 'Corporate Investment Banker': 1.5, 'Business Consultant': 1.7,
        'Marketing Manager': 1.3,
    },
    "Strategy": {
        'Strategic Planning Manager': 30.2, 'Marketing Manager': 14.5, 'Business Consultant': 12.2,
        'Brand Manager': 13.2, 'Product Manager': 8.8, 'Human Resources Manager': 8.7,
        'Tax Advisor': 5.4, 'Financial Analyst': 3.3, 'Entrepreneur': 3.3,
        'Supply Chain Manager': 2.3, 'Data Analyst': 0.5,
    },
    "Sustainability": {
        'Entrepreneur': 11.4, 'Strategic Planning Manager': 4.7, 'Supply Chain Manager': 4.5,
        'Data Analyst': 1.5, 'ICT Application Developer': 1.4, 'Corporate Investment Banker': 0.8,
        'Business Consultant': 0.9,
    },
    "Communication": {
        'Strategic Planning Manager': 6.2, 'Brand Manager': 5.7, 'Entrepreneur': 3.3,
        'Marketing Manager': 3.9, 'Data Analyst': 1.9, 'Human Resources Manager': 3.1,
        'Product Manager': 2.6, 'Supply Chain Manager': 2.3, 'Corporate Lawyer': 2.4,
    },
    "Mathematics": {
        'Business Consultant': 1.7, 'Brand Manager': 0.9,
    },
    "Culture": {
        'Entrepreneur': 13.0, 'Brand Manager': 5.7, 'Marketing Manager': 4.6,
        'Strategic Planning Manager': 3.9, 'Human Resources Manager': 3.1,
        'Supply Chain Manager': 3.4, 'Product Manager': 1.8, 'Business Consultant': 2.6,
    },
    "Organisation": {
        'Business Consultant': 20.0, 'Strategic Planning Manager': 17.8,
        'Human Resources Manager': 15.7, 'Supply Chain Manager': 14.8, 'Entrepreneur': 13.0,
        'Tax Advisor': 12.5, 'Financial Analyst': 7.5, 'Corporate Investment Banker': 6.0,
        'Data Analyst': 5.8, 'Product Manager': 6.1, 'Marketing Manager': 6.6, 'Brand Manager': 3.8,
    },
    "Innovation": {
        'Entrepreneur': 2.4, 'Product Manager': 1.8, 'Brand Manager': 1.9,
        'ICT Application Developer': 1.4, 'Data Analyst': 0.5,
    },
    "Data": {
        'Data Analyst': 41.3, 'Financial Analyst': 8.3, 'Product Manager': 3.5,
        'Marketing Manager': 2.6, 'Entrepreneur': 2.4, 'Supply Chain Manager': 1.1,
        'Business Consultant': 0.9, 'Brand Manager': 0.9, 'Corporate Investment Banker': 0.8,
    },
    "Finance": {
        'Corporate Investment Banker': 31.6, 'Financial Analyst': 10.8, 'Tax Advisor': 5.4,
        'Product Manager': 5.3, 'Business Consultant': 3.5, 'Brand Manager': 1.9,
        'Supply Chain Manager': 1.1, 'Entrepreneur': 1.6, 'Marketing Manager': 1.3,
    },
    "Design": {
        'ICT Application Developer': 13.0, 'Product Manager': 8.8, 'Data Analyst': 3.4,
        'Entrepreneur': 3.3, 'Human Resources Manager': 2.4, 'Brand Manager': 1.9,
        'Financial Analyst': 1.7, 'Supply Chain Manager': 1.1, 'Strategic Planning Manager': 0.8,
    },
    "Negotiation": {
        'Supply Chain Manager': 4.5, 'Corporate Lawyer': 3.6, 'Financial Analyst': 2.5,
        'Business Consultant': 2.6, 'Human Resources Manager': 2.4, 'Tax Advisor': 1.8,
        'Corporate Investment Banker': 1.5, 'Data Analyst': 1.0, 'Strategic Planning Manager': 0.8,
    },
}


# --- Functions ---

def extract_text_from_pdf(uploaded_file):
    """Reads all pages of the uploaded PDF and returns the full text as one string."""
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def calculate_cv_scores(cv_text, min_keywords=2):
    """
    Scores each job based on ESCO keyword matching against the CV.

    For each skill, counts how many keywords appear in the CV.
    A skill counts as matched if at least min_keywords are found.
    Score = matched skills / total skills * 100.
    """
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
    """
    Sums INTEREST_SPREAD values for each selected interest per job.
    Returns a dict of job -> raw score. Score is a subset of 100
    depending on how many interests were selected.
    """
    scores = {job: 0 for job in JOBS}
    if not interests:
        return scores
    for interest in interests:
        spread = INTEREST_SPREAD.get(interest, {})
        for job, points in spread.items():
            if job in scores:
                scores[job] += points
    return scores


# --- Page setup ---

st.set_page_config(page_title="Careerly", page_icon="🧩", layout="wide")
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
</style>
""", unsafe_allow_html=True)

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

st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)
st.subheader(t("start_subheader"))

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(t("cv_upload_label"))
    uploaded_file = st.file_uploader("Upload your CV", type=["pdf", "docx"], label_visibility="collapsed")

    cv_text = ""
    if uploaded_file is not None:
        try:
            cv_text = extract_text_from_pdf(uploaded_file)
            st.success(t("cv_success"))
        except Exception:
            st.warning(t("cv_warning"))

    st.markdown(t("interests_label"))
    interests_display = get_interests_display(INTERESTS)
    selected_display = st.pills(
        "Select your interests", interests_display,
        selection_mode="multi", label_visibility="collapsed")
    interests = map_interests_to_en(selected_display)

    st.divider()

    if st.button(t("analyze_button"), type="primary", width="stretch"):
        cv_scores = calculate_cv_scores(cv_text) if cv_text else {j: 0 for j in JOBS}
        interest_scores = calculate_interest_scores(interests)
        tfidf_scores = calculate_tfidf_scores(cv_text, JOB_DETAILS)

        # run all three scores through the Random Forest to get final match %
        try:
            combined_scores = combine_scores(
                esco_scores=cv_scores,
                interest_scores=interest_scores,
                tfidf_scores=tfidf_scores,
                cv_uploaded=uploaded_file is not None,
            )
        except Exception as e:
            st.error(f"Model error: {e}")
            st.stop()

        # store everything in session state so results and detail pages can use it
        st.session_state["profile"] = {
            "interests": interests,
            "cv_uploaded": uploaded_file is not None,
            "cv_text": cv_text,
            "cv_scores": cv_scores,
            "interest_scores": interest_scores,
            "tfidf_scores": tfidf_scores,
            "combined_scores": combined_scores,
        }
        st.switch_page("pages/Analyzing.py")

with col2:
    st.markdown(t("whats_next_title"))
    st.write(t("whats_next_body"))
    st.markdown(t("tips_title"))
    st.write(t("tips_body"))
