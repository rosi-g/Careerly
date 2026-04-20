import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from job_page import show_job_page
import streamlit as st

career = st.session_state.get("selected_career", "Marketing Manager")
show_job_page(career)
