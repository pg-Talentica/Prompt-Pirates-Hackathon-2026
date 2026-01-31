# Task-002: Synthetic Dataset & Chunking Strategy

## Summary
Generate the fixed knowledge corpus (100+ documents, 5–6 pages each) and define the chunking and overlap strategy with a documented rationale.

## Scope
- Generate at least 100 synthetic files suitable for support/incident KB: runbooks, FAQs, incident summaries, product docs (mix of .txt, .pdf, .docx, .pptx as required; no image content)
- Each file: equivalent of 5–6 pages of text
- Define chunk size and overlap (e.g. token or character based); document rationale in README (semantic continuity, retrieval quality, model context limits)
- Script or process to place generated files in a known path (e.g. `data/kb/` or `corpus/`) for indexing

## Acceptance Criteria
- [ ] 100+ files generated and stored in repo or generated via script
- [ ] README section (or dedicated doc) describes chunk size, overlap, and justification
- [ ] No empirical eval required; rationale only
- [ ] No images; text-only content

## Dependencies
- Task-001 (project structure exists)

## Notes
- Optional stretch: support “upload doc” later; this task is fixed corpus only.
- File types: prioritize .txt and .pdf for simplicity; add .docx/.pptx if tooling is available.
