# admission-evaluator

A Claude Code skill for end-to-end master's program admission evaluation.

## What it does

1. Reads applicant CVs, transcripts, recommendation letters, and publications in parallel (one agent per candidate)
2. Scores each candidate against a configurable rubric
3. Generates a sortable HTML dashboard (index + per-candidate profiles)
4. Outputs a scored CSV ready to paste into the official evaluation spreadsheet

## Installation

Copy the skill into your project's `.claude/skills/` directory:

```bash
cp skill.md /path/to/project/.claude/skills/eval-admission.md
```

Then invoke with:
```
/eval-admission
```

## Configuration

Copy `config.example.json` to your project root as `eval-admission.config.json` and edit:

```json
{
  "program": { "name": "...", "year": 2026, "committee": "..." },
  "paths": {
    "csv": "basic.csv",
    "output_dir": "dashboard",
    "students_json": "dashboard/_students.json"
  },
  "scoring": { ... },
  "relevance": { ... },
  "manual_overrides": { ... }
}
```

## Preparing student data (`_students.json`)

Build the students JSON file by reading the evaluation CSV and mapping each student to their document files. See the `skill.md` for the expected field structure.

## Workflow script

`workflow.js` is the parallel evaluation agent script. Pass student data as `args.students`:

```javascript
Workflow({ script: workflowScript, args: { students: STUDENTS, program_name: '...', program_year: '2026' } })
```

## Dashboard generator

Run after the workflow to produce HTML and scored CSV:

```bash
python3 generate.py dashboard/_results.json
```

Output:
- `dashboard/index.html` — sortable/filterable candidate table
- `dashboard/profiles/{id}.html` — per-candidate detail pages
- `basic_scored.csv` — CSV with all scoring fields filled

## Scoring formula

```
Total = 35×(grade/10)×rel_mult + 30×(course_avg/10)×(min(N,6)/6)
      + 10×(min(pubs,3)/3) + 8×((ref1+ref2)/2/10) + 6×(thesis_grade/10)×(thesis_coeff/15)
      + 4×(master_coeff/10) + 4×(exp/10) + 3×(bonus/10)

rel_mult: 0→0.1 | 1→1.0 | 2→0.6
```

## Iterating

After reviewing the dashboard, you can:
1. Edit `_results.json` to fix individual scores
2. Re-run `python3 generate.py dashboard/_results.json` to regenerate HTML
3. Or re-run `/eval-admission` for a full re-evaluation with an updated rubric

## License

MIT
