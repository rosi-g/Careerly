"""
generate_labels.py - generates training data for the Random Forest model.

Run this script once to create a CSV of user-job profile scenarios.
Your team then fills in the match_score column (0-100) for each row.
That labeled CSV becomes the training data for ml_model.py.

Usage:
    python generate_labels.py

Output:
    training_labels.csv — open in Excel or Google Sheets, fill in match_score, save.

Labeling tips:
- High interest alone is not enough (cap around 30-40)
- High interest + high ESCO together deserve a big boost
- Low interest should cap the score at 30-40 even if skills are perfect
- All three high = 85-100
- All three low = 0-10
"""

import pandas as pd
import numpy as np

N_PROFILES = 80

rng = np.random.RandomState(0)

# structured grid so all regions of the (esco, interest, tfidf) cube are covered
# 3 levels x 3 scores = 27 base points, each with 3 noisy variants
profiles = []

levels = [15, 50, 85]
for e in levels:
    for i in levels:
        for t in levels:
            for _ in range(3):
                esco     = int(np.clip(rng.normal(e, 8), 0, 100))
                interest = int(np.clip(rng.normal(i, 8), 0, 100))
                tfidf    = int(np.clip(rng.normal(t, 8), 0, 100))
                profiles.append((esco, interest, tfidf))

# fill remaining slots with random profiles for extra coverage
while len(profiles) < N_PROFILES:
    esco     = int(rng.uniform(0, 100))
    interest = int(rng.uniform(0, 100))
    tfidf    = int(rng.uniform(0, 100))
    profiles.append((esco, interest, tfidf))

profiles = profiles[:N_PROFILES]

df = pd.DataFrame(profiles, columns=["esco_score", "interest_score", "tfidf_score"])
df.index.name = "id"
df["match_score"] = ""  # fill this in manually
df["notes"] = ""        # optional reasoning column

output_path = "training_labels.csv"
df.to_csv(output_path)

print(f"Generated {N_PROFILES} profiles -> {output_path}")
print("Open the CSV, fill in match_score (0-100) for each row, then save.")
