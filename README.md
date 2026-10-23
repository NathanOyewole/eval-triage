# eval-triage

Triage Inspect AI `.eval` logs by monitor suspicion score.

Researchers running ControlArena / Inspect evals dig through `.eval` logs by hand to find which samples a monitor flagged. `eval-triage` makes that one command.

## Usage

```bash
eval-triage logs/                       # triage a directory
eval-triage run.eval --top 20            # single file
eval-triage logs/ --min-score 0.7       # only high-suspicion
eval-triage logs/ --only-unparsed       # monitor failures only
eval-triage logs/ --out report.json     # JSON export
```

## Output

Ranked table: score, parsed flag, sample id, task, tool-call snippet. Optional JSON export for further analysis.

## Status

v0. Works on synthetic and real Inspect `.eval` logs. Markdown report + CSV coming in v1.

## License

MIT
EOF
echo done