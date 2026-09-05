# JOSS submission checklist

The submission lives at `output/joss_submission/`. To complete it, you need to:

## Pre-submission

1. **Replace `<OWNER>`** in `CITATION.cff` with your GitHub username.  ← done (Tiankai Wang / wangtiankai)
2. **Replace `[1]` affiliation** in `paper.md` with your actual affiliation.  ← done (Texas State University)
3. **Trim the paper** to JOSS's target: ~250–1000 words is typical. The current draft is on the longer side; cut the worked-downstream-application paragraph if you want to stay tight.
4. **Push to a public git repo** (GitHub is standard) with the following contents at the repo root:
   - `paper.md`
   - `paper.bib`
   - `LICENSE`
   - `README.md`
   - `pyproject.toml`
   - `CITATION.cff`
   - `ng911_extract/__init__.py` and `ng911_extract/pipeline.py`
   - `tests/test_panel.py`
   - `.github/workflows/test.yml`
   - `code/` (the four scripts)
   - `data/ng911/state_ng911_panel.csv`
   - `data/ng911/raw_pdfs/` (the eight source PDFs)

## Submission

5. **Wait at least six months after the repo's first public commit** before submitting. JOSS requires more than six months of public development history with iterative activity. Submissions made public just before submission are pre-review-screened out.
6. Submit via http://joss.theoj.org/papers/new (the old `joss.theoj.org/submit` URL no longer resolves).
7. After acceptance, deposit the tagged release with Zenodo to obtain a DOI; JOSS will then issue a CrossRef DOI for the paper itself.
8. The smoke tests already pass against the real panel (10 tests, all PASS). The CI workflow is included so reviewers see a passing badge immediately.

## Estimated total time

- Filling in remaining placeholders: 15 min.
- Setting up GitHub repo with the listed contents: 1 hour.
- Six-month public development history: must wait.
- Submission form (after the six months): 15 min.

Total wall-clock from "draft ready" to "submitted": at least six months + ~1.5 hours of work.

## Notes

- JOSS does not require novelty; they explicitly want software that is "of value to the community" and "respects the discipline's norms." A reproducible extraction pipeline with documented data gaps meets that bar.
- The paper.md does NOT cite the negative empirical finding prominently. If reviewers push for "what did you learn?", you can point them at `output/verdict_ng911.md` (which lives outside the JOSS submission scope) as a worked example.
- The "Functionality" section names scripts by filename. JOSS prefers this to prose; keep it.
