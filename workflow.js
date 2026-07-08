// Generic admission evaluation workflow.
// Pass an array of student objects as `args`.
// See skill.md for the expected student object shape.

export const meta = {
  name: 'eval-admission-workflow',
  description: 'Evaluate master program applicants — one agent per student, parallel execution',
  phases: [
    { title: 'Evaluate', detail: 'Read all applicant documents and produce structured scores' },
  ],
}

// --- Configuration ---
// Adjust these for your program.
const PROGRAM_NAME = args.program_name || 'ΠΜΣ ΤΠΕ'
const PROGRAM_YEAR = args.program_year || '2026'
const STUDENTS = args.students  // array of student objects (required)

if (!STUDENTS || !STUDENTS.length) {
  throw new Error('No students provided in args.students')
}

// --- JSON Schema for structured output ---
const SCHEMA = {
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
      required: ['degree', 'thesis', 'courses', 'master', 'refs', 'experience', 'publications']
    }
  },
  required: [
    'id', 'app_id', 'degree_relevance', 'thesis_coeff', 'course_avg', 'n_relevant_courses',
    'master_coeff', 'ref1_pts', 'ref2_pts', 'experience_score', 'relevant_pubs',
    'bonus', 'bonus_reasons', 'cv_quality', 'cv_notes', 'evaluator_comment',
    'flags', 'justification'
  ],
  additionalProperties: false
}

// --- Evaluation ---
phase('Evaluate')

const results = await parallel(STUDENTS.map(s => async () => {
  const letterSection = s.letter_paths && s.letter_paths.length > 0
    ? 'Recommendation letter files:\n' + s.letter_paths.map((p, i) => `  ${i + 1}. ${p}`).join('\n')
    : 'No recommendation letters (score ref1_pts=0, ref2_pts=0).'

  const paperSection = s.paper_paths && s.paper_paths.length > 0
    ? 'Publication files:\n' + s.paper_paths.map((p, i) => `  ${i + 1}. ${p}`).join('\n')
    : ''

  const expOrgs = [s.exp_org1, s.exp_org2, s.exp_org3].filter(Boolean).join(', ')

  const prompt = `You are evaluating a master's program applicant for ${PROGRAM_NAME} (${PROGRAM_YEAR}).

## Applicant Data (pre-filled by secretariat — do not modify these facts)

Name: ${s.surname} ${s.name}
App ID: ${s.app_id} | File ID: ${s.id}
Undergraduate degree: ${s.degree_dept} at ${s.degree_uni} (grade: ${s.degree_grade}/10)
Undergraduate thesis: "${s.thesis_title || 'Δεν εκπονήθηκε'}" (grade: ${s.thesis_grade || '0'}/10)
Relevant courses (pre-selected by secretariat):
${s.courses || '(none listed)'}
Pre-filled course average: ${s.course_avg_prefilled || '(not pre-filled — use 0 if no courses)'}
Master's degree: ${s.master_title || 'none'} at ${s.master_uni || ''} (grade: ${s.master_grade || ''})
Ref 1: ${s.ref1_name || '(none)'}, ${s.ref1_inst || ''}
Ref 2: ${s.ref2_name || '(none)'}, ${s.ref2_inst || ''}
Experience: ${s.exp_years || 'not stated'} years; orgs: ${expOrgs || 'none'}
Publications: ${s.pubs_count || 'none'} ${s.pub1_title ? '— "' + s.pub1_title + '"' : ''}
Distinctions / extra info: ${s.distinctions || 'none'}
Secretariat notes: ${s.secretariat_notes || 'none'}
English level: ${s.english_level || 'not stated'}

## Documents to Read

CV: ${s.cv_path}
${letterSection}
${paperSection}

---

## Scoring Rubric

### 1. degree_relevance — 0 / 1 / 2

Based on the UNDERGRADUATE degree DEPARTMENT only (not individual courses taken).

**Score 1 — Directly CS/ICT related (×1.0 multiplier):**
Computer Science (Πληροφορική), Informatics, Computer Engineering,
Electrical Engineering (Ηλεκτρολόγοι Μηχανικοί / ΗΜΜΥ), Electronics, Telecommunications,
Software Engineering, Digital Systems (Ψηφιακά Συστήματα).
Any department where programming, algorithms, and computing form the CORE curriculum (>50%).
A degree from an institution not recognized by ΔΟΑΤΑΠ still counts as rel=1 if the subject is CS/CE — but must be flagged.

**Score 2 — Adjacent STEM / Engineering (×0.6 multiplier):**
Mathematics (Μαθηματικά), Physics (Φυσική), Statistics,
ALL Engineering disciplines: Mechanical, Civil, Chemical,
Industrial Engineering / Industrial Management and Technology (Βιομηχανική Διοίκηση και Τεχνολογία),
Surveying & Geoinformatics Engineering (Αγρονόμων & Τοπογράφων Μηχανικών / Μηχανικών Γεωπληροφορικής),
Environmental Engineering, Biomedical Engineering, Applied Mathematics, Computational Science.
Fields with a strong STEM foundation where computing is used but not the primary focus.

**Score 0 — Unrelated (×0.1 multiplier):**
Economics, Business, Accounting, Finance, Management, Law, Political Science,
Public Administration, Humanities (Φιλολογία, Ιστορία, Φιλοσοφία),
Social Sciences, Medicine, Agriculture (without geoinformatics), Pedagogy.
Score 0 even if the student took computing electives — the DEPARTMENT determines the score.

**Rule:** When in doubt between 0 and 1, choose 0. When in doubt between 1 and 2, choose 2.

### 2. thesis_coeff — 0 / 3 / 8 / 15

- **0**: No thesis ("Δεν εκπονήθηκε") or thesis under completion
- **3**: Thesis not ICT-related, OR ICT-related but grade < 7.0
- **8**: ICT-related thesis, grade 7.0–8.49
- **15**: ICT-related thesis, grade ≥ 8.5

ICT-related = involves computing, software, networks, data analysis, ML, signal processing, etc.

### 3. course_avg and n_relevant_courses

- **course_avg**: Use the pre-filled value shown above. If no courses listed, use 0.
- **n_relevant_courses**: Count the number of courses in the pre-filled list. If none, use 0.
The secretariat has already selected the relevant courses; accept their list as-is.

### 4. master_coeff — 0 / 2 / 6 / 10

- **0**: No master's degree (or only enrolled, not completed)
- **2**: Master's in unrelated field (law, education without tech, public administration, business)
- **6**: Partially related (techno-economics, educational technology, biomedical informatics)
- **10**: Directly ICT-related (CS, EE, Networks, Data Science, Cybersecurity, AI/ML)

### 5. ref1_pts and ref2_pts — 0 / 3 / 6 / 10

Score each letter independently:
- **0**: No letter
- **3**: Generic/weak; minimal specifics; or from a completely unrelated field
- **6**: Good letter with specifics; OR from related but non-CS/EE department; OR technical but generic
- **10**: Strong, specific letter from CS/EE department or senior technical professional with concrete examples of the applicant's abilities

### 6. experience_score — 0 to 10

Count RELEVANT experience only (software, IT, data engineering, networks, technical roles):
0 years→0, <0.5→1, 0.5–1.5→3, 1.5–3→5, 3–5→7, 5–7→8, >7→10.
Administrative roles in IT: count at 50%. Teaching: does not count.

### 7. relevant_pubs — integer ≥ 0

Peer-reviewed journal articles or conference papers on ICT topics only.
Requires actual PDF or DOI. Theses/reports/class projects: do NOT count.

### 8. bonus — 0 to 10, and bonus_reasons

Notable achievements beyond standard qualifications:
- Scholarships, distinctions, awards: 1–3 pts
- Competitive fellowships: 2–4 pts
- Erasmus+/international exchange: 1–2 pts
- Relevant technical certifications: 1–2 pts

Leave bonus=0 and bonus_reasons="" if nothing notable.

---

## CV Quality

**cv_quality**: "high" | "medium" | "low"
- high: Professional, specific verifiable claims, no unexplained gaps, consistent with all documents
- medium: Mostly professional with minor vagueness or small inconsistencies
- low: Vague/unverifiable claims, major inconsistencies, apparent exaggeration

**cv_notes**: 1–2 sentences on quality and any notable observations.

---

## Flags — EMPTY ARRAY for most applicants

Return [] unless there is a GENUINE PROBLEM requiring special attention:
- "Degree from [institution] — ΔΟΑΤΑΠ recognition uncertain per secretariat notes" (still score normally if subject is CS/CE)
- "CV claims [X] — no supporting document provided"
- "Overlapping positions at [A] and [B]: [dates]"
- "Secretariat flagged [document] as missing"

DO NOT flag:
- Reference letters from thesis supervisors or academic advisors — these are VALUED highly, not a conflict of interest. Score them higher (up to 10) if they are specific and address research ability.
- Low scores, missing recommendations, non-ICT background, or anything already captured by the scoring fields.

---

## Justification (cite specific documents)

For each dimension, 2–4 sentences including:
1. The score and the key reason
2. Specific document reference: "From CV, p.2: employed as Software Engineer at [Co.] 2021–2024" or "Letter from Prof. X ([Dept, Univ]) states '...'"
3. Any uncertainty

---

## Evaluator Comment

3–5 sentences: strongest/weakest dimensions, fit for the program, recommendation (strong / borderline / weak).

---

Return ONLY valid JSON — no markdown, no explanation.`

  return agent(prompt, {
    label: `eval-${s.app_id}-${s.surname}`,
    schema: SCHEMA,
    effort: s.paper_paths && s.paper_paths.length > 0 ? 'high' : 'medium'
  })
}))

return results.filter(Boolean)
