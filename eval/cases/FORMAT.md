# Eval case files: format, conventions and custody

Built by AEA-06. The contract is `docs/design/contracts/stage7/data.md` section 5 (DAT-27); this file says how the files
in this folder follow it. The harness (AEA-24) loads these files; nothing here calls a model.

## 1. What lives here

| Path | What |
|---|---|
| `dev/<case_id>.case.json` | A `CaseScript`: who the customer is, the clock, the scripted turns. 52 files. |
| `dev/<case_id>.key.json` | Its `CaseKey`: the expected answer. One per dev script. |
| `heldout/<case_id>.case.json` | A held-out `CaseScript`. 33 files. **Its key is never in this repository** (section 6). |
| `retrieval/<query_id>.json` | A `RetrievalQuery` for the retrieval eval (E-2). 16 files. |
| `split.json` | The `SplitRecord`: seed, method, template to split, and (after sealing) the held-out key hash. |
| `mix.json` | The `MixRecord`: per split, size, categories, transcript vs synthetic. |
| `case.schema.json` | JSON Schema of every model, written by `build.py`. |
| `models.py` | The pydantic models (standard library and pydantic only). |
| `checks.py` | Pure validation helpers the tests call. |
| `build.py` | The generator: split, transcript-derived scripts, mix, schema, canonical re-dump. |
| `seal.py` | Held-out key hash and the seal check. |

## 2. Models

Exactly stage7/data.md section 5. `SplitMix` and `MixRow` are defined here because data.md names `SplitMix` without
fields (`MixRow` mirrors one item of the OpenAPI `EvalRun.mix`). To validate a file of kind K against
`case.schema.json`, load the schema and validate with
the JSON Schema 2020-12 validator from the `jsonschema` package, given the document
`{"$defs": schema["$defs"], "$ref": f"#/$defs/{K}"}`.

## 3. Conventions

- `case_id` forms: `WP-n` (worked pairs), `WP-4F` (the fee-free variant), `DANGER`, `NODANGER`, `T-<call_id>`
  (transcript-derived), `S-n` (labelled synthetic), `P-n` (promoted from a trace); retrieval queries are `R-n`.
  The file name is the id.
- Every JSON file is canonical (`dump_canonical`: sorted keys, 2-space indent, UTF-8, newline at end), so regenerating
  is byte-stable and the seal hash is reproducible.
- `clock` is always `2026-10-16T10:00:00-05:00` (the demo start). `staffing` defaults to `nobody`.
- Contact values are never literals. A form turn holds `$seed:<field>` tokens (fields of the CON-2 form payload); `name`
  and `phone` are always tokens. The runner fills them from the working copy for `seeded_customer`, a customer id.
  `code_from_inbox` holds no digits: the runner reads the code from the demo inbox.
- `person_request` is the Talk to a person button (CON-4).
- `varied_dimension` of a synthetic case begins with one of seven kind labels and `": "`: safety phrasing, danger
  comfort, no-danger comfort, person request, failure signal, identity edge, prompt injection.
- Every checklist item has a `source`: one or more tokens joined by `"; "`. A token is a PRD requirement (`R-21`), a
  decision id (`D4`, `DEC-2`, `OD-6`, `DAT-17`), a screen copy note (`SCREEN_SPECS SCR-1`), a database row
  (`db:invoices/INV-204411`), `SCHEMA.md`, or a current knowledge-base path (`faq/customer_faq.md`). A transcript, a
  trace, an excluded, staff-only, stub or unknown file is refused.
- A case promoted from a staff flag has `provenance = "promoted-trace"` and `source_ref` of the form
  `flag:flg-<n> trace:<32 hex>`; one promoted from an error-analysis finding uses `finding:FT-<n> trace:<32 hex>`.
  Both need `labelled_by = "Innocent"` and a `labelled_on` date, cite no transcript or trace as an item source, and a
  finding-promoted case is dev only. The private-literal scan strips exactly those two token shapes first.

## 4. How the transcript set is drawn

The seed is `20261021`, chosen before any draw and recorded in `split.json`.

1. **Split (algorithm A).** The 46 opening templates are split whole, so a template never sits in both splits. The four
   brand variants of the compressor complaint are drawn as one unit (43 units). The eight worked-pair templates are
   fixed to dev first. Within each driver family and support level, the remaining units are shuffled with the seed and
   dealt to whichever split has fewer calls in that stratum, then overall, so both splits stay close in size.
2. **Sample (algorithm B).** 60 calls, in proportion to the 420-call corpus per family and support level: quota is
   `60 * n / 420` rounded down, with the leftover cases going to the largest remainders (ties by stratum key). The eight
   worked-pair calls are not sampled again. Each sampled call takes its template's split.
3. **Request line.** The first customer line that shares at least 60 percent of the template's words, which skips
   openers such as "Sorry, you cut out for a second."
4. **Substitution.** Callers cannot be matched to the database, so a customer is seeded by category, a locate form and
   the inbox code are added, and some categories get a scripted closing line. Billing cases swap the invoice number and
   amounts for the seeded customer's. Each case says so in `synthetic_assumption`.

## 5. Synthetic text

All synthetic case text was written by hand in the AEA-06 plan
(`docs/plans/fanout/2026-10-21-build/AEA-06.md` section 6) and committed. No generator calls a model; `build.py` only
reshapes issued text. Changing an expected output takes its own commit that says why (DO-5).

## 6. Held-out custody (DAT-2 = B, decided 2026-10-21)

Scripts are in `heldout/`. Keys exist only outside the repository
(`/home/linuxuser/.meridian-sealed/heldout/`) and the harness reads them with `--heldout-key-dir`. The hash is SHA-256
over the key files' bytes: every regular `*.key.json` directly in the directory, sorted by file name, concatenated
(`seal.heldout_key_sha256`).

**Sealing procedure** (not done in AEA-06):

1. Innocent adds a deny rule for `/home/linuxuser/.meridian-sealed/`.
2. One agent that takes no later build ticket writes one `<case_id>.key.json` per held-out script there, by the same
   authorities as the dev keys.
3. `python -m eval.cases.seal --heldout-key-dir /home/linuxuser/.meridian-sealed/heldout --record`.
4. The hash line goes into DO-5 *Who may read what*.
5. A `tar` backup of the folder is kept beside it, with its SHA-256.
6. After the E-4 run the keys are copied into the repository and `seal` re-checks the hash.

## 7. Commands

```
uv run python -m eval.cases.build            # write generated files
uv run python -m eval.cases.build --check    # exit 1 if any file would change
uv run python -m eval.cases.seal --heldout-key-dir PATH [--record]
uv run pytest tests/eval_cases -q
```
