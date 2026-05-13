"""
ml_model.py - career matching model for Careerly.

What happens here:
- Builds a TF-IDF representation of each job's description and skills
- Compares a user's CV against that representation to get a similarity score
- Trains a Random Forest on manually labeled (esco, interest, tfidf) -> match score data
- Combines all three scores per job into one final match percentage

Why Random Forest and not a simple weighted average?
A weighted sum treats the three scores independently. The forest learns interactions,
e.g. high interest + high ESCO together should score much better than either alone.
That non-linear behavior is what we want.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import cross_val_score

LABELS_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_labels.csv")


def build_job_corpus(stored_cvs: dict = None) -> tuple[list[str], list[str]]:
    """
    Builds a text document for each job using only:
    - ESCO job description (natural language context, from translations.xlsx)
    - Confirmed CV matches from Supabase (real student CVs that led to this career)

    Skill keywords are intentionally excluded because they are already captured
    by the ESCO keyword score. Including them here would create overlap between
    the context score and the skills score, reducing the Random Forest's ability
    to learn meaningful interactions between the two.

    Returns two lists: job names and their corresponding text documents.
    """
    import pandas as pd
    base_dir = os.path.dirname(os.path.abspath(__file__))
    xl = pd.ExcelFile(os.path.join(base_dir, "translations.xlsx"))
    desc_df = xl.parse("job_descriptions_long").fillna("")
    descriptions = dict(zip(desc_df["job"], desc_df["en"]))

    job_names, job_texts = [], []
    for job_name, description in descriptions.items():
        combined = description.strip()

        # Append confirmed CV matches from Supabase — this is what makes
        # the context score improve over time as more students use the app
        if stored_cvs and job_name in stored_cvs:
            combined += " " + " ".join(stored_cvs[job_name])

        job_names.append(job_name)
        job_texts.append(combined)

    return job_names, job_texts


def calculate_tfidf_scores(cv_text: str, job_details: dict = None) -> dict[str, int]:
    """
    Computes TF-IDF cosine similarity between the CV and each job's ESCO description.
    Returns a score from 0 to 100 per job.

    The corpus is built from ESCO job descriptions only (no skill keywords).
    Confirmed CV matches from Supabase are appended over time to enrich the corpus.

    Why 0.30 as ceiling and not the max similarity in the batch?
    Normalizing against the best match in a given run makes scores relative and unstable.
    A fixed ceiling gives consistent absolute scores. Typical student CVs scored 0.10-0.28.
    """
    if not cv_text or not cv_text.strip():
        # return zeros for all jobs from translations
        try:
            import pandas as pd
            base_dir = os.path.dirname(os.path.abspath(__file__))
            xl = pd.ExcelFile(os.path.join(base_dir, "translations.xlsx"))
            jobs = xl.parse("job_descriptions_long")["job"].tolist()
            return {job: 0 for job in jobs}
        except Exception:
            return {}

    # try to pull confirmed CV matches from Supabase to enrich the corpus
    try:
        from feedback import fetch_cv_matches
        stored_cvs = fetch_cv_matches()
    except Exception:
        stored_cvs = {}

    job_names, job_texts = build_job_corpus(stored_cvs)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),   # includes bigrams like "financial modeling"
        min_df=1,
        max_df=0.85,          # drops terms appearing in 85%+ of job docs (too generic)
        sublinear_tf=True,    # log-scale term frequency to reduce skew from repeated words
    )

    # fit on all job texts, then transform both jobs and CV
    job_matrix = vectorizer.fit_transform(job_texts)
    cv_vector = vectorizer.transform([cv_text.lower()])

    # cosine similarity gives a value between 0 and 1 for each job
    similarities = cosine_similarity(cv_vector, job_matrix)[0]

    TFIDF_CEILING = 0.30
    return {
        job_names[i]: int(min(round((similarities[i] / TFIDF_CEILING) * 100), 100))
        for i in range(len(job_names))
    }


def _load_from_csv(path: str) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Loads labeled training data from CSV.
    Skips rows where match_score is missing.
    Returns None if the file doesn't exist or has fewer than 10 labeled rows.
    """
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)

    # drop rows where match_score wasn't filled in yet
    df = df[pd.to_numeric(df["match_score"], errors="coerce").notna()]
    df["match_score"] = pd.to_numeric(df["match_score"])

    if len(df) < 10:
        print(f"[ml_model] Only {len(df)} labeled rows — please label more.")
        return None

    X = df[["esco_score", "interest_score", "tfidf_score"]].values.astype(float)
    y = df["match_score"].values.astype(float) / 100.0  # convert 0-100 to 0.0-1.0

    print(f"[ml_model] Loaded {len(df)} labeled profiles from {path}")
    return X, y


def generate_training_data() -> tuple[np.ndarray, np.ndarray]:
    """
    Loads training data from training_labels.csv.
    Raises a FileNotFoundError if the file is missing or doesn't have enough rows.
    """
    data = _load_from_csv(LABELS_CSV_PATH)
    if data is None:
        raise FileNotFoundError(
            "\n[ml_model] training_labels.csv not found or has fewer than 10 labeled rows.\n"
            "Run: python generate_labels.py -- then fill in the match_score column."
        )
    return data


def train_match_model() -> tuple[RandomForestRegressor, StandardScaler, float]:
    """
    Trains a RandomForestRegressor on the labeled CSV data.
    Returns the trained model, the fitted scaler, and the 5-fold CV RMSE.

    Hyperparameter choices:
    - n_estimators=200: 200 trees gives stable predictions on a small dataset
    - max_depth=5: shallow trees to avoid overfitting
    - min_samples_leaf=4: each leaf needs at least 4 samples

    StandardScaler is used because different score ranges can bias tree splits.
    5-fold cross-validation gives an estimate of how the model performs on unseen data.
    """
    X, y = generate_training_data()

    # scale features so all three scores are on the same scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=5,
        min_samples_leaf=4,
        random_state=42,
    )
    model.fit(X_scaled, y)

    # 5-fold CV: split data into 5 parts, train on 4, test on 1, repeat
    # neg_root_mean_squared_error returns negative values so we flip the sign
    cv_scores = cross_val_score(
        model, X_scaled, y,
        cv=5,
        scoring="neg_root_mean_squared_error"
    )
    cv_rmse = -cv_scores.mean()

    return model, scaler, cv_rmse


# train once at startup so all prediction calls reuse the same model
_model, _scaler, _cv_rmse = train_match_model()

# these are exposed so other parts of the app can display model info
MODEL_CV_RMSE = _cv_rmse
MODEL_FEATURE_IMPORTANCES = dict(zip(
    ["esco_score", "interest_score", "tfidf_score"],
    _model.feature_importances_
))
MODEL_USING_CSV = os.path.exists(LABELS_CSV_PATH)


def predict_match_score(esco: float, interest: float, tfidf: float) -> float:
    """
    Predicts the match quality for one user-job pair.
    Returns a float between 0.0 and 1.0.
    """
    features = np.array([[esco, interest, tfidf]])
    features_scaled = _scaler.transform(features)
    score = _model.predict(features_scaled)[0]

    # clip to [0, 1] in case the forest predicts slightly outside that range
    return float(np.clip(score, 0.0, 1.0))


def combine_scores(
    esco_scores: dict,
    interest_scores: dict,
    tfidf_scores: dict,
    cv_uploaded: bool,
) -> dict[str, int]:
    """
    Runs the Random Forest for every job and returns match percentages (0-100).

    If no CV was uploaded, ESCO and TF-IDF are set to 0 so the model
    scores based on interest alignment only.
    """
    raw_scores = {}
    for job in esco_scores:
        esco = esco_scores.get(job, 0)
        interest = interest_scores.get(job, 0)
        tfidf = tfidf_scores.get(job, 0)

        if not cv_uploaded:
            # no CV means we can only use interest score
            raw_scores[job] = predict_match_score(0, interest, 0)
        else:
            raw_scores[job] = predict_match_score(esco, interest, tfidf)

    # convert 0.0-1.0 floats to 0-100 integers for display
    return {
        job: round(score * 100)
        for job, score in raw_scores.items()
    }
