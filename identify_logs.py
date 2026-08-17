"""
Lists every .eval log in ./logs with its seed_instructions, sample count,
and duration -- so you can identify which files are your full 20-epoch
batches vs. short validation runs, without guessing from filenames/timestamps.

Usage:
    python identify_logs.py
"""

import os
from datetime import datetime
from inspect_ai.log import read_eval_log


def parse_ts(ts):
    """Parse an ISO timestamp string, return None if missing/unparseable."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None

LOG_DIR = "logs"

rows = []
for fname in sorted(os.listdir(LOG_DIR)):
    if not fname.endswith(".eval"):
        continue
    path = os.path.join(LOG_DIR, fname)
    try:
        log = read_eval_log(path)
    except Exception as e:
        print(f"{fname}: FAILED TO READ ({e})")
        continue

    # seed_instructions is usually in the task args
    task_args = getattr(log.eval, "task_args", {}) or {}
    seed = task_args.get("seed_instructions", "?")

    n_samples = len(log.samples) if log.samples else 0

    # duration, if available
    stats = getattr(log, "stats", None)
    duration = None
    if stats:
        started = parse_ts(getattr(stats, "started_at", None))
        completed = parse_ts(getattr(stats, "completed_at", None))
        if started and completed:
            duration = completed - started

    rows.append((fname, seed, n_samples, duration))

print(f"{'filename':60s} {'seed_instructions':30s} {'n_samples':10s} {'duration'}")
print("-" * 120)
for fname, seed, n, dur in rows:
    print(f"{fname:60s} {str(seed):30s} {n:<10d} {dur}")