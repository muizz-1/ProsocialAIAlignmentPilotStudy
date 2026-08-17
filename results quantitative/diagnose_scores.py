from inspect_ai.log import read_eval_log

LOG_PATH = "logs/2026-08-16T15-30-31-00-00_audit_KWsJnSqLrovJSqQcDcTVzR.eval"  # edit this

log = read_eval_log(LOG_PATH)
print(f"n_samples: {len(log.samples)}")

sample = log.samples[0]
print(f"\nsample.scores type: {type(sample.scores)}")
print(f"sample.scores: {sample.scores}")

if sample.scores:
    for key, val in sample.scores.items():
        print(f"\n  key: {key!r}")
        print(f"  type(val): {type(val)}")
        print(f"  val: {val}")
        if hasattr(val, "value"):
            print(f"  val.value type: {type(val.value)}")
            print(f"  val.value: {val.value}")