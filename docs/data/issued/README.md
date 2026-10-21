# Issued data — Meridian Home Comfort (AEA FDE Challenge)

**Received 2026-10-20** from Innocent as `meridian_fde_dataset (1).zip` (Downloads), SHA-256
`ab143c1a8d752d4ed32cc532847f8e544c42feba0db267d01c6994e224796422`. Extracted unchanged into
`meridian_dataset/` (446 files; directory tree identical to the zip). Source IDs S-102…S-104 in
`docs/source/source-register.md`; the dataset's own `meridian_dataset/README.md` is ISSUED text.

**Do not edit anything under `meridian_dataset/`.** It is the reference copy. In particular,
`scheduling_db/meridian_scheduling.sqlite` is the database the reviewer will test against, so the
running agent works on a **copy** of it and the original stays pristine for reset and for checking
what the agent wrote. Our samples, worked pairs and findings go in `docs/data/` beside this folder,
never inside it.

| Asset | Path | What's in it |
|---|---|---|
| Call transcripts (S-102) | `meridian_dataset/call_transcripts/` + `call_transcripts_index.csv` | 420 calls, July–Sept 2026, STT text with `Agent:` / `Customer:` turns; index has call_id, timestamp, agent, duration only (no labels) |
| Knowledge base (S-103) | `meridian_dataset/knowledge_base/` | 17 files in 8 folders: Markdown, TXT, a PDF (`pricing/2026_fee_schedule.pdf`), a CSV (`pricing/repair_price_book_2026.csv`), a PNG (`policies/holiday_hours_2026.png`); `archive/` and `faq/faq_old_copy.md` look like outdated duplicates; `internal/` is agent-facing only |
| Scheduling DB (S-104) | `meridian_dataset/scheduling_db/` | SQLite + CSV exports of customers, technicians, appointment_slots, appointments, invoices; `SCHEMA.md` gives status values, the city→zone map, expected booking behaviour and four seeded test customers |

**"Today" is 2026-10-16** for this dataset (its README); slots run three weeks from then.
