"""Reproduces every non-classification number cited in docs/data/handoff-information-inventory.md.

Run:  python3 -I checks_handoff_inventory.py      (read-only on the issued dataset; SQLite opened mode=ro)
Run classify_calls.py first: this script reads ../handoff-inventory-call-map.csv.
"""
import sys, os, re, csv, json, sqlite3, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_calls import load, ROOT
from classify_calls import first_request, is_noise
calls = load()
rows = {r["call_id"]: r for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handoff-inventory-call-map.csv")))}
db = sqlite3.connect("file:" + os.path.abspath(os.path.join(ROOT, "scheduling_db", "meridian_scheduling.sqlite")) + "?mode=ro", uri=True)
AG = lambda v: " ".join(t for s, t in v["turns"] if s == "Agent")
CU = lambda v: " ".join(t for s, t in v["turns"] if s == "Customer")
def h(t): print(f"\n### {t}")

h("C1  corpus and index")
idx = list(csv.DictReader(open(os.path.join(ROOT, "call_transcripts_index.csv"))))
def secs(d):
    m = re.match(r"(?:(\d+)m )?(\d+)s", d); return int(m.group(1) or 0) * 60 + int(m.group(2))
bad = [r["call_id"] for r in idx if r["call_id"] not in calls or int(r["duration_sec"]) != secs(calls[r["call_id"]]["head"]["Duration"]) or r["timestamp"] != calls[r["call_id"]]["head"]["Date"] or r["agent"] != calls[r["call_id"]]["head"]["Agent"]]
print("transcripts", len(calls), "| index rows", len(idx), "| index/header mismatches", len(bad), "| direction", collections.Counter(v["head"]["Direction"] for v in calls.values()))
print("date range", min(v["head"]["Date"] for v in calls.values()), "->", max(v["head"]["Date"] for v in calls.values()))

h("C2  can the DB verify any transcript caller?")
ids = {r[0] for r in db.execute("select customer_id from customers")}
phones = {r[0] for r in db.execute("select phone from customers")}
invs = {r[0] for r in db.execute("select invoice_id from invoices")}
acc, inv, ph = set(), set(), set()
for v in calls.values():
    acc |= set(re.findall(r"MHC-\d+", v["text"])); inv |= set(re.findall(r"INV-\d+", v["text"])); ph |= set(re.findall(r"\d{3}-\d{3}-\d{4}", v["text"]))
print(f"account IDs in calls {len(acc)}, found in customers {len(acc & ids)} | phones {len(ph)}, found {len(ph & phones)} | invoice IDs {len(inv)}, found {len(inv & invs)}")
reps = [a for coll in (acc, ph, inv) for a in coll if sum(a in v["text"] for v in calls.values()) > 1]
print("identifiers repeated across calls:", len(reps))
print("seeded customer IDs MHC-10001..10004 mentioned in any call:", any(s in v["text"] for v in calls.values() for s in ("MHC-10001", "MHC-10002", "MHC-10003", "MHC-10004")), "| INV-204411 mentioned:", any("INV-204411" in v["text"] for v in calls.values()))

h("C3  DB: invoices, appointments, what is missing")
print("customers", db.execute("select count(*) from customers").fetchone()[0], "| tiers", dict(db.execute("select membership_tier,count(*) from customers group by 1")))
print("invoices", db.execute("select count(*), sum(balance_cents>0), sum(appointment_id is null) from invoices").fetchone(), "(count, open, appointment_id NULL)")
print("open invoices past due vs 2026-10-16:", db.execute("select count(*) from invoices where balance_cents>0 and due_date<'2026-10-16'").fetchone()[0])
d_with_repair = 0; credit = 0; n_diag = 0
for iid, lines in db.execute("select invoice_id,line_items from invoices"):
    L = [x["desc"] for x in json.loads(lines)]
    if "Diagnostic visit" in L:
        n_diag += 1
        if [x for x in L if x not in ("Diagnostic visit", "Equipment disposal", "Disposal", "Mechanical permit", "Leak search")]: d_with_repair += 1
    if any("credit" in x.lower() for x in L): credit += 1
print(f"invoices with a Diagnostic visit line: {n_diag}; of those also billing a repair line: {d_with_repair}; invoices with any credit line: {credit}")
print("INV-204411:", db.execute("select line_items,amount_cents from invoices where invoice_id='INV-204411'").fetchone())
print("appointments by status/warranty:", db.execute("select status,is_warranty_visit,count(*) from appointments group by 1,2").fetchall())
print("appointments created after 2026-10-16:", db.execute("select count(*) from appointments where created_at>'2026-10-16'").fetchone()[0], "of", db.execute("select count(*) from appointments").fetchone()[0])
print("tables:", [r[0] for r in db.execute("select name from sqlite_master where type='table'")])
print("slot weekdays present (0=Sun):", sorted({r[0] for r in db.execute("select strftime('%w',slot_date) from appointment_slots")}), "| 16:00-19:00 weekdays:", sorted({r[0] for r in db.execute("select strftime('%w',slot_date) from appointment_slots where window='16:00-19:00'")}))
print("estimate-slot windows:", dict(db.execute("select window,count(*) from appointment_slots where service_type='estimate' group by 1")))

h("C4  dispute arithmetic")
d = collections.Counter(); why = collections.Counter()
for k, r in rows.items():
    if r["initial"] == "BILL-DISPUTE":
        m = re.search(r"quoted me \$(\d+) and the invoice says \$(\d+)", calls[k]["text"]); d[int(m.group(2)) - int(m.group(1))] += 1
        why[re.search(r"difference is the ([a-z\- ]+?) which", AG(calls[k]).lower()).group(1)] += 1
print("invoice minus quote:", dict(d), "| cause stated by agent:", dict(why))

h("C5  reschedule calls vs the 24-hour rule (call timestamp taken at face value)")
start = {"8": 8, "12": 12, "1": 13, "4": 16}; inside = 0; n = 0; fee = 0
for k, r in rows.items():
    if r["initial"] != "SCH-RESCHED": continue
    v = calls[k]; m = re.search(r"appointment tomorrow,? (\d+) to (\d+)", AG(v)); when = datetime.datetime.fromisoformat(v["head"]["Date"])
    st = datetime.datetime.combine((when + datetime.timedelta(days=1)).date(), datetime.time(start[m.group(1)]))
    n += 1; inside += (st - when).total_seconds() < 24 * 3600; fee += "fee" in AG(v).lower()
print(f"reschedule calls {n}; start of window < 24h after the call: {inside}; agent mentions any fee: {fee}")

h("C6  what handoff-type calls contain")
HAND = ["SAF-GAS", "SAF-CO", "SAF-SPARK", "BILL-DISPUTE", "BILL-REFUND", "COMPLAINT-REPEAT", "COMPLAINT-CONDUCT", "COMPLAINT-OPINION", "COMMERCIAL"]
hc = [k for k, r in rows.items() if r["initial"] in HAND]
print("handoff-type calls (escalation-type opening):", len(hc), f"{len(hc)/len(rows):.1%}")
for lbl, rx in (("callback window/time asked", r"callback window|best time|what time (works|is best)|good time to (call|reach)"), ("callback number asked", r"best (phone )?number|number to reach|reach you at"), ("reference/case/ticket number given", r"reference number|case number|ticket number|confirmation number")):
    print(f"  {lbl}: agent-side in {sum(1 for k in calls if re.search(rx, AG(calls[k]).lower()))} of 420 calls")
print("  phone number spoken in the call, by group:", {g: f"{sum(int(rows[k]['phone_spoken']) for k in hc if rows[k]['initial'] in cats)}/{sum(1 for k in hc if rows[k]['initial'] in cats)}" for g, cats in {"safety": HAND[:3], "dispute": ["BILL-DISPUTE"], "refund": ["BILL-REFUND"], "commercial": ["COMMERCIAL"]}.items()})
comp = ["COMPLAINT-REPEAT", "COMPLAINT-CONDUCT", "COMPLAINT-OPINION"]
print("  complaint phone spoken:", f"{sum(int(rows[k]['phone_spoken']) for k in hc if rows[k]['initial'] in comp)}/{sum(1 for k in hc if rows[k]['initial'] in comp)}", "| all 54:", f"{sum(int(rows[k]['phone_spoken']) for k in hc)}/{len(hc)}")
print("  identity step in safety calls:", sum(1 for k in hc if rows[k]['initial'].startswith('SAF') and re.search(r'E-IDENT', rows[k]['events'])), "of 9")
print("  promise events:", collections.Counter(e for k in hc for e in rows[k]["events"].split("|") if e.startswith("E-PROMISE")))

h("C7  emergent escalation: escalation words in the customer's LATER turns, outside escalation categories")
kw = re.compile(r"manager|supervisor|refund|gas|smell|carbon|spark|lawyer|attorney|sue |chargeback|legal|dispute|breaker|tripped|smoke|fire|flame|someone in charge")
cnt = 0
for k, v in calls.items():
    if rows[k]["initial"] in HAND: continue
    cust = [(i, t) for i, (s, t) in enumerate(v["turns"]) if s == "Customer" and not is_noise(t)]
    cnt += sum(1 for i, (s, t) in enumerate(v["turns"]) if i > cust[0][0] and s == "Customer" and kw.search(t.lower()))
print("hits:", cnt, "(0 means no benign call turned into a dispute, refund, manager request or safety report)")
print("burning-smell calls mentioning a breaker (either speaker):", sum(1 for k, r in rows.items() if r["initial"] == "SCH-BURNING" and re.search(r"breaker|tripped", calls[k]["text"].lower())), "of 16")

h("C8  scripted habits the KB asks for, absent from the calls")
book = [k for k, r in rows.items() if r["family"] == "F1 New service booking"]
for lbl, rx in (("troubleshooting checks (filter/breaker/float switch)", r"air filter|breaker|float switch|check the filter|thermostat is set"), ("gate code / pets / adult-present", r"gate|\bpets?\b|over 18|adult"), ("membership status asked", r"member")):
    print(f"  {lbl}: agent mentions in {sum(1 for k in book if re.search(rx, AG(calls[k]).lower()))} of {len(book)} booking-family calls")
print("  customer explicitly asks for a person/human/agent:", sum(1 for v in calls.values() if re.search(r"real person|human|speak to (a|an) (agent|rep|person)|representative", CU(v).lower())))
print("  customers asking for a manager / someone in charge:", sum(1 for v in calls.values() if re.search(r"manager|someone in charge", CU(v).lower())), "| agent lines naming supervisor/manager:", sum(1 for v in calls.values() if re.search(r"supervisor|manager", AG(v).lower())))
print("  diagnostic fee $89 quoted in tune-up calls:", sum(1 for k, r in rows.items() if r["initial"] == "SCH-TUNEUP" and "$89" in AG(calls[k])), "of 16; '$129' mentioned:", sum(1 for k, r in rows.items() if r["initial"] == "SCH-TUNEUP" and "$129" in AG(calls[k])))
print("  'portal' said by customer (BILL-BALANCE):", sum(1 for k, r in rows.items() if r["initial"] == "BILL-BALANCE" and "portal" in CU(calls[k]).lower()), "| by agent (BILL-AUTOPAY):", sum(1 for k, r in rows.items() if r["initial"] == "BILL-AUTOPAY" and "portal" in AG(calls[k]).lower()))
print("  compressor-warranty callers who ask to schedule:", sum(1 for k, r in rows.items() if r["initial"] == "WAR-PARTS" and "schedule it" in CU(calls[k]).lower()), "of 7 | calls where agent then books:", sum(1 for k, r in rows.items() if r["initial"] == "WAR-PARTS" and "E-BOOKED" in r["events"]))

h("C9  timing against knowledge-base hours")
dts = {k: datetime.datetime.fromisoformat(v["head"]["Date"]) for k, v in calls.items()}
print("Sunday calls:", sum(d.weekday() == 6 for d in dts.values()), "| 19:00 or later:", sum(d.hour >= 19 for d in dts.values()), "| Saturday outside 08:00-16:00:", sum(d.weekday() == 5 and not 8 <= d.hour < 16 for d in dts.values()), "| any outside customer_faq.md phone hours:", sum(not ((d.weekday() < 5 and 7 <= d.hour < 19) or (d.weekday() == 5 and 8 <= d.hour < 16)) for d in dts.values()))
print("calls dated 2026-09-07 (Labor Day, 'Emergency only' in holiday_hours_2026.png):", sum(d.date() == datetime.date(2026, 9, 7) for d in dts.values()))

h("C10  window offers: label vs hours")
w = collections.Counter()
for v in calls.values():
    for s, t in v["turns"]:
        if s == "Agent":
            m = re.search(r"i have a (morning|afternoon) window [a-z]+,? (\d+) to (\d+)", t.lower().replace("um, ", ""))
            if m: w[(m.group(1), f"{m.group(2)}-{m.group(3)}")] += 1
print(dict(w), "| label contradicts hours:", sum(n for (lab, hrs), n in w.items() if (lab == "morning" and hrs != "8-12") or (lab == "afternoon" and hrs == "8-12")), "of", sum(w.values()))
req = sum(1 for k in book if re.search(r"4 to 7", CU(calls[k]))); print("booking callers who asked for 4-to-7pm:", req, "| offered a 16:00-19:00 window:", sum(1 for k in book if re.search(r"window [a-z]+,? 4 to 7", AG(calls[k]).lower())))

h("C11  identity step")
meth = collections.Counter()
for k in calls:
    a = re.sub(r"\b(um|uh),? ?", "", AG(calls[k]).lower()).replace(",", "")
    for lbl, rx in (("account number + name", r"account number handy"), ("name + phone", r"name and the phone number"), ("name + service address", r"name and service address")):
        if re.search(rx, a): meth[lbl] += 1
print(dict(meth), "| calls with at least one identity step:", sum(1 for r in rows.values() if "E-IDENT" in r["events"]), "| none:", sum(1 for r in rows.values() if "E-IDENT" not in r["events"]))
print("categories with no identity step:", dict(collections.Counter(r["initial"] for r in rows.values() if "E-IDENT" not in r["events"])))

h("C12  topics checked and ABSENT from customers' words (all 420 calls)")
cust = {k: CU(v).lower() for k, v in calls.items()}
for name, rx in {"password / login / account access": r"password|log ?in|username|locked out", "financing": r"financ|payment plan", "business hours / are you open": r"are you open|what time do you|hours", "holiday hours": r"holiday|thanksgiving|christmas|labor day|july 4", "service area / zip / named excluded city": r"service area|do you (service|serve)|zip code|san marcos|bastrop|lakeway|dripping|manor", "duct cleaning": r"duct", "legal threat / chargeback": r"attorney|lawyer|\bsue\b|chargeback|legal", "late-cancel / no-show fee": r"no.show|late cancel", "diagnostic fee question": r"diagnostic", "heat/cold urgency or vulnerable occupant": r"degrees|hot in|freezing|elderly|baby|infant|medical", "customer asks to call back / voicemail": r"call me back|voicemail"}.items():
    print(f"  {name}: {sum(1 for t in cust.values() if re.search(rx, t))} calls")
