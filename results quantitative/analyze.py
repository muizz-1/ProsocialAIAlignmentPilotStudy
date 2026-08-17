"""
Reads scores_control.csv, scores_procompany.csv, scores_rival.csv and prints:
  1. Per-arm summary stats (mean, std, n) for key dimensions
  2. A side-by-side comparison table across all three arms
  3. Kruskal-Wallis omnibus test per dimension (is there ANY difference
     across the three arms?)
  4. Pairwise Mann-Whitney U tests, but ONLY run/interpreted for dimensions
     where the omnibus test was significant -- standard practice, avoids
     fishing through pairwise tests without justification
  5. Benjamini-Hochberg correction applied across all pairwise p-values,
     since we're running many tests and want to control the false discovery
     rate rather than trusting raw p<0.05 on each one individually

Requires: pandas, scipy, statsmodels
    pip install pandas scipy statsmodels --break-system-packages

Usage:
    python analyze_arms.py
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ARM_FILES = {
    "Control":    "scores_control.csv",
    "Procompany": "scores_procompany.csv",
    "Rival":      "scores_rival.csv",
}

KEY_DIMENSIONS = ["admirable", "audit_situational_awareness", "auditor_failure", "broken_tool_use", "concerning", "concerning_with_no_mitigating_factors", "cooperation_with_harmful_sysprompt", "cooperation_with_human_misuse", "counterfactual_bad_behavior", "disappointing", "eval_awareness", "facilitating_terrorism", "fun_or_funny", "high_stakes_setting", "input_hallucination", "manipulated_by_developer", "needs_attention", "overrefusal", "prefill_susceptibility", "scenario_realism", "stuck_in_loops", "unfaithful_thinking", "unprompted_bizarre_behavior", "unprompted_blackmail", "unprompted_deception_toward_user", "unprompted_emotional_manipulativeness", "unprompted_encouragement_of_user_delusion", "unprompted_gratitude", "unprompted_initiative", "unprompted_leaking", "unprompted_neg_affect", "unprompted_pos_affect", "unprompted_self_preservation", "unprompted_self_serving_bias", "unprompted_spirituality_or_extreme_awe", "unprompted_sycophancy", "unprompted_whistleblowing", "user_over_sysprompt", "prosocial_escalation"]


arms = {}
for name, path in ARM_FILES.items():
    try:
        df = pd.read_csv(path)
        arms[name] = df
        print(f"Loaded {name}: {len(df)} rows from {path}")
    except FileNotFoundError:
        print(f"WARNING: {path} not found, skipping {name}")

if len(arms) < 2:
    raise SystemExit("Need at least 2 arm files loaded to compare anything.")

# ---- 1. Per-arm summary stats, as a proper table ----
print("\n" + "=" * 80)
print("PER-ARM SUMMARY (mean, std, n) per dimension")
print("=" * 80)

summary_rows = []
for dim in KEY_DIMENSIONS:
    row = {"dimension": dim}
    for name, df in arms.items():
        if dim not in df.columns:
            row[f"{name}_mean"] = None
            row[f"{name}_std"] = None
            row[f"{name}_n"] = None
            continue
        vals = df[dim].dropna()
        row[f"{name}_mean"] = round(vals.mean(), 2)
        row[f"{name}_std"] = round(vals.std(), 2)
        row[f"{name}_n"] = len(vals)
    summary_rows.append(row)

stats_table = pd.DataFrame(summary_rows).set_index("dimension")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
print(stats_table.to_string())
stats_table.to_csv("summary_stats_table.csv")
print("\nSaved summary_stats_table.csv")

# ---- 2. Comparison table ----
print("\n" + "=" * 80)
print("COMPARISON TABLE (mean per arm per dimension)")
print("=" * 80)

summary_rows = []
for name, df in arms.items():
    row = {"arm": name}
    for dim in KEY_DIMENSIONS:
        row[dim] = df[dim].mean() if dim in df.columns else None
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows).set_index("arm")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)
print(summary_df.round(2))
summary_df.to_csv("comparison_summary.csv")
print("\nSaved comparison table to comparison_summary.csv")

# ---- 3. Kruskal-Wallis omnibus test, as a table ----
print("\n" + "=" * 80)
print("KRUSKAL-WALLIS OMNIBUS TEST (is there ANY difference across arms?)")
print("=" * 80)

arm_names = list(arms.keys())
omnibus_results = {}
omnibus_rows = []

for dim in KEY_DIMENSIONS:
    groups = []
    valid = True
    for name in arm_names:
        df = arms[name]
        if dim not in df.columns:
            valid = False
            break
        vals = df[dim].dropna()
        if len(vals) < 2:
            valid = False
            break
        groups.append(vals)
    if not valid or len(groups) < 2:
        omnibus_rows.append({"dimension": dim, "H": None, "p_value": None,
                              "note": "skipped (missing data)"})
        continue

    try:
        h_stat, p_val = stats.kruskal(*groups)
    except ValueError:
        omnibus_rows.append({"dimension": dim, "H": None, "p_value": None,
                              "note": "no variance (all values identical)"})
        continue

    omnibus_results[dim] = p_val
    omnibus_rows.append({
        "dimension": dim,
        "H": round(h_stat, 2),
        "p_value": round(p_val, 4),
        "note": "significant" if p_val < 0.05 else "",
    })

omnibus_table = pd.DataFrame(omnibus_rows).set_index("dimension")
print(omnibus_table.to_string())
omnibus_table.to_csv("omnibus_table.csv")
print("\nSaved omnibus_table.csv")

# ---- 4. Pairwise Mann-Whitney, only for dimensions with significant omnibus ----
print("\n" + "=" * 80)
print("PAIRWISE MANN-WHITNEY U (only for dimensions with significant Kruskal-Wallis)")
print("=" * 80)

sig_dims = [d for d, p in omnibus_results.items() if p < 0.05]

if not sig_dims:
    print("No dimensions showed a significant omnibus difference across arms.")
    print("Not running pairwise tests -- would just be fishing without justification.")
else:
    pairwise_rows = []
    for dim in sig_dims:
        for i in range(len(arm_names)):
            for j in range(i + 1, len(arm_names)):
                a_name, b_name = arm_names[i], arm_names[j]
                a_vals = arms[a_name][dim].dropna()
                b_vals = arms[b_name][dim].dropna()
                if len(a_vals) < 2 or len(b_vals) < 2:
                    continue
                u_stat, p_val = stats.mannwhitneyu(a_vals, b_vals, alternative="two-sided")
                pairwise_rows.append({
                    "dimension": dim, "arm_a": a_name, "arm_b": b_name,
                    "mean_a": a_vals.mean(), "mean_b": b_vals.mean(),
                    "n_a": len(a_vals), "n_b": len(b_vals),
                    "u_stat": u_stat, "p_raw": p_val,
                })

    pairwise_df = pd.DataFrame(pairwise_rows)

    # ---- 5. Benjamini-Hochberg correction across all pairwise p-values ----
    if len(pairwise_df) > 0:
        reject, p_adj, _, _ = multipletests(pairwise_df["p_raw"], method="fdr_bh")
        pairwise_df["p_adj_bh"] = p_adj
        pairwise_df["significant_after_correction"] = reject

        pairwise_display = pairwise_df.round(4).set_index(["dimension", "arm_a", "arm_b"])
        print(pairwise_display.to_string())
        pairwise_df.to_csv("significance_tests.csv", index=False)
        print("\nSaved corrected pairwise results to significance_tests.csv")
        print(f"\n{reject.sum()} of {len(reject)} pairwise comparisons remain "
              f"significant after Benjamini-Hochberg correction.")

print("\n" + "=" * 80)
print("NOTE: Kruskal-Wallis gating avoids fishing through pairwise tests when")
print("there's no overall difference. Benjamini-Hochberg controls the false")
print("discovery rate across all pairwise tests run. With n=20/arm, only")
print("moderate-to-large effects will survive both filters -- a null result")
print("here means 'not enough power to detect a difference', not 'no effect'.")
print("=" * 80)