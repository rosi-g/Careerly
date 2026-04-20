import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Results | Careerly", page_icon="🧩", layout="wide")
st.markdown("<h1 style='color:#0d542b;'>Careerly</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;'>Your Top 3:</h2>", unsafe_allow_html=True)

# Spider chart profiles per job: Skills, Interests, Education, Languages, Experience
JOB_PROFILES = {
    "Financial Analyst":      [4, 3, 4, 1, 3],
    "Investment Banker":      [4, 4, 4, 1, 5],
    "Management Consultant":  [4, 3, 3, 2, 5],
    "Marketing Manager":      [3, 5, 3, 2, 3],
    "Data Analyst":           [5, 4, 4, 1, 3],
    "Software Engineer":      [5, 3, 4, 1, 3],
    "Corporate Lawyer":       [3, 2, 5, 3, 3],
    "Tax Lawyer":             [3, 2, 5, 1, 3],
    "HR Manager":             [3, 4, 3, 2, 3],
    "Operations Manager":     [4, 3, 4, 2, 4],
    "Product Manager":        [4, 5, 3, 2, 3],
    "Strategy Consultant":    [4, 3, 3, 2, 5],
    "Brand Manager":          [3, 5, 3, 2, 3],
    "Supply Chain Manager":   [4, 3, 4, 2, 4],
    "Entrepreneur":           [4, 5, 2, 2, 3],
}

JOB_DESCRIPTIONS = {
    "Financial Analyst": "Analyze financial data, build models, and support investment or business decisions. Perfect for those who love numbers and economics.",
    "Investment Banker": "Help companies raise capital, execute mergers and acquisitions, and navigate complex financial transactions.",
    "Management Consultant": "Help organizations solve complex problems and improve performance across strategy, operations, and more.",
    "Marketing Manager": "Create and execute campaigns that build brand awareness, drive customer acquisition, and grow revenue.",
    "Data Analyst": "Turn raw data into actionable insights using statistics, visualization tools, and analytical thinking.",
    "Software Engineer": "Design and build software systems and applications that power modern businesses.",
    "Corporate Lawyer": "Advise businesses on legal matters including contracts, compliance, and corporate transactions.",
    "Tax Lawyer": "Help individuals and companies navigate tax obligations, planning, and regulatory compliance.",
    "HR Manager": "Attract, develop, and retain talent while building a strong company culture and people strategy.",
    "Operations Manager": "Oversee day-to-day business operations, improve processes, and ensure efficiency across the organization.",
    "Product Manager": "Define product vision, work cross-functionally, and bring new products from idea to launch.",
    "Strategy Consultant": "Help executives define long-term direction, competitive positioning, and transformation roadmaps.",
    "Brand Manager": "Build and protect brand identity, manage creative campaigns, and connect with consumers emotionally.",
    "Supply Chain Manager": "Optimize the flow of goods from suppliers to customers through smart logistics and procurement.",
    "Entrepreneur": "Build something from scratch — identify opportunities, take risks, and create value through innovation.",
}

def create_spider_chart(user_values, job_values):
    categories = ["Skills", "Interests", "Education", "Languages", "Experience"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=user_values, theta=categories, fill="toself",
        name="Your Profile", line=dict(color="#0d542b", width=3),
        fillcolor="rgba(13,84,43,0.45)"))
    fig.add_trace(go.Scatterpolar(
        r=job_values, theta=categories, fill="toself",
        name="Career Match", line=dict(color="#7fbf90", width=3),
        fillcolor="rgba(127,191,144,0.35)"))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 5])),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=20, b=20), height=300)
    return fig

def match_header(rank, match_pct, cv_uploaded):
    badge = "📄 CV + Interests" if cv_uploaded else "Interests only"
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

# --- Get data from session state ---
profile = st.session_state.get("profile", {})
combined_scores = profile.get("combined_scores", {})
cv_uploaded = profile.get("cv_uploaded", False)
interests = profile.get("interests", [])

# --- User spider chart vector ---
user = [3, 3, 3, 2, 2]
interest_axis_map = {
    "Finance": 1,
    "Business & Strategy": 1,
    "Marketing & Communication": 2,
    "Technology & Data": 0,
    "Law & Compliance": 2,
    "People & Culture": 1,
    "International & Diplomacy": 3,
    "Entrepreneurship & Innovation": 2,
    "Operations & Logistics": 0,
}
for interest in interests:
    idx = interest_axis_map.get(interest, 1)
    user[idx] = min(user[idx] + 1, 5)

# --- Get top 3 ---
top3 = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:3]
page_map = {0: "pages/page3.py", 1: "pages/page4.py", 2: "pages/page5.py"}

if not top3:
    st.warning("No profile data found. Please go back and fill in your profile.")
    if st.button("Go back"):
        st.switch_page("careerly.py")
else:
    cols = st.columns(3)
    for i, (col, (job, score)) in enumerate(zip(cols, top3)):
        with col:
            with st.container(border=True):
                match_header(i + 1, score, cv_uploaded)
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align:center; background:#d4edda; padding:6px; border-radius:8px;'>{job}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; font-size:0.9rem;'>{JOB_DESCRIPTIONS.get(job, '')}</p>", unsafe_allow_html=True)
                st.plotly_chart(
                    create_spider_chart(user, JOB_PROFILES.get(job, [3, 3, 3, 2, 2])),
                    use_container_width=True, key=f"chart_{i}")
                if st.button(f"Select {job}", key=f"btn_{i}", use_container_width=True):
                    st.session_state["selected_career"] = job
                    st.switch_page(page_map[i])
