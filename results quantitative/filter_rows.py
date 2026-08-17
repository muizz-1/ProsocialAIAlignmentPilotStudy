"""
Filters all_scores.csv down to rows from the three real arm seeds:
    ./my_seed_control_v2
    ./my_seed_procompany_v2
    ./my_seed_rival_v2

Writes:
    filtered_scores.csv        -- all three arms combined
    scores_control.csv         -- control arm only
    scores_procompany.csv      -- procompany (affiliated) arm only
    scores_rival.csv           -- rival arm only

Usage:
    python filter_arms.py
"""

import pandas as pd

INPUT_CSV = "all_scores.csv"

TARGET_SEEDS = [
    "./my_seed_control_v2",
    "./my_seed_procompany_v2",
    "./my_seed_rival_v2",
]

df = pd.read_csv(INPUT_CSV)

print("Unique seed_instructions values found in the file:")
print(df["seed_instructions"].unique())

filtered = df[df["seed_instructions"].isin(TARGET_SEEDS)].copy()

print(f"\nTotal rows before filtering: {len(df)}")
print(f"Total rows after filtering:  {len(filtered)}")
print("\nRow counts per arm:")
print(filtered["seed_instructions"].value_counts())

filtered.to_csv("filtered_scores.csv", index=False)

arm_filename_map = {
    "./my_seed_control_v2": "scores_control.csv",
    "./my_seed_procompany_v2": "scores_procompany.csv",
    "./my_seed_rival_v2": "scores_rival.csv",
}

for seed, out_name in arm_filename_map.items():
    subset = filtered[filtered["seed_instructions"] == seed]
    subset.to_csv(out_name, index=False)
    print(f"Wrote {len(subset)} rows to {out_name}")

print("\nAlso wrote all three combined to filtered_scores.csv")