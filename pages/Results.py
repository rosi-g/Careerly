"""
Results.py - displays the top 3 career matches for the user.

Each card shows:
- Match percentage from the Random Forest model
- Job title and short description
- Radar chart comparing skills match, interest fit, and contextual match
- Button to navigate to the detailed job page
"""

import streamlit as st
import plotly.graph_objects as go
from translations import t, language_toggle, t_job_desc

st.set_page_config(page_title="Results | Careerly", page_icon="🧩", layout="wide")
language_toggle()

if st.button(t("back_to_start")):
    st.switch_page("careerly.py")

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

st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align:center;'>{t('results_subheader')}</h2>", unsafe_allow_html=True)


def create_spider_chart(user_values):
    """
    Builds a three-axis radar chart for one job.
    Axes: skills match, interest fit, contextual match.
    The first category is repeated at the end to close the polygon shape.
    """
    categories = [t("skills_match"), t("interest_fit"), t("contextual_match"), t("skills_match")]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=user_values,
        theta=categories,
        fill="toself",
        name="Your Profile",
        line=dict(color="#0d542b", width=3),
        fillcolor="rgba(13,84,43,0.45)"))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 5])),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=300)
    return fig


def match_header(rank, match_pct, cv_uploaded):
    """
    Renders the green gradient header at the top of each result card.
    Shows rank, match percentage, a progress bar, and a badge for CV vs interests mode.
    """
    badge = t("badge_cv") if cv_uploaded else t("badge_interests")
    st.markdown(f"""
        <div style="
            background:linear-gradient(90deg, #0d542b, #2f7d4f);
            padding: 14px 16px 10px 16px;
            border-radius: 12px 12px 0 0;
            color:white;
            margin: -1rem -1rem -1rem -1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:13px;">#{rank} Match &nbsp;
                    <span style="font-size:11px; background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:999px;">{badge}</span>
                </span>
                <span style="font-size:32px; font-weight:700; line-height:1;">{match_pct}%</span>
            </div>
            <div style="margin-top:10px; background:rgba(225,225,225,0.25); height:8px; border-radius:999px; overflow:hidden;">
                <div style="width:{match_pct}%; background:white; height:100%; border-radius:999px;"></div>
            </div>
        </div>""", unsafe_allow_html=True)


# pull all scores from session state
profile = st.session_state.get("profile", {})
combined_scores = profile.get("combined_scores") or {}
cv_uploaded = profile.get("cv_uploaded", False)
cv_scores = profile.get("cv_scores", {})
interest_scores = profile.get("interest_scores", {})
tfidf_scores = profile.get("tfidf_scores", {})


def build_user_vector(job_name):
    """
    Converts the three raw scores for a job into a 1-5 scale for the radar chart.
    All axes use a fixed max of 100 so scores are absolute, not relative to the best match.
    Values are clamped to a minimum of 1 so the chart never collapses to a dot.
    """
    def to_spider(score, max_val):
        if max_val == 0:
            return 1
        return max(1, min(5, round((score / max_val) * 5, 1)))

    values = [
        to_spider(cv_scores.get(job_name, 0), 100),
        to_spider(interest_scores.get(job_name, 0), 100),
        to_spider(tfidf_scores.get(job_name, 0), 100),
    ]
    return values + [values[0]]  # repeat first value to close the polygon


# sort all jobs by combined score and take top 3
top3 = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:3]

# each of the top 3 maps to its own detail page
page_map = {0: "pages/Details.py", 1: "pages/Details2.py", 2: "pages/Details3.py"}

if not top3:
    st.warning("No profile data found. Please go back and fill in your profile.")
    if st.button("Go back"):
        st.switch_page("Careerly.py")
else:
    cols = st.columns(3)
    for i, (col, (job, score)) in enumerate(zip(cols, top3)):
        with col:
            with st.container(border=True):
                match_header(i + 1, score, cv_uploaded)
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align:center; padding:6px; border-radius:8px;'>{job}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; font-size:0.9rem;'>{t_job_desc(job)}</p>", unsafe_allow_html=True)
                st.plotly_chart(
                    create_spider_chart(build_user_vector(job)),
                    use_container_width=True,
                    key=f"chart_{i}")
                if st.button(f"{job} {t('select_button')}", key=f"btn_{i}", use_container_width=True):
                    st.session_state["selected_career"] = job
                    st.switch_page(page_map[i])

    # --- All Jobs Ranking ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"<h3 style='color:#0d542b;'>{t('all_careers_title')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#666; font-size:0.9rem;'>{t('all_careers_subtitle')}</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    all_jobs_sorted = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    for rank, (job, score) in enumerate(all_jobs_sorted, 1):
        bar_color = "#0d542b" if rank <= 3 else "#7fbf90"
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        col_rank, col_bar, col_score = st.columns([0.5, 8, 1])
        with col_rank:
            st.markdown(
                f"<div style='font-size:1rem; font-weight:700; color:#0d542b; padding-top:6px;'>{medal}</div>",
                unsafe_allow_html=True)
        with col_bar:
            bar_html = (
                f"<div style='margin-top:4px;'>"
                f"<div style='font-size:0.9rem; font-weight:600; color:#1a1a1a; margin-bottom:4px;'>{job}</div>"
                f"<div style='background:#e8f5e9; border-radius:999px; height:10px; overflow:hidden;'>"
                f"<div style='width:{score}%; background:{bar_color}; height:100%; border-radius:999px;'></div>"
                f"</div></div>"
            )
            st.markdown(bar_html, unsafe_allow_html=True)
        with col_score:
            st.markdown(
                f"<div style='font-size:1rem; font-weight:700; color:{bar_color}; text-align:right; padding-top:6px;'>{score}%</div>",
                unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)
