import argparse
import json
import os
import sys
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log
from rich.console import Console
from rich.table import Table


def collect_samples(log_path):
    """Yield (log_file, sample, task_name) tuples."""
    p = Path(log_path)
    files = []
    if p.is_file():
        files = [p]
    elif p.is_dir():
        info = list_eval_logs(str(p))
        files = [i.name for i in info] if hasattr(info, "__iter__") else []
        if not files:
            files = sorted(p.rglob("*.eval"))
    else:
        files = []
    out = []
    for f in files:
        try:
            log = read_eval_log(str(f))
        except Exception as e:
            print(f"warn: could not read {f}: {e}", file=sys.stderr)
            continue
        task = getattr(log, "eval", None)
        task_name = getattr(task, "task", None) if task else None
        for s in (log.samples or []):
            out.append((str(f), s, task_name))
    return out


def extract_monitor(s):
    """Return (score, score_parsed, reason, snippet) or None."""
    best = None
    for m in getattr(s, "messages", []) or []:
        if getattr(m, "role", None) != "assistant":
            continue
        md = getattr(m, "metadata", None)
        if not isinstance(md, dict):
            continue
        if "suspicion_score" not in md:
            continue
        try:
            score = float(md["suspicion_score"])
        except (TypeError, ValueError):
            continue
        parsed = bool(md.get("score_parsed", True))
        reason = md.get("reason", "")
        # snippet: tool calls if present
        tcs = getattr(m, "tool_calls", None)
        snippet = ""
        if tcs:
            tc = tcs[0]
            snippet = f"{getattr(tc, 'function', '')}({getattr(tc, 'arguments', '')})"
        cand = (score, parsed, reason, snippet, m)
        if best is None or score > best[0]:
            best = cand
    return best


def main(argv=None):
    ap = argparse.ArgumentParser(prog="eval-triage", description="Triage Inspect .eval logs by monitor suspicion.")
    ap.add_argument("path", help="Path to a .eval file or directory")
    ap.add_argument("--top", type=int, default=20, help="Show top N samples (default 20)")
    ap.add_argument("--min-score", type=float, default=0.0, help="Minimum suspicion score to include")
    ap.add_argument("--only-unparsed", action="store_true", help="Only show samples where score_parsed=False")
    ap.add_argument("--sample-below", type=int, default=0, metavar="N", help="Randomly include N below-threshold samples (catch monitor misses)")
    ap.add_argument("--format", choices=["json", "csv", "markdown"], default="json", help="Export format for --out (default json)")
    ap.add_argument("--out", type=str, default=None, help="Write export to this file")
    args = ap.parse_args(argv)

    rows = []
    below = []
    for f, s, task in collect_samples(args.path):
        res = extract_monitor(s)
        if res is None:
            continue
        score, parsed, reason, snippet, _ = res
        sid = getattr(s, "id", None)
        entry = {
            "file": f,
            "sample_id": sid,
            "task": task,
            "score": score,
            "score_parsed": parsed,
            "snippet": snippet,
            "reason": (reason or "")[:120],
            "below_threshold": False,
        }
        if score < args.min_score:
            below.append(entry)
            continue
        if args.only_unparsed and parsed:
            continue
        rows.append(entry)

    # randomly include N below-threshold samples to catch monitor misses
    if args.sample_below and below:
        import random
        random.seed(42)
        chosen = random.sample(below, min(args.sample_below, len(below)))
        for c in chosen:
            c["below_threshold"] = True
            rows.append(c)

    rows.sort(key=lambda r: r["score"], reverse=True)
    rows = rows[: args.top]

    console = Console()
    table = Table(title=f"eval-triage: {len(rows)} samples")
    table.add_column("Score", justify="right")
    table.add_column("Parsed")
    table.add_column("Sample")
    table.add_column("Task")
    table.add_column("Snippet")
    for r in rows:
        table.add_row(
            f"{r['score']:.3f}",
            "✓" if r["score_parsed"] else "✗",
            str(r["sample_id"]) + (" *" if r.get("below_threshold") else ""),
            str(r["task"] or ""),
            r["snippet"][:60],
        )
    console.print(table)

    if args.out:
        if args.format == "json":
            Path(args.out).write_text(json.dumps(rows, indent=2, default=str))
        elif args.format == "csv":
            import csv
            with open(args.out, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["file","sample_id","task","score","score_parsed","snippet","reason"])
                w.writeheader()
                for r in rows:
                    w.writerow(r)
        elif args.format == "markdown":
            lines = ["# eval-triage report", "", f"Samples: {len(rows)}", "", "| Score | Parsed | Sample | Task | Snippet |", "|---|---|---|---|---|"]
            for r in rows:
                lines.append(f"| {r['score']:.3f} | {'✓' if r['score_parsed'] else '✗'} | {r['sample_id']} | {r['task']} | {r['snippet']} |")
            lines.append("")
            lines.append("## Details")
            for r in rows:
                lines.append(f"### {r['sample_id']} (score {r['score']:.3f})")
                lines.append(f"- Parsed: {r['score_parsed']}")
                lines.append(f"- Reason: {r['reason']}")
                lines.append("")
            Path(args.out).write_text("\n".join(lines))
        console.print(f"Wrote {len(rows)} rows to {args.out} ({args.format})")


if __name__ == "__main__":
    main()
