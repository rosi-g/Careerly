"""
feedback.py -- Supabase feedback loop for course and career match tracking.

Two things are tracked:
- Course helpfulness clicks: when a user marks a course as helpful for a skill gap,
  that course gets boosted in future recommendations for the same gap.
- CV-career matches: when a user confirms a career is a good match, their CV text
  is stored and later used to enrich the TF-IDF corpus in ml_model.py.
"""

import os
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_client():
    """Returns a connected Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def record_helpful_click(skill_gap: str, course_title: str):
    """
    Records that a user found a course helpful for a specific skill gap.
    If the (skill_gap, course_title) pair exists, increments the click count.
    Otherwise inserts a new row with clicks=1.
    """
    try:
        client = get_client()
        existing = (
            client.table("course_clicks")
            .select("id, clicks")
            .eq("skill_gap", skill_gap)
            .eq("course_title", course_title)
            .execute()
        )
        if existing.data:
            row_id = existing.data[0]["id"]
            new_count = existing.data[0]["clicks"] + 1
            client.table("course_clicks").update({"clicks": new_count}).eq("id", row_id).execute()
        else:
            client.table("course_clicks").insert({
                "skill_gap": skill_gap,
                "course_title": course_title,
                "clicks": 1,
            }).execute()
    except Exception as e:
        # non-critical, ignore errors
        print(f"Feedback recording failed: {e}")


def record_cv_match(job_name: str, cv_text: str):
    """
    Stores a confirmed CV-career match in Supabase.
    Called when the user clicks 'Yes, this is a good match' on a job page.
    CV text is capped at 5000 chars to stay within database limits.
    """
    if not cv_text or not cv_text.strip():
        return
    try:
        client = get_client()
        client.table("cv_career_matches").insert({
            "job_name": job_name,
            "cv_text": cv_text[:5000],
        }).execute()
    except Exception as e:
        print(f"CV match recording failed: {e}")


def fetch_cv_matches() -> dict:
    """
    Fetches all confirmed CV-career matches from Supabase.
    Returns a dict of job_name -> list of CV texts.
    Used by ml_model.py to enrich the TF-IDF corpus.
    """
    try:
        client = get_client()
        result = (
            client.table("cv_career_matches")
            .select("job_name, cv_text")
            .execute()
        )
        matches = {}
        for row in result.data:
            job = row["job_name"]
            if job not in matches:
                matches[job] = []
            matches[job].append(row["cv_text"])
        return matches
    except Exception:
        return {}


def get_click_boost(skill_gap: str, course_title: str) -> int:
    """
    Returns how many times a course has been marked helpful for a given skill gap.
    Used in job_page.py to boost course ranking in recommendations.
    """
    try:
        client = get_client()
        result = (
            client.table("course_clicks")
            .select("clicks")
            .eq("skill_gap", skill_gap)
            .eq("course_title", course_title)
            .execute()
        )
        if result.data:
            return result.data[0]["clicks"]
        return 0
    except Exception:
        return 0
