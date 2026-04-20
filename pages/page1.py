import streamlit as st
import time

st.set_page_config(
	page_title="Analyzing | Careerly",
	page_icon="🧩",
	layout="wide")

st.markdown(
	"<h1 style='color:#0d542b;'>Careerly</h1>",
	unsafe_allow_html=True)

st.subheader("Analyzing your profile...")
profile= st.session_state.get("profile",{})


if profile.get("cv_uploaded"):
	st.success("CV uploaded successfully", icon="✅")

else:
	st.warning("No CV uploaded, using manual inputs only", icon="⚠️")

interests = profile.get("interests", [])
if interests:
		st.write("**Selected interests:** "+", ".join(interests))

else:
	st.write("**Selected interests:** none")


progress_text=st.empty()
progress_bar=st.progress(0)

steps=[
	"Reading profile...",
	"Extracting relevant information...",
	"Matching career paths...",
	"Calculating skill gaps...",
	"Preparing recommendations..."]

for i, step in enumerate(steps):
	progress_text.write(step)
	progress_bar.progress((i+1)*20)
	time.sleep(0.7)

time.sleep(0.5)
st.switch_page("page2.py")
