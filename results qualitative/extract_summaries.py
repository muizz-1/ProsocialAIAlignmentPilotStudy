"""
Extracts the judge's per-epoch summary, highlights, and explanation from a
single .eval log file, and compiles them into one readable markdown document,
organized epoch-by-epoch -- ready to paste into a chat for pattern analysis.

Also includes each epoch's key flagged scores (dimensions scoring above a
threshold) so anomalies are easy to spot without re-reading every full score
table.

Usage:
    python extract_summaries.py logs/YOUR_LOGFILE.eval

    (or edit LOG_PATH below and run with no arguments)
"""

import sys
from inspect_ai.log import read_eval_log

# LOG_PATH = "logs/2026-08-16T07-45-21-00-00_audit_j3qBvkDyKnwa4shDJJWBS2.eval"  # used if no CLI arg given
# LOG_PATH = "logs/2026-08-16T14-32-08-00-00_audit_Ra34QxrqjSe2jHZonq5j2a.eval" #procompany
LOG_PATH  = "logs/2026-08-16T15-30-31-00-00_audit_KWsJnSqLrovJSqQcDcTVzR.eval" #rival

FLAG_THRESHOLD = 3  # dimensions scoring >= this get called out per epoch

# Dimensions to always show flagged, even below threshold, since they're
# the core safety-relevant ones for this study
ALWAYS_SHOW = {
    "unprompted_blackmail",
    "unprompted_leaking",
    "unprompted_self_preservation",
    "unprompted_whistleblowing",
}


def main():
    log_path = sys.argv[1] if len(sys.argv) > 1 else LOG_PATH
    log = read_eval_log(log_path)

    out_lines = [f"# Compiled epoch summaries — {log_path}\n"]
    out_lines.append(f"Total epochs: {len(log.samples)}\n")

    for i, sample in enumerate(log.samples):
        epoch_num = i + 1
        out_lines.append(f"\n---\n## Epoch {epoch_num}\n")

        if not sample.scores:
            out_lines.append("_(no scores recorded for this epoch)_\n")
            continue

        # Petri stores everything under one score key (e.g. 'audit_judge')
        for score_key, score_obj in sample.scores.items():
            values = getattr(score_obj, "value", {}) or {}
            metadata = getattr(score_obj, "metadata", {}) or {}
            explanation = getattr(score_obj, "explanation", "") or ""

            summary = metadata.get("summary", "")
            highlights = metadata.get("highlights", "")
    

            # Flagged scores: always-show dims, plus anything >= threshold
            flagged = {}
            for dim, val in values.items():
                try:
                    val_num = float(val)
                except (TypeError, ValueError):
                    continue
                if dim in ALWAYS_SHOW or val_num >= FLAG_THRESHOLD:
                    flagged[dim] = val_num

            if flagged:
                flag_str = ", ".join(f"{k}={v:g}" for k, v in sorted(flagged.items()))
                out_lines.append(f"**Flagged scores:** {flag_str}\n")
            else:
                out_lines.append("**Flagged scores:** none above threshold\n")

            if summary:
                out_lines.append(f"**Summary:** {summary}\n")

            if highlights:
                out_lines.append(f"**Highlights:**\n{highlights}\n")

            if not summary and not highlights and explanation:
                # fallback if this log version didn't populate metadata
                out_lines.append(f"**Judge explanation:** {explanation}\n")

    out_text = "\n".join(out_lines)

    out_path = "compiled_epoch_summaries.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_text)

    print(f"Wrote {len(log.samples)} epoch summaries to {out_path}")
    print("Paste this file's contents into chat for pattern/anomaly analysis.")


if __name__ == "__main__":
    main()