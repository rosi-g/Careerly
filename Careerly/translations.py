"""
translations.py - handles all text translations for Careerly (EN/DE).

All strings come from translations.xlsx, which has separate sheets for:
- ui_strings: general UI labels and messages
- interests: interest category names
- job_descriptions_short: one-line job summaries shown on the results page
- job_descriptions_long: full job descriptions shown on the detail page
- skill_names: ESCO skill names
- career_twins: career twin fun facts per job

The active language is stored in st.session_state["lang"] and defaults to "en".
"""

import streamlit as st
import pandas as pd
from pathlib import Path

_BASE = Path(__file__).parent
_xl = pd.ExcelFile(_BASE / "translations.xlsx")

def _load(sheet, key_col, lang_cols):
    """Parses one sheet from the Excel file into a nested dict: key -> {lang -> text}."""
    df = _xl.parse(sheet).fillna("")
    return {
        row[key_col]: {lang: row[lang] for lang in lang_cols}
        for _, row in df.iterrows()
    }

# load all sheets once at startup
TRANSLATIONS                       = _load("ui_strings",            "key",   ["en", "de"])
INTERESTS_EN_TO_DE                 = dict(zip(
    _xl.parse("interests")["en"], _xl.parse("interests")["de"]
))
INTERESTS_DE_TO_EN                 = {v: k for k, v in INTERESTS_EN_TO_DE.items()}
JOB_DESCRIPTIONS_TRANSLATED        = _load("job_descriptions_short", "job",   ["en", "de"])
JOB_DETAIL_DESCRIPTIONS_TRANSLATED = _load("job_descriptions_long",  "job",   ["en", "de"])
SKILL_NAMES_TRANSLATED             = _load("skill_names",           "skill", ["en", "de"])
CAREER_TWINS_TRANSLATED            = _load("career_twins",          "job",   ["en", "de"])


def _lang():
    """Returns the active language code ('en' or 'de')."""
    return st.session_state.get("lang", "en")

def t(key: str) -> str:
    """Looks up a UI string by key in the active language. Falls back to the key itself."""
    return TRANSLATIONS.get(key, {}).get(_lang(), key)

def t_skill(skill_name: str) -> str:
    """Returns the translated skill name."""
    return SKILL_NAMES_TRANSLATED.get(skill_name, {}).get(_lang(), skill_name)

def t_job_desc(job_name: str) -> str:
    """Returns the short job description for the results page."""
    return JOB_DESCRIPTIONS_TRANSLATED.get(job_name, {}).get(_lang(), "")

def t_job_detail(job_name: str) -> str:
    """Returns the full job description for the detail page."""
    return JOB_DETAIL_DESCRIPTIONS_TRANSLATED.get(job_name, {}).get(_lang(), "")

def t_twin_fact(job_name: str) -> str:
    """Returns the career twin fun fact for a given job."""
    return CAREER_TWINS_TRANSLATED.get(job_name, {}).get(_lang(), "")

def get_interests_display(interests_en: list) -> list:
    """Converts English interest names to German if the active language is DE."""
    if _lang() == "de":
        return [INTERESTS_EN_TO_DE.get(i, i) for i in interests_en]
    return interests_en

def map_interests_to_en(selected: list) -> list:
    """Converts selected interest labels back to English regardless of display language."""
    if _lang() == "de":
        return [INTERESTS_DE_TO_EN.get(i, i) for i in selected]
    return selected

def language_toggle():
    """Renders the EN/DE toggle button in the top-right corner."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button(t("lang_toggle"), key="lang_btn"):
            st.session_state["lang"] = "de" if st.session_state["lang"] == "en" else "en"
            st.rerun()
