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
from shared_data import INTEREST_SPREAD, JOB_DETAILS
from translations import t, language_toggle, get_interests_display, map_interests_to_en

nltk.download('stopwords', quiet=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from job_page import SKILLS_FROM_EXCEL
from ml_model import calculate_tfidf_scores, combine_scores

JOBS = list(SKILLS_FROM_EXCEL.keys())

# 24 interest categories shown to the user as selectable pills
INTERESTS = [
    "Numbers", "Creativity", "People", "Languages", "Writing",
    "Technology", "Detail & Precision", "Leadership", "Problem Solving",
    "Research", "Law & Justice", "International", "Entrepreneurship",
    "Strategy", "Sustainability", "Communication", "Mathematics",
    "Culture", "Organisation", "Innovation", "Data", "Finance",
    "Design", "Negotiation",
]

from shared_data import INTEREST_SPREAD

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
        skills = SKILLS_FROM_EXCEL.get(job, [])
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
