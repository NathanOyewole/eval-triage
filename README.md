# eval-triage

Triage Inspect AI `.eval` logs by monitor suspicion score.

Researchers running ControlArena / Inspect evals dig through `.eval` logs by hand to find which samples a monitor flagged. `eval-triage` makes that one command.

## Usage

```bash
eval-triage logs/                       # triage a directory
eval-triage run.eval --top 20            # single file
eval-triage logs/ --min-score 0.7       # only high-suspicion
eval-triage logs/ --only-unparsed       # monitor failures only
eval-triage logs/ --format markdown --out report.md
eval-triage logs/ --format csv --out triage.csv
```

## Output

Ranked table: score, parsed flag, sample id, task, tool-call snippet. Optional JSON/CSV/markdown export for further analysis.

## Demo

```
$ eval-triage logs/ --top 4
eval-triage: 4 samples
┏━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┓
┃ Score ┃ Parsed ┃ Sample ┃ Task      ┃ Snippet ┃
┡━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━┩
│ 0.900 │ ✓      │ s0     │ test_task │         │
│ 0.850 │ ✓      │ s3     │ test_task │         │
│ 0.200 │ ✓      │ s1     │ test_task │         │
│ 0.000 │ ✗      │ s2     │ test_task │         │
└───────┴────────┴────────┴───────────┴─────────┘
```

## Status

v1. Ranking table + JSON/CSV/markdown export. Works on synthetic and real Inspect `.eval` logs. Side-by-side run comparison (v2) pending.

## License

MIT
EOF