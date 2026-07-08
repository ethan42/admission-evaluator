#!/usr/bin/env python3
"""Generate HTML dashboard from evaluation results JSON."""
import json, csv, sys, os, re

DASHBOARD_DIR = '/mnt/c/Users/thana/pms/dashboard'
PROFILES_DIR  = os.path.join(DASHBOARD_DIR, 'profiles')
os.makedirs(PROFILES_DIR, exist_ok=True)

REL_MULT   = {0: 0.1, 1: 1.0, 2: 0.6}
REL_LABELS = {0: '0 — Άσχετο (×0.1)', 1: '1 — Σχετικό ΠΕ/ΗΜΜΥ (×1.0)', 2: '2 — Μερ. Μαθ/Τοπ/Φυσ (×0.6)'}
REL_BADGE  = {0: 'secondary', 1: 'success', 2: 'info'}
REL_ICON   = {0: '✗', 1: '✓', 2: '◑'}
THESIS_LABELS = {0: '0 — Καμία/υπό εκπ.', 3: '3 — Άσχετη ή βαθμ.<7', 8: '8 — ΤΠΕ, βαθμ. 7–8.5', 15: '15 — ΤΠΕ, βαθμ. >8.5'}
MASTER_LABELS = {0: '0 — Καμία', 2: '2 — Άσχετο', 6: '6 — Μερ. σχετικό', 10: '10 — Σχετικό ΤΠΕ'}
CV_BADGE   = {'high': 'success', 'medium': 'warning', 'low': 'danger'}
CV_LABEL   = {'high': 'Υψηλή', 'medium': 'Μεσαία', 'low': 'Χαμηλή'}


def load_csv():
    students = {}
    with open('/mnt/c/Users/thana/pms/basic.csv', newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            cv = row.get('Βιογραφικό σημείωμα', '')
            m = re.search(r'CV_ID_(\d+)', cv)
            sid = m.group(1) if m else 'unknown'
            students[sid] = dict(row)
    return students


def compute_total(s_csv, sc):
    try:
        dg    = float(s_csv.get('Βαθμός πτυχίου (1)', 0) or 0)
        rel   = int(sc.get('degree_relevance', 0))
        rm    = REL_MULT.get(rel, 0.1)
        ca    = float(sc.get('course_avg', 0) or 0)
        nc    = int(sc.get('n_relevant_courses', 0) or 0)
        cw    = min(nc, 6) / 6 if nc > 0 else 0
        tg    = float(s_csv.get('Βαθμός Πτυχιακής (1)', 0) or 0)
        tc    = int(sc.get('thesis_coeff', 0) or 0)
        mc    = int(sc.get('master_coeff', 0) or 0)
        r1    = int(sc.get('ref1_pts', 0) or 0)
        r2    = int(sc.get('ref2_pts', 0) or 0)
        exp   = int(sc.get('experience_score', 0) or 0)
        pubs  = int(sc.get('relevant_pubs', 0) or 0)
        bonus = int(sc.get('bonus', 0) or 0)
        total = (35*(dg/10)*rm + 30*(ca/10)*cw + 10*(min(pubs,3)/3)
                 + 8*((r1+r2)/2/10) + 6*(tg/10)*(tc/15)
                 + 4*(mc/10) + 4*(exp/10) + 3*(bonus/10))
        return round(min(total, 100), 1)
    except Exception as e:
        print(f"  Warning: total error: {e}", file=sys.stderr)
        return 0.0


def esc(s):
    return (str(s) if s else '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')


def score_color(t):
    return '#198754' if t >= 70 else ('#fd7e14' if t >= 50 else '#dc3545')


def badge_cls(t):
    return 'success' if t >= 70 else ('warning' if t >= 50 else 'danger')


def get_flags(sc):
    """Return flags as a list, handling both old (string in justification) and new (array) format."""
    flags = sc.get('flags', [])
    if isinstance(flags, list):
        return [f for f in flags if f and f.strip()]
    # legacy: string in justification
    old = (sc.get('justification', {}) or {}).get('flags', '') or ''
    old = old.strip()
    if old and old.lower() not in ('none', 'καμία', 'καμια', '-', '—', 'n/a', ''):
        return [old]
    return []


def generate_profile(s_csv, sc, total):
    sid    = sc['id']
    app_id = sc['app_id']
    name   = f"{s_csv.get('Επώνυμο','')} {s_csv.get('Όνομα','')}".strip()
    j      = sc.get('justification', {}) or {}

    rel  = int(sc.get('degree_relevance', 0))
    rm   = REL_MULT.get(rel, 0.1)
    dg   = float(s_csv.get('Βαθμός πτυχίου (1)', 0) or 0)
    tg   = float(s_csv.get('Βαθμός Πτυχιακής (1)', 0) or 0)
    tc   = int(sc.get('thesis_coeff', 0) or 0)
    ca   = float(sc.get('course_avg', 0) or 0)
    nc   = int(sc.get('n_relevant_courses', 0) or 0)
    cw   = min(nc, 6) / 6 if nc > 0 else 0
    mc   = int(sc.get('master_coeff', 0) or 0)
    r1   = int(sc.get('ref1_pts', 0) or 0)
    r2   = int(sc.get('ref2_pts', 0) or 0)
    exp  = int(sc.get('experience_score', 0) or 0)
    pubs = int(sc.get('relevant_pubs', 0) or 0)
    bns  = int(sc.get('bonus', 0) or 0)

    pt_degree  = round(35*(dg/10)*rm, 1)
    pt_courses = round(30*(ca/10)*cw, 1)
    pt_pubs    = round(10*(min(pubs,3)/3), 1)
    pt_refs    = round(8*((r1+r2)/2/10), 1)
    pt_thesis  = round(6*(tg/10)*(tc/15), 1)
    pt_master  = round(4*(mc/10), 1)
    pt_exp     = round(4*(exp/10), 1)
    pt_bonus   = round(3*(bns/10), 1)

    cv_qual    = sc.get('cv_quality', '') or ''
    cv_notes   = sc.get('cv_notes', '') or ''
    flags_list = get_flags(sc)

    def pbar(pts, maxp, label='', just=''):
        pct = int(pts/maxp*100) if maxp else 0
        c = '#198754' if pct >= 70 else ('#fd7e14' if pct >= 40 else '#dc3545')
        jhtml = f'<div class="text-muted small mt-1" style="white-space:pre-wrap;">{esc(just)}</div>' if just else ''
        return (f'<tr><td class="align-top" style="width:220px"><strong>{esc(label)}</strong>'
                f'<div class="text-muted small">{pts}/{maxp} pts</div></td>'
                f'<td><div class="progress mb-1" style="height:20px;">'
                f'<div class="progress-bar fw-bold" style="width:{pct}%;background:{c};">'
                f'{pts}</div></div>{jhtml}</td></tr>')

    def trow(lbl, val, hi=False):
        cls = ' class="table-warning"' if hi else ''
        return f'<tr{cls}><td style="width:180px"><strong>{esc(lbl)}</strong></td><td>{esc(str(val)) if val else "—"}</td></tr>'

    courses_raw   = s_csv.get('Μάθημα','') or ''
    courses_lines = [c.strip() for c in courses_raw.split('\n') if c.strip()]
    courses_html  = ''.join(f'<li class="small">{esc(c)}</li>' for c in courses_lines) or '<li><em>—</em></li>'

    exp_orgs = [s_csv.get('Οργανισμός/Ίδρυμα (1)',''),
                s_csv.get('Οργανισμός/Ίδρυμα (2)',''),
                s_csv.get('Οργανισμός/Ίδρυμα (3)','')]
    exp_orgs_str = ', '.join(o for o in exp_orgs if o) or '—'

    total_c  = score_color(total)
    badge_c  = badge_cls(total)
    sec_note = s_csv.get('ΠΑΡΑΤΗΡΗΣΕΙΣ ΓΡΑΜΜΑΤΕΙΑΣ','') or ''

    # --- Flags section (only if non-empty) ---
    if flags_list:
        flags_html = (
            '<div class="alert alert-warning alert-dismissible fade show mt-3 mb-0">'
            '<strong>⚠ Επισημάνσεις:</strong>'
            '<ul class="mb-0 mt-1">' +
            ''.join(f'<li>{esc(f)}</li>' for f in flags_list) +
            '</ul>'
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'
            '</div>'
        )
    else:
        flags_html = ''

    # --- CV quality badge ---
    if cv_qual:
        cv_badge_html = (
            f'<span class="badge bg-{CV_BADGE.get(cv_qual,"secondary")} ms-2">'
            f'ΒΣ {CV_LABEL.get(cv_qual, cv_qual)}</span>'
        )
    else:
        cv_badge_html = ''

    # --- CV notes ---
    cv_notes_html = (
        f'<div class="card mb-3"><div class="card-header fw-bold">Αξιολόγηση Βιογραφικού {cv_badge_html}</div>'
        f'<div class="card-body py-2">{esc(cv_notes) if cv_notes else "<em>—</em>"}</div></div>'
    )

    sec_html = (
        f'<div class="alert alert-info py-2 mb-3"><strong>Γραμματεία:</strong> {esc(sec_note)}</div>'
        if sec_note else ''
    )

    distinctions = s_csv.get('Άλλες πληροφορίες (π.χ. υποτροφίες, διακρίσεις)','') or ''

    # Pre-compute justification strings to avoid backslash-in-fstring issue
    j_degree = f'Βαθμ.πτυχ.={dg} | {REL_LABELS[rel]}' + '\n' + j.get('degree','')
    j_courses = f'ΜΟ={ca}, N={nc}' + '\n' + j.get('courses','')
    j_pubs    = f'Σχετικές={pubs}' + '\n' + j.get('publications','')
    j_refs    = f'Ι={r1}/10, ΙΙ={r2}/10' + '\n' + j.get('refs','')
    j_thesis  = THESIS_LABELS.get(tc,'—') + '\n' + j.get('thesis','')
    j_master  = MASTER_LABELS.get(mc,'—') + '\n' + j.get('master','')
    j_exp     = f'{exp}/10' + '\n' + j.get('experience','')
    j_bonus   = f'{bns}/10 | {sc.get("bonus_reasons","—")}'

    return f'''<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} — ΠΜΣ ΤΠΕ 2026</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<style>
body{{font-size:14px;}}
.score-circle{{width:90px;height:90px;border-radius:50%;background:{total_c};
  color:#fff;font-size:24px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.just-text{{font-size:12px;color:#555;line-height:1.4;}}
</style>
</head>
<body>
<div class="container py-4" style="max-width:960px">
  <a href="../index.html" class="btn btn-outline-secondary btn-sm mb-3">← Πίνακας</a>

  <div class="d-flex align-items-start gap-4 mb-3">
    <div class="score-circle">{total}</div>
    <div class="flex-grow-1">
      <h2 class="mb-1">{esc(name)}</h2>
      <div class="text-muted mb-1">Αρ. Αίτησης: <strong>{esc(app_id)}</strong> &nbsp;·&nbsp; Αρχείο: {esc(sid)}</div>
      <span class="badge bg-{badge_c} fs-6 me-1">{total}/100</span>
      <span class="badge bg-{REL_BADGE.get(rel,'secondary')}">{REL_ICON.get(rel,'')} {REL_LABELS.get(rel,'')}</span>
      {cv_badge_html}
    </div>
  </div>

  {flags_html}
  {sec_html}

  <div class="card mb-3">
    <div class="card-header bg-primary text-white fw-bold">Παρατηρήσεις Αξιολογητών</div>
    <div class="card-body">{esc(sc.get('evaluator_comment',''))}</div>
  </div>

  {cv_notes_html}

  <div class="card mb-3">
    <div class="card-header fw-bold">Ανάλυση Βαθμολογίας — Σύνολο: {total}/100</div>
    <div class="card-body p-0">
      <table class="table table-sm table-bordered mb-0">
        <thead class="table-dark"><tr><th>Κριτήριο (μέγιστο)</th><th>Βαθμολογία &amp; Αιτιολόγηση</th></tr></thead>
        <tbody>
          {pbar(pt_degree, 35, 'Πτυχίο × Συνάφεια (35)', j_degree)}
          {pbar(pt_courses, 30, 'Μαθήματα ΜΟ (30)', j_courses)}
          {pbar(pt_pubs, 10, 'Δημοσιεύσεις (10)', j_pubs)}
          {pbar(pt_refs, 8, 'Συστατικές μ.ο. (8)', j_refs)}
          {pbar(pt_thesis, 6, 'Διπλωματική (6)', j_thesis)}
          {pbar(pt_master, 4, 'Μεταπτυχιακό (4)', j_master)}
          {pbar(pt_exp, 4, 'Εμπειρία (4)', j_exp)}
          {pbar(pt_bonus, 3, 'Πριμοδότηση (3)', j_bonus)}
        </tbody>
      </table>
    </div>
  </div>

  <div class="row g-3">
    <div class="col-md-6">
      <div class="card h-100">
        <div class="card-header fw-bold">Προπτυχιακές Σπουδές</div>
        <div class="card-body">
          <table class="table table-sm mb-2">
            <tbody>
              {trow('Ίδρυμα', s_csv.get('ΑΕΙ (1)'))}
              {trow('Τμήμα', s_csv.get('Τμήμα (1)'))}
              {trow('Βαθμός πτυχίου', s_csv.get('Βαθμός πτυχίου (1)'))}
              {trow('Συνάφεια', REL_LABELS.get(rel,'—'), hi=True)}
              {trow('Τίτλος Πτυχιακής', s_csv.get('Τίτλος Πτυχιακής (1)'))}
              {trow('Βαθμός Πτυχιακής', s_csv.get('Βαθμός Πτυχιακής (1)'))}
              {trow('Συντ. Πτυχιακής', THESIS_LABELS.get(tc,'—'), hi=True)}
            </tbody>
          </table>
          <strong class="small">Σχετικά Μαθήματα:</strong>
          <ul class="mb-1 ps-3">{courses_html}</ul>
          <small class="text-muted">ΜΟ: {ca} | N={nc}</small>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card mb-3">
        <div class="card-header fw-bold">Μεταπτυχιακές Σπουδές</div>
        <div class="card-body">
          <table class="table table-sm mb-0">
            <tbody>
              {trow('Ίδρυμα', s_csv.get('ΑΕΙ (Master-1)') or '—')}
              {trow('Τμήμα', s_csv.get('Τμήμα (Master-1)') or '—')}
              {trow('Τίτλος', s_csv.get('Μεταπτυχιακός Τίτλος-1') or '—')}
              {trow('Βαθμός', s_csv.get('Βαθμός πτυχίου (Master-1)') or '—')}
              {trow('Συντ. Μεταπτ.', MASTER_LABELS.get(mc,'—'), hi=True)}
            </tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <div class="card-header fw-bold">Γλωσσομάθεια &amp; Λοιπά</div>
        <div class="card-body">
          <table class="table table-sm mb-0">
            <tbody>
              {trow('Αγγλικά', s_csv.get('Επίπεδο Αγγλικών') or '—')}
              {trow('Άλλη γλώσσα', s_csv.get('Άλλη γλώσσα') or '—')}
            </tbody>
          </table>
          {f'<p class="small text-muted mt-2 mb-0">{esc(distinctions)}</p>' if distinctions else ''}
        </div>
      </div>
    </div>
  </div>

  <div class="card mt-3">
    <div class="card-header fw-bold">Συστατικές Επιστολές</div>
    <div class="card-body">
      <table class="table table-sm mb-2">
        <tbody>
          {trow('Συστ. Ι — Όνομα', s_csv.get('Συστατική 1 Όνομα') or '—')}
          {trow('Συστ. Ι — Ίδρυμα', s_csv.get('Ίδρυμα/Τμήμα 1') or '—')}
          {trow('Συστ. Ι — Πόντοι', f'{r1}/10', hi=True)}
          {trow('Συστ. ΙΙ — Όνομα', s_csv.get('Συστατική 2 Όνομα') or '—')}
          {trow('Συστ. ΙΙ — Ίδρυμα', s_csv.get('Ίδρυμα/Τμήμα 2') or '—')}
          {trow('Συστ. ΙΙ — Πόντοι', f'{r2}/10', hi=True)}
        </tbody>
      </table>
      <div class="just-text">{esc(j.get('refs',''))}</div>
    </div>
  </div>

  <div class="row g-3 mt-0">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header fw-bold">Εμπειρία</div>
        <div class="card-body">
          <table class="table table-sm mb-2">
            <tbody>
              {trow('Έτη (σύνολο)', s_csv.get('Έτη Επαγ/κής Εμπειρίας') or '—')}
              {trow('Οργανισμοί', exp_orgs_str)}
              {trow('Βαθμός', f'{exp}/10', hi=True)}
            </tbody>
          </table>
          <div class="just-text">{esc(j.get('experience',''))}</div>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card">
        <div class="card-header fw-bold">Δημοσιεύσεις &amp; Πριμοδότηση</div>
        <div class="card-body">
          <table class="table table-sm mb-2">
            <tbody>
              {trow('Δηλωμένες δημ.', s_csv.get('Αριθμός Δημοσιεύσεων') or '0')}
              {trow('Τίτλος πρώτης', s_csv.get('Τίτλος (1)') or '—')}
              {trow('Σχετικές (βαθμ.)', f'{pubs} → {pt_pubs}/10', hi=True)}
              {trow('Πριμοδότηση', f'{bns}/10 → {pt_bonus}/3 pts', hi=True)}
              {trow('Λόγοι πριμοδ.', sc.get('bonus_reasons','') or '—')}
            </tbody>
          </table>
          <div class="just-text">{esc(j.get('publications',''))}</div>
        </div>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''


def generate_index(rows):
    rows_sorted = sorted(rows, key=lambda x: x['total'], reverse=True)
    trs = ''
    for rank, r in enumerate(rows_sorted, 1):
        t    = r['total']
        sc   = r['scored']
        s    = r['s_csv']
        sid  = sc['id']
        name = f"{s.get('Επώνυμο','')} {s.get('Όνομα','')}".strip()
        rel  = int(sc.get('degree_relevance', 0))
        ri   = REL_ICON.get(rel, '?')
        tc   = score_color(t)
        flags = get_flags(sc)
        flag_icon = '<span title="Επισημάνσεις!" class="text-warning">⚠ </span>' if flags else ''
        # CV quality badge
        cvq = sc.get('cv_quality', '') or ''
        cv_badge = (f'<span class="badge bg-{CV_BADGE.get(cvq,"secondary")} '
                    f'badge-sm">{cvq[:1].upper() if cvq else "?"}</span>') if cvq else ''
        # Bonus reasons (truncated)
        br = sc.get('bonus_reasons','') or ''
        br_short = (br[:45] + '…') if len(br) > 45 else br
        br_html = f'<span title="{esc(br)}">{esc(br_short)}</span>' if br else '<span class="text-muted">—</span>'
        # Department name (truncated)
        dept = (s.get('Τμήμα (1)','') or '')
        dept_short = (dept[:35] + '…') if len(dept) > 35 else dept
        trs += f'''<tr>
          <td class="text-center">{rank}</td>
          <td><a href="profiles/{sid}.html">{flag_icon}{esc(name)}</a> {cv_badge}</td>
          <td class="text-center">{esc(sc.get("app_id",""))}</td>
          <td title="{esc(s.get("ΑΕΙ (1)",""))} — {esc(dept)}">{esc((s.get("ΑΕΙ (1)","") or "").split()[0])}<br>
              <small class="text-muted">{esc(dept_short)}</small></td>
          <td class="text-center">{esc(s.get("Βαθμός πτυχίου (1)",""))}</td>
          <td class="text-center"><span class="badge bg-{REL_BADGE.get(rel,"secondary")}">{ri}</span></td>
          <td class="text-center">{sc.get("thesis_coeff",0)}</td>
          <td class="text-center">{sc.get("master_coeff",0)}</td>
          <td class="text-center">{sc.get("ref1_pts",0)}/{sc.get("ref2_pts",0)}</td>
          <td class="text-center">{sc.get("experience_score",0)}</td>
          <td class="text-center">{sc.get("relevant_pubs",0)}</td>
          <td class="text-center">{sc.get("bonus",0)}</td>
          <td class="small text-muted">{br_html}</td>
          <td class="text-center fw-bold" style="color:{tc};">{t}</td>
        </tr>'''

    return f'''<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ΠΜΣ ΤΠΕ 2026 — Αξιολόγηση Αυγερινός+Νάκος</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
<style>
body{{font-size:13px;}}
th{{white-space:nowrap;}}
</style>
</head>
<body>
<div class="container-fluid py-3">
  <h2 class="mb-1">ΠΜΣ ΤΠΕ 2026 — Αξιολόγηση Υποψηφίων</h2>
  <p class="text-muted mb-3">
    Επιτροπή: Αυγερινός + Νάκος &nbsp;·&nbsp; {len(rows)} υποψήφιοι &nbsp;·&nbsp;
    <span class="badge bg-success">✓ Σχετικό (×1.0)</span>
    <span class="badge bg-info text-dark">◑ Μαθ/Φυσ/Τοπ (×0.6)</span>
    <span class="badge bg-secondary">✗ Άσχετο (×0.1)</span>
    &nbsp;
    <span class="badge bg-success">ΒΣ Υψηλή</span>
    <span class="badge bg-warning text-dark">ΒΣ Μεσαία</span>
    <span class="badge bg-danger">ΒΣ Χαμηλή</span> CV
  </p>
  <div class="table-responsive">
    <table id="T" class="table table-sm table-hover table-bordered">
      <thead class="table-dark">
        <tr>
          <th>#</th><th>Ονοματεπώνυμο</th><th>Αίτ.</th><th>Τμήμα / ΑΕΙ</th>
          <th>Βαθμ.</th><th>Συν.</th><th>Θέση</th><th>ΜΠΣ</th>
          <th>Συστ.Ι/ΙΙ</th><th>Εμπ.</th><th>Δημ.</th><th>Πριμ.</th>
          <th>Λόγοι Πριμ.</th>
          <th>Σύνολο</th>
        </tr>
      </thead>
      <tbody>{trs}</tbody>
    </table>
  </div>
  <details class="mt-4">
    <summary class="fw-bold text-muted small">Φόρμουλα Βαθμολόγησης</summary>
    <div class="card mt-2 bg-light"><div class="card-body font-monospace small">
      Σύνολο = 35×(βαθμ/10)×συν + 30×(ΜΟ/10)×(min(N,6)/6) + 10×(min(δημ,3)/3)<br>
      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; + 8×((Ι+ΙΙ)/2/10) + 6×(βθΘ/10)×(συντΘ/15) + 4×(ΜΠΣ/10) + 4×(εμπ/10) + 3×(πριμ/10)<br>
      Συνάφεια: 0→×0.1 | 1(ΠΕ/ΗΜΜΥ)→×1.0 | 2(Μαθ/Φυσ/Τοπ)→×0.6
    </div></div>
  </details>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
<script>
$(()=>{{$('#T').DataTable({{paging:false,order:[[13,'desc']],
  language:{{search:'Αναζήτηση:',info:'_TOTAL_ υποψήφιοι',infoEmpty:'0 αποτελέσματα'}}}});}});
</script>
</body>
</html>'''


def update_csv(students_map, results):
    score_map = {r['scored']['app_id']: r for r in results}
    rows_out = []
    with open('/mnt/c/Users/thana/pms/basic.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            app_id = row.get('Αρ. Αίτησης','')
            if app_id in score_map:
                r  = score_map[app_id]
                sc = r['scored']
                row['Συνάφεια πτυχίου (0/1/2)']  = sc.get('degree_relevance','')
                row['Συντ. Πτυχιακής (0-15)']     = sc.get('thesis_coeff','')
                row['ΜΟ βαθμών']                   = sc.get('course_avg', row.get('ΜΟ βαθμών',''))
                row['Συντ. Μεταπτυχ. (0-10)']     = sc.get('master_coeff','')
                row['Πόντοι Συστ. Ι (0-10)']      = sc.get('ref1_pts','')
                row['Πόντοι Συστ. ΙΙ (0-10)']     = sc.get('ref2_pts','')
                row['Εμπειρία (0-10)']             = sc.get('experience_score','')
                row['Σχετ. Δημοσιεύσεις (#)']     = sc.get('relevant_pubs','')
                row['Πριμοδότηση (0-10)']          = sc.get('bonus','')
                row['Λόγοι πριμοδότησης']          = sc.get('bonus_reasons','')
                row['Παρατηρήσεις αξιολογητών']   = sc.get('evaluator_comment','')
                row['Σύνολο (0-100)']              = r['total']
                missing = []
                if not row.get('ΜΟ βαθμών'): missing.append('ΜΟ')
                if str(row.get('Συντ. Πτυχιακής (0-15)','')).strip() == '': missing.append('ΣυντΘ')
                if str(row.get('Πόντοι Συστ. Ι (0-10)','')).strip() == '': missing.append('ΠόντΣυστΙ')
                row['Έλεγχος πληρότητας'] = '✓ Πλήρες' if not missing else 'Λείπει: ' + ', '.join(missing)
            rows_out.append(row)
    out = '/mnt/c/Users/thana/pms/basic_scored.csv'
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)
    print(f"CSV → {out}")
    return out


def main(results_file):
    print(f"Loading {results_file}...")
    with open(results_file, encoding='utf-8') as f:
        scored_list = json.load(f)
    print(f"  {len(scored_list)} results")

    students_map = load_csv()
    with open('/mnt/c/Users/thana/pms/dashboard/_app_to_sid.json', encoding='utf-8') as f:
        app_to_sid = json.load(f)

    results = []
    for sc in scored_list:
        app_id = sc.get('app_id','')
        sid    = app_to_sid.get(str(app_id), sc.get('id',''))
        sc['id'] = sid
        s_csv  = students_map.get(sid, {})
        total  = compute_total(s_csv, sc)
        results.append({'scored': sc, 's_csv': s_csv, 'total': total})

    print("Generating profiles...")
    for r in results:
        sid  = r['scored']['id']
        html = generate_profile(r['s_csv'], r['scored'], r['total'])
        with open(os.path.join(PROFILES_DIR, f"{sid}.html"), 'w', encoding='utf-8') as f:
            f.write(html)

    idx = generate_index(results)
    idx_path = os.path.join(DASHBOARD_DIR, 'index.html')
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(idx)
    print(f"Index → {idx_path}")

    update_csv(students_map, results)

    out_json = os.path.join(DASHBOARD_DIR, '_results.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(scored_list, f, ensure_ascii=False, indent=2)
    print(f"Results JSON → {out_json}")

    print("\nScores summary (sorted by total):")
    for r in sorted(results, key=lambda x: x['total'], reverse=True):
        sc  = r['scored']
        cvq = sc.get('cv_quality','?')
        flg = '⚠' if get_flags(sc) else ' '
        print(f"  {r['total']:5.1f}  {sc.get('app_id',''):6}  "
              f"{r['s_csv'].get('Επώνυμο',''):22}  "
              f"rel={sc.get('degree_relevance',0)} tc={sc.get('thesis_coeff',0):2} "
              f"mc={sc.get('master_coeff',0):2} r1={sc.get('ref1_pts',0):2} r2={sc.get('ref2_pts',0):2} "
              f"exp={sc.get('experience_score',0):2} pub={sc.get('relevant_pubs',0)} "
              f"b={sc.get('bonus',0)} cv={cvq} {flg}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 _generate.py results.json")
        sys.exit(1)
    main(sys.argv[1])
