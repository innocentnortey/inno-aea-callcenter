---
paths:
  - "**/*retriev*"
  - "**/*rag*"
  - "**/*embed*"
  - "**/*rerank*"
  - "**/*index*.py"
  - "**/*index*.ts"
  - "**/*chunk*"
  - "**/*prompt*"
  - "**/prompts/**"
  - "**/corpus/**"
---

> **Provenance:** copy of `Gauntlet AI/.claude/rules/retrieval-and-context.md` (zero-to-hero principles pack), copied 2026-10-14. Change the original first, then re-copy.

# Retrieval and Context

Applies to retrieval pipelines, embedding and indexing code, chunkers, corpora, and prompt files.

Source: `principles/context-and-rag.md`, Gauntlet AI repo.

## Rules

1. **Fewer, better tokens [GP-25].** Send the model the context a question needs, not everything that fits. Reference material over a few thousand tokens goes behind retrieval, not into the system prompt. System prompts hold role, rules and output contract.
2. **Evaluate retrieval on its own [GP-26].** Retrieval has its own cases (query → expected passages) and metrics (precision/recall at k), separate from answer quality.
3. **Name the RAG rung and justify it by eval [GP-27].** Naive → metadata-filtered → hybrid (BM25 + dense, rank-fused) → query decomposition/rewrite → graph → agentic. Moving up a rung requires eval cases the lower rung fails. Metadata filtering is the default first step.
4. **Relevance floor and refusal [GP-18].** Search always returns something. Apply a relevance threshold (on rerank or similarity score), and pass "no supporting evidence" to the model when nothing clears it.
5. **Retrieval configuration lives in one place [GP-28].** Embedding model, dimensions, similarity metric, chunker, chunk size and overlap, top-k and threshold are named constants or config, recorded next to the index. Default starting point: recursive character splitting at ~500 tokens, cosine similarity.
6. **One embedding model per index [GP-28].** Changing the model means re-embedding the whole corpus; make that an explicit migration, never a silent switch.
7. **Verify wiring at startup [GP-28].** Readiness checks confirm the index or collection name exists and its dimension matches the configured embedding model.
8. **Keep evidence stores separate and cited.** Retrieved guideline passages carry source, section and date, and never mix with patient-chart facts in a single citation.

## Review checklist

- [ ] Is there a query in the eval set that should return nothing, and does it?
- [ ] If a rung was added, which failing eval cases justified it?
- [ ] Are chunking and embedding settings in config, not scattered literals?
