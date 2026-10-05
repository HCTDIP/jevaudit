"""Turn a reconcile report into named findings (one code per kind of fault).

Codes
  PASS                   nothing wrong in the checked range
  EXTRA_IN_LEDGER        ledger has a fill the chain does not have
  MISSING_FROM_LEDGER    chain fill absent from the ledger; the block still has other ledger fills
  MISSING_BLOCK          every tracked chain fill of a block is absent (block + fill count)
  TRAILING_GAP           missing fills in blocks after the last ledger block, up to the expected end
                         (expected end = listener checkpoint, not the ledger's own last block)
  MISSING_DAY_PARTITION  a UTC day inside the run window has no ledger file
  INPUT_HASH_MISMATCH    matched fill whose input_hash does not match the raw chain log
  DUPLICATE_IN_LEDGER    same (tx, log_index) written more than once
  INTEGRITY_FAIL         output_hash / code_hash failure
  UNRESOLVED / NO_ANSWER nodes disagreed / did not answer -> range not proven either way
"""
import datetime as _dt
import os
import re

_DAY = re.compile(r"chain_listener_(\d{8})\.jsonl(\.gz)?$")


def check_partitions(paths, run_start_ts, run_end_ts):
    """Every UTC day touched by [run_start_ts, run_end_ts] must have a ledger file."""
    have = {m.group(1) for m in (_DAY.search(os.path.basename(p)) for p in paths) if m}
    d = _dt.datetime.fromtimestamp(run_start_ts, _dt.timezone.utc).date()
    end = _dt.datetime.fromtimestamp(run_end_ts, _dt.timezone.utc).date()
    expected = []
    while d <= end:
        expected.append(d.strftime("%Y%m%d"))
        d += _dt.timedelta(days=1)
    missing = [x for x in expected if x not in have]
    return {"expected": expected, "present": sorted(have), "missing": missing,
            "findings": [{"code": "MISSING_DAY_PARTITION", "day": x, "file": f"chain_listener_{x}.jsonl.gz"} for x in missing]}


def classify(rep, ledger_last_block, integrity=None, partitions=None):
    """rep = reconcile_with_chain() output; ledger_last_block = highest block in the WHOLE ledger."""
    f = []
    trailing = [b for b in rep["missing_blocks"] if b["block"] > ledger_last_block]
    for b in rep["missing_blocks"]:
        if b["block"] > ledger_last_block:
            continue
        if b["ledger_fills"] == 0:
            f.append({"code": "MISSING_BLOCK", "block": b["block"], "missing_fills": b["missing_fills"]})
        else:
            for m in rep["missing_fills"]:
                if m["block"] == b["block"]:
                    f.append({"code": "MISSING_FROM_LEDGER", **m})
    if trailing:
        f.append({"code": "TRAILING_GAP", "ledger_last_block": ledger_last_block, "expected_last_block": rep["range"]["to"],
                  "blocks": [b["block"] for b in trailing], "missing_fills": sum(b["missing_fills"] for b in trailing)})
    f += [{"code": "EXTRA_IN_LEDGER", **x} for x in rep["extra_fills"]]
    f += [{"code": "INPUT_HASH_MISMATCH", **x} for x in rep["input_hash_mismatch"]]
    f += [{"code": "UNRESOLVED", **x} for x in rep["unresolved_blocks"]]
    f += [{"code": "NO_ANSWER", **x} for x in rep["unanswered_chunks"]]
    if integrity:
        for x in integrity["failures"]:
            dup = "duplicate tx/log_index" in x["reasons"]
            f.append({"code": "DUPLICATE_IN_LEDGER" if dup else "INTEGRITY_FAIL", **x})
    if partitions:
        f += partitions["findings"]
    return f or [{"code": "PASS"}]
