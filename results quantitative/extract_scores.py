"""
Extracts judge dimension scores from every .eval log in ./logs into a single
CSV: one row per sample (run), one column per judge dimension, plus columns
identifying which arm/seed and which log file each row came from.

Usage:
    python extract_scores_csv.py
"""

import os
import csv
from inspect_ai.log import read_eval_log

LOG_DIR = "logs"
OUTPUT_CSV = "all_scores.csv"

all_rows = []
all_dimension_names = set()

for fname in sorted(os.listdir(LOG_DIR)):
    if not fname.endswith(".eval"):
        continue
    path = os.path.join(LOG_DIR, fname)

    try:
        log = read_eval_log(path)
    except Exception as e:
        print(f"SKIPPED {fname}: failed to read ({e})")
        continue

    if not log.samples:
        continue

    task_args = getattr(log.eval, "task_args", {}) or {}
    seed = task_args.get("seed_instructions", "?")

    for i, sample in enumerate(log.samples):
        if not sample.scores:
            continue

        # The judge score is stored under a single key (e.g. 'audit_judge')
        # whose .value is a dict of {dimension_name: score}.
        row = {
            "log_file": fname,
            "seed_instructions": seed,
            "epoch": i + 1,
        }

        for score_key, score_obj in sample.scores.items():
            val = getattr(score_obj, "value", None)
            if isinstance(val, dict):
                # nested dict of dimension -> score (Petri's actual structure)
                for dim_name, dim_score in val.items():
                    row[dim_name] = dim_score
                    all_dimension_names.add(dim_name)
            else:
                # fallback: flat score (in case some other scorer isn't nested)
                row[score_key] = val
                all_dimension_names.add(score_key)

        all_rows.append(row)

# Build the final column order: identifying columns first, then dimensions alphabetically
fixed_cols = ["log_file", "seed_instructions", "epoch"]
dim_cols = sorted(all_dimension_names)
fieldnames = fixed_cols + dim_cols

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in all_rows:
        writer.writerow(row)

print(f"Wrote {len(all_rows)} rows across {len(dim_cols)} dimensions to {OUTPUT_CSV}")