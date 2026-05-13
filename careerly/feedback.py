"""
feedback.py - Supabase feedback loop for Careerly.

Two things are tracked:
- Course clicks: when a user marks a course helpful, it gets ranked higher next time
- CV matches: when a user confirms a career match, their CV text is stored
  and later used to enrich the TF-IDF corpus in ml_model.py
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_client():
    """Returns a connected Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def record_helpful_click(skill_gap: str, course_title: str):
    """
    Records that a user found a course helpful for a skill gap.
    Increments the click count if the row exists, otherwise inserts a new one.
    Errors are silently ignored since this is non-critical.
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
        print(f"Feedback recording failed: {e}")


def record_cv_match(job_name: str, cv_text: str):
    """
    Stores a confirmed CV-career match in Supabase.
    Called when the user clicks 'Yes, this is a good match'.
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
    Used in job_page.py to boost that course's ranking in future recommendations.
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
