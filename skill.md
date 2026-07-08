---
description: End-to-end master's program admission evaluation — reads applicant documents, scores candidates against a configurable rubric, and generates an HTML review dashboard with scored CSV output.
---

# eval-admission

A reusable skill for evaluating master's program applicants. Reads CVs, transcripts, recommendation letters, and publications; scores each candidate; and produces a sortable HTML dashboard plus a scored CSV ready to paste into the official evaluation spreadsheet.

---

## How to invoke

```
/eval-admission                          # uses eval-admission.config.json in cwd
/eval-admission path/to/custom.json      # uses a specific config file
```

---

## Prerequisites

Before running, ensure:
1. **`eval-admission.config.json`** exists in the project root (see `config.example.json`)
2. **`_students.json`** exists in the output directory (or set `paths.auto_discover: true` to build it)
3. **Document files** are accessible at the paths listed in `_students.json`

---

## Steps Claude follows when invoked

### Step 1 — Load configuration

Read `eval-admission.config.json` (or the path provided as argument). Extract:
- `program.name`, `program.year`, `program.committee`
- `paths.csv` — the pre-filled evaluation CSV
- `paths.output_dir` — where to write dashboard HTML
- `paths.students_json` — JSON file mapping student IDs to document paths
- `scoring` — formula weights (degree, courses, pubs, refs, thesis, master, experience, bonus)
- `relevance` — labels and multipliers for degree_relevance 0/1/2

### Step 2 — Load student file mappings

Read `paths.students_json`. It must be an array of objects with:
```json
{
  "id": "<file_id>",
  "app_id": "<application_number>",
  "surname": "...",
  "name": "...",
  "degree_uni": "...", "degree_dept": "...", "degree_grade": "...",
  "thesis_title": "...", "thesis_grade": "...",
  "courses": "course1 (grade)\ncourse2 (grade)\n...",
  "course_avg_prefilled": "...",
  "master_uni": "...", "master_dept": "...", "master_title": "...", "master_grade": "...",
  "ref1_name": "...", "ref1_inst": "...",
  "ref2_name": "...", "ref2_inst": "...",
  "exp_years": "...", "exp_org1": "...", "exp_org2": "...", "exp_org3": "...",
  "pubs_count": "...", "pub1_title": "...",
  "distinctions": "...", "secretariat_notes": "...",
  "english_level": "...", "other_language": "...",
  "cv_path": "/absolute/path/to/CV.pdf",
  "letter_paths": ["/path/to/letter1.pdf"],
  "paper_paths": ["/path/to/paper1.pdf"]
}
```

### Step 3 — Run the evaluation workflow

Call the Workflow tool with `workflow.js` (from this repo) and pass the students array as `args`.

The workflow spawns one evaluation agent per student. Each agent reads the student's documents and returns structured JSON scores. All agents run in parallel.

### Step 4 — Post-process results

After the workflow returns:
1. Remap IDs if the workflow used temporary IDs (check `paths.id_mappings`)
2. Apply any manual overrides from `config.manual_overrides`
3. Save results to `{output_dir}/_results.json`

### Step 5 — Generate the dashboard

```bash
python3 {output_dir}/../generate.py {output_dir}/_results.json
```

Or if generate.py was copied into the output dir:
```bash
python3 {output_dir}/_generate.py {output_dir}/_results.json
```

This produces:
- `{output_dir}/index.html` — sortable dashboard
- `{output_dir}/profiles/{id}.html` — per-student detail pages
- `{paths.scored_csv}` — CSV with all scoring fields filled

---

## Evaluation agent prompt template

Use the following prompt for each student agent. Replace `${...}` with actual student data.

```
You are evaluating a master's program applicant for ${PROGRAM_NAME} (${YEAR}).

## Applicant Data (pre-filled by secretariat — do not modify these facts)

Name: ${SURNAME} ${FIRST_NAME}
App ID: ${APP_ID}
Undergraduate degree: ${DEGREE_DEPT} at ${DEGREE_UNI} (grade: ${DEGREE_GRADE}/10)
Undergraduate thesis: "${THESIS_TITLE}" (grade: ${THESIS_GRADE}/10)
Relevant courses pre-selected by secretariat:
${COURSES_LIST || "(none listed)"}
Pre-filled course average: ${COURSE_AVG_PREFILLED || "not pre-filled"}
Master's: ${MASTER_TITLE || "none"} at ${MASTER_UNI || ""}
Ref 1: ${REF1_NAME || "none"}, ${REF1_INST || ""}
Ref 2: ${REF2_NAME || "none"}, ${REF2_INST || ""}
Experience: ${EXP_YEARS || "not stated"} years; orgs: ${EXP_ORGS || "none stated"}
Publications: ${PUBS_COUNT || "none"} ${PUB1_TITLE ? "— " + PUB1_TITLE : ""}
Distinctions / extra info: ${DISTINCTIONS || "none"}
Secretariat notes: ${SECRETARIAT_NOTES || "none"}

## Documents to Read

CV: ${CV_PATH}
${LETTER_LIST}
${PAPER_LIST}

Read all documents above, then produce a structured evaluation JSON.

---

## Scoring Rubric

### 1. degree_relevance — 0 / 1 / 2

Based on the UNDERGRADUATE degree department ONLY (not what courses they took).

**Score 1 — Directly CS/ICT related (×1.0 multiplier):**
Computer Science (Πληροφορική), Informatics (Πληροφορική & Τηλεπικοινωνίες),
Computer Engineering, Electrical Engineering (Ηλεκτρολόγοι Μηχανικοί / ΗΜΜΥ),
Electronics, Telecommunications, Software Engineering, Digital Systems (Ψηφιακά Συστήματα).
Any department where programming, algorithms, and computing form the CORE curriculum (>50%).
A degree from an institution not recognized by ΔΟΑΤΑΠ still counts as rel=1 if the subject is CS/CE — but must be flagged.

**Score 2 — Adjacent STEM / Engineering (×0.6 multiplier):**
Mathematics (Μαθηματικά), Physics (Φυσική), Statistics (Στατιστική),
ALL Engineering disciplines: Mechanical, Civil, Chemical,
Industrial Engineering / Industrial Management and Technology (Βιομηχανική Διοίκηση και Τεχνολογία),
Surveying & Geoinformatics Engineering (Αγρονόμων & Τοπογράφων Μηχανικών / Μηχανικών Γεωπληροφορικής),
Environmental Engineering, Biomedical Engineering, Applied Mathematics, Computational Science.
Fields with a strong STEM foundation where computing is used but not the primary focus.

**Score 0 — Unrelated (×0.1 multiplier):**
Economics, Business Administration, Accounting, Finance, Management,
Law, Political Science, Public Administration,
Humanities (Φιλολογία, Ιστορία, Φιλοσοφία),
Social Sciences (Κοινωνιολογία, Ψυχολογία), Medicine, Nursing,
Agriculture (non-geoinformatics), Pedagogy, Education.
Score 0 even if the student took CS electives — it's the DEPARTMENT that determines the score.

**Rule:** When in doubt between 0 and 1, choose 0. When in doubt between 1 and 2, choose 2.

### 2. thesis_coeff — 0 / 3 / 8 / 15

Based on the undergraduate thesis:
- **0**: No thesis submitted, or thesis explicitly not completed ("Δεν εκπονήθηκε")
- **3**: Thesis exists but is not ICT-related, OR is ICT-related but grade < 7.0/10
- **8**: ICT-related thesis with grade 7.0–8.49/10
- **15**: ICT-related thesis with grade ≥ 8.5/10

ICT-related = involves computing, software, networks, data analysis, machine learning, signal processing, or similar technical ICT topics.

### 3. course_avg and n_relevant_courses

- **course_avg**: Use the pre-filled value (`course_avg_prefilled`) if available. If no courses are listed, use 0.
- **n_relevant_courses**: Count the number of courses in the pre-filled course list. If none listed, use 0.

The secretariat has already selected the relevant courses. Do not add or remove courses from the list.

### 4. master_coeff — 0 / 2 / 6 / 10

Based on a COMPLETED master's degree:
- **0**: No master's degree (or currently enrolled — not yet completed)
- **2**: Master's in an unrelated field (law, education without tech, business, public administration)
- **6**: Partially related (techno-economics, educational technology, biomedical informatics, industrial management with IT focus)
- **10**: Directly ICT-related (CS, EE, Networks, Data Science, Cybersecurity, ML/AI)

### 5. ref1_pts and ref2_pts — 0 / 3 / 6 / 10

Score each recommendation letter independently:
- **0**: No letter submitted
- **3**: Generic letter with minimal specifics, OR from a completely unrelated department
- **6**: Good letter with some specifics about the applicant; OR from a relevant but non-CS/EE department; OR a technical but very generic letter
- **10**: Strong, specific letter from a CS/EE/ICT department or senior technical professional, explicitly addressing the applicant's research ability or technical capabilities with concrete examples

**Special rule**: Graduates of the evaluating institution's own department typically receive 10 for ref1_pts even without a letter. Check the config or secretariat notes for this.

### 6. experience_score — 0 to 10

Count only RELEVANT professional experience (software development, IT, data engineering, networks, technical roles):

| Relevant years | Score |
|---|---|
| 0 | 0 |
| < 0.5 | 1 |
| 0.5–1.5 | 3 |
| 1.5–3 | 5 |
| 3–5 | 7 |
| 5–7 | 8 |
| > 7 | 10 |

- Administrative/management roles in IT companies: count at 50% of their duration
- Teaching/tutoring: does NOT count as relevant experience
- Short internships and part-time work: count proportionally

### 7. relevant_pubs — integer ≥ 0

Count peer-reviewed publications on ICT topics (journal articles, conference papers with proceedings).
- Count only if an actual PDF or full citation with DOI is provided
- Preprints, reports, theses, class projects: do NOT count
- Preprints submitted to peer review but not yet accepted: count as 0

### 8. bonus — 0 to 10, and bonus_reasons

Award bonus points for achievements beyond standard qualifications:
- Academic scholarships, excellence awards, distinctions: 1–3 pts
- Competitive program admission or fellowship: 2–4 pts
- International exchange (Erasmus+, etc.): 1–2 pts
- Relevant technical certifications (AWS, Azure, professional programming certs): 1–2 pts per notable cert

Leave **bonus=0** and **bonus_reasons=""** if there is nothing notable beyond standard qualifications.
Do not award bonus for things already captured in other fields.

---

## CV Quality Assessment

After reading the CV:

**cv_quality**: one of "high" / "medium" / "low"
- **high**: Professional layout, specific verifiable claims (dates, company names, project descriptions), no unexplained gaps, fully consistent with application form and supporting documents
- **medium**: Mostly professional but with minor vagueness, incomplete dates, or small inconsistencies
- **low**: Vague/unverifiable claims, significant inconsistencies with other documents, apparent exaggeration of qualifications, missing key information

**cv_notes**: 1–2 sentences on the overall quality and any notable CV-specific observations.

---

## Flags — IMPORTANT

Return **`[]` (empty array)** for the vast majority of applicants. Flags are NOT scores or comments — they are alerts for situations that require special human attention OUTSIDE the scoring rubric.

Add a flag string only for:
- **Foreign degree recognition**: "Degree from [institution] — ΔΟΑΤΑΠ recognition uncertain per secretariat notes" (still score the degree normally for relevance if the subject is CS/CE)
- **Document inconsistency**: "CV claims [X] but no supporting document provided to verify"
- **Timeline problem**: "CV shows concurrent positions at [A] and [B] with overlapping dates [period]"
- **Missing critical document**: "Secretariat flagged [document] as missing"

**DO NOT flag:**
- Reference letters from thesis supervisors or academic advisors — these are VALUED more highly, not a problem. An advisor who supervised the student's thesis can provide the most informed assessment. Score such letters higher (up to 10) if they are specific and substantive.
- Low scores (that's what the scoring fields are for)
- No recommendation letters (ref1_pts=0 already captures this)
- Non-ICT background (degree_relevance=0 already captures this)
- "No publications" or "no master's" — normal, captured by the score
- Any observation already captured by a numeric field
- The quality of a recommendation letter (captured by ref points)
- Normal things like "Greek university, no ΔΟΑΤΑΠ needed"

---

## Justification (with document references)

For each scoring dimension, write 2–4 sentences that:
1. State the score and the main reason
2. Reference the specific document and content: e.g., "CV (pages 1–2) shows employment as Software Engineer at Company X from Jan 2021–Mar 2024", "Reference letter from Prof. Y (CS Dept, University Z) explicitly states 'among the top 3% of students I have supervised in 20 years'"
3. Note any ambiguity or assumption made

---

## Overall Evaluator Comment

Write 3–5 sentences summarizing:
- The applicant's strongest and weakest dimensions
- How the profile fits the master's program
- Your overall recommendation: **strong candidate** / **borderline** / **weak — unlikely to succeed without significant background work**

---

## Output

Return ONLY valid JSON (no explanation, no markdown fences):

{
  "id": "<provided>",
  "app_id": "<provided>",
  "degree_relevance": <0|1|2>,
  "thesis_coeff": <0|3|8|15>,
  "course_avg": <number — use pre-filled value or 0>,
  "n_relevant_courses": <integer>,
  "master_coeff": <0|2|6|10>,
  "ref1_pts": <0|3|6|10>,
  "ref2_pts": <0|3|6|10>,
  "experience_score": <0..10>,
  "relevant_pubs": <integer ≥ 0>,
  "bonus": <0..10>,
  "bonus_reasons": "<string or empty>",
  "cv_quality": "<high|medium|low>",
  "cv_notes": "<1–2 sentences>",
  "evaluator_comment": "<3–5 sentences>",
  "flags": [],
  "justification": {
    "degree": "<with document ref>",
    "thesis": "<with document ref>",
    "courses": "<explain course_avg and n_relevant_courses>",
    "master": "<with document ref>",
    "refs": "<with document ref for each letter>",
    "experience": "<with document ref>",
    "publications": "<with document ref>"
  }
}
```

---

## JSON Schema (for Workflow structured output)

```javascript
const EVAL_SCHEMA = {
  type: 'object',
  properties: {
    id:                 { type: 'string' },
    app_id:             { type: 'string' },
    degree_relevance:   { type: 'integer', enum: [0, 1, 2] },
    thesis_coeff:       { type: 'integer', enum: [0, 3, 8, 15] },
    course_avg:         { type: 'number' },
    n_relevant_courses: { type: 'integer' },
    master_coeff:       { type: 'integer', enum: [0, 2, 6, 10] },
    ref1_pts:           { type: 'integer', enum: [0, 3, 6, 10] },
    ref2_pts:           { type: 'integer', enum: [0, 3, 6, 10] },
    experience_score:   { type: 'integer', minimum: 0, maximum: 10 },
    relevant_pubs:      { type: 'integer', minimum: 0 },
    bonus:              { type: 'integer', minimum: 0, maximum: 10 },
    bonus_reasons:      { type: 'string' },
    cv_quality:         { type: 'string', enum: ['high', 'medium', 'low'] },
    cv_notes:           { type: 'string' },
    evaluator_comment:  { type: 'string' },
    flags:              { type: 'array', items: { type: 'string' } },
    justification: {
      type: 'object',
      properties: {
        degree:       { type: 'string' },
        thesis:       { type: 'string' },
        courses:      { type: 'string' },
        master:       { type: 'string' },
        refs:         { type: 'string' },
        experience:   { type: 'string' },
        publications: { type: 'string' }
      },
      required: ['degree','thesis','courses','master','refs','experience','publications']
    }
  },
  required: [
    'id','app_id','degree_relevance','thesis_coeff','course_avg','n_relevant_courses',
    'master_coeff','ref1_pts','ref2_pts','experience_score','relevant_pubs',
    'bonus','bonus_reasons','cv_quality','cv_notes','evaluator_comment','flags','justification'
  ],
  additionalProperties: false
}
```

---

## Scoring formula

```
Total = 35 × (degree_grade/10) × rel_mult
      + 30 × (course_avg/10) × (min(n_relevant_courses, 6) / 6)
      + 10 × (min(relevant_pubs, 3) / 3)
      +  8 × ((ref1_pts + ref2_pts) / 2 / 10)
      +  6 × (thesis_grade/10) × (thesis_coeff / 15)
      +  4 × (master_coeff / 10)
      +  4 × (experience_score / 10)
      +  3 × (bonus / 10)

rel_mult: degree_relevance=0 → 0.1 | degree_relevance=1 → 1.0 | degree_relevance=2 → 0.6
```

Formula weights come from `scoring` in the config file.

---

## Token efficiency tips

- One agent per student is the right granularity — parallelism is efficient, and each document is read once
- If a student has no paper files, skip that section of the prompt entirely
- For students with no letter files, the agent can immediately score ref1_pts=0, ref2_pts=0
- Use `effort: 'medium'` for most agents; `effort: 'high'` only if the student has publications
- The secretariat has pre-filled course_avg — trust it and don't re-compute unless you see a clear error
