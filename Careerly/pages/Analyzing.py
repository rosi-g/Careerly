"""
Analyzing.py - loading screen shown between the main page and results.

All scoring is already done in careerly.py before this page loads.
This page is purely cosmetic: it shows a progress bar with step labels,
then redirects to Results.py.
"""

import streamlit as st
import time
from translations import t, language_toggle, get_interests_display

st.set_page_config(
    page_title="Analyzing | Careerly",
    page_icon="🧩",
    layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {
    display: none;
}
[data-testid="collapsedControl"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

language_toggle()

st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)
st.subheader(t("analyzing_subheader"))

# show what was submitted
profile = st.session_state.get("profile", {})

if profile.get("cv_uploaded"):
    st.success(t("cv_uploaded_ok"), icon="✅")
else:
    st.warning(t("no_cv_warning"), icon="⚠️")

interests = profile.get("interests", [])
if interests:
    st.write(t("selected_interests") + ", ".join(get_interests_display(interests)))
else:
    st.write(t("no_interests"))

# animated progress bar stepping through the five analysis stages
progress_text = st.empty()
progress_bar = st.progress(0)

steps = [t("step_reading"), t("step_extracting"), t("step_matching"), t("step_gaps"), t("step_preparing")]

for i, step in enumerate(steps):
    progress_text.write(step)
    progress_bar.progress((i + 1) * 20)
    time.sleep(0.7)

time.sleep(0.5)
st.switch_page("pages/Results.py")
