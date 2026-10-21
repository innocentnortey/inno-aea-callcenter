"""Rule-based classification of all 420 Meridian transcripts for the handoff-information inventory.

Reproduce:  python3 -I classify_calls.py  (run from this folder; reads the issued dataset read-only,
writes call_classification.csv and prints the summary tables used in the report).

Three layers, in this order:
  1. INITIAL NEED  - first substantive customer turn (noise turns skipped) matched to one category.
  2. EVENTS        - what the agent said/did anywhere in the call (lookups, actions, promises, hand-offs).
  3. EMERGENT      - escalation-type events that the initial need does not imply (dispute, manager, safety).
The classifier is deliberately simple; every rule was written after reading template exemplars, and the
report lists the manual checks. A call that matches no rule raises, so nothing is silently dropped.
"""
import sys, os, re, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_calls import load, norm

NOISE = re.compile(r"^(um,? )?(sorry,? (you cut out|i'?m driving)|can you hear me|hold on,? my dog|um,?$|hm+,? okay)", re.I)
def is_noise(t):
    n = re.sub(r"[^a-z' ,]", "", t.lower()).strip()
    return bool(NOISE.match(n)) or n in ("sorry, you cut out for a second", "um")

# (category id, label, regex on lower-cased opening request)  - first match wins, order matters
INITIAL_RULES = [
    ("SAF-GAS",  r"smell gas"),
    ("SAF-CO",   r"carbon monoxide"),
    ("SAF-SPARK",r"sparks"),
    ("WRONG-NO", r"meridian dental"),
    ("HIRING",   r"hiring"),
    ("COMMERCIAL", r"strip center|rooftop units"),
    ("COMPLAINT-REPEAT", r"called three times"),
    ("COMPLAINT-CONDUCT", r"talk to a manager|rude"),
    ("COMPLAINT-OPINION", r"second opinion"),
    ("BILL-REFUND", r"full refund"),
    ("BILL-DISPUTE", r"tech quoted me"),
    ("BILL-DUP", r"charged twice"),
    ("BILL-EXPLAIN", r"not sure what it'?s for"),
    ("BILL-BALANCE", r"current balance"),
    ("BILL-PAY", r"pay invoice"),
    ("BILL-AUTOPAY", r"autopay"),
    ("MEM-CANCEL", r"cancel my comfort club"),
    ("MEM-RENEW", r"membership is renewing"),
    ("MEM-INCLUDE", r"membership actually include"),
    ("MEM-PRICE", r"how much is the maintenance plan"),
    ("MEM-UPGRADE", r"upgrade from"),
    ("MEM-DISCOUNT", r"discount on a new system"),
    ("MULTI-REPAIR-PLAN", r"two things"),
    ("WAR-CLAIM", r"file a warranty claim"),
    ("WAR-REPEAT", r"labor warranty cover a repeat"),
    ("WAR-PARTS", r"compressor died"),
    ("WAR-TRANSFER", r"warranty transfer"),
    ("WAR-REGISTER", r"register my new unit"),
    ("SCH-LATE", r"nobody'?s here"),
    ("SCH-CANCEL", r"cancel my appointment"),
    ("SCH-CONFIRM", r"confirm i still have someone"),
    ("SCH-RESCHED", r"can i move it"),
    ("EST-REPLACE", r"thinking about replacing"),
    ("SCH-BURNING", r"burning from the,? vents"),
    ("SCH-TUNEUP", r"annual tune-?up"),
    ("SCH-PLUMB", r"sink is backing up|pilot light"),
    ("SCH-HVAC", r"isn'?t cooling|air is warm|won'?t kick on|thermostat is blank|water pooling|grinding noise"),
]
LABELS = {
 "SAF-GAS":"Safety: gas smell","SAF-CO":"Safety: CO detector alarm","SAF-SPARK":"Safety: sparks from unit",
 "WRONG-NO":"Wrong number","HIRING":"Employment inquiry","COMMERCIAL":"Commercial project quote",
 "COMPLAINT-REPEAT":"Complaint: repeated unreturned calls","COMPLAINT-CONDUCT":"Complaint: technician conduct (manager requested)",
 "COMPLAINT-OPINION":"Complaint: second opinion contradicts recommended repair",
 "BILL-REFUND":"Billing: refund demand","BILL-DISPUTE":"Billing: quote vs invoice dispute","BILL-DUP":"Billing: duplicate charge",
 "BILL-EXPLAIN":"Billing: explain an invoice","BILL-BALANCE":"Billing: balance inquiry","BILL-PAY":"Billing: pay an invoice",
 "BILL-AUTOPAY":"Billing: set up autopay","MEM-CANCEL":"Membership: cancel","MEM-RENEW":"Membership: renewal date/charge",
 "MEM-INCLUDE":"Membership: what is included","MEM-PRICE":"Membership: price","MEM-UPGRADE":"Membership: upgrade to Plus",
 "MEM-DISCOUNT":"Membership: discount on new system","MULTI-REPAIR-PLAN":"Two-part: book repair + ask if plan saves money",
 "WAR-CLAIM":"Warranty: file claim on install","WAR-REPEAT":"Warranty: repeat repair","WAR-PARTS":"Warranty: compressor / parts coverage",
 "WAR-TRANSFER":"Warranty: transfer to new homeowner","WAR-REGISTER":"Warranty: manufacturer registration",
 "SCH-LATE":"Scheduling: technician late / missed window","SCH-CANCEL":"Scheduling: cancel appointment",
 "SCH-CONFIRM":"Scheduling: confirm appointment","SCH-RESCHED":"Scheduling: reschedule appointment",
 "EST-REPLACE":"Replacement estimate (system sales)","SCH-BURNING":"Book repair: burning smell from vents (safety-ambiguous)",
 "SCH-TUNEUP":"Book: annual tune-up","SCH-PLUMB":"Book: plumbing repair","SCH-HVAC":"Book: HVAC repair",
}
def first_request(call):
    cust = [t for s, t in call["turns"] if s == "Customer"]
    for t in cust:
        if not is_noise(t):
            return t
    raise ValueError(call["id"])
def initial_category(call):
    req = first_request(call).lower().replace("’", "'")
    req = re.sub(r"\b(um|uh),? ?", "", req)   # strip STT filler words before matching
    for cid, rx in INITIAL_RULES:
        if re.search(rx, req):
            return cid
    raise ValueError(f"unclassified {call['id']}: {req}")

AG = lambda c: [t for s, t in c["turns"] if s == "Agent"]
CU = lambda c: [t for s, t in c["turns"] if s == "Customer"]
EVENT_RULES = [  # (event id, regex on agent turns, joined)
 ("E-SAFETY-INSTR", r"leave the house right now"),
 ("E-PRIORITY-NOTE", r"priority note on your account"),
 ("E-IDENT-NAME-PHONE", r"name and the phone number"),
 ("E-IDENT-ACCT-NAME", r"account number handy"),
 ("E-IDENT-NAME-ADDR", r"name and service address"),
 ("E-SCHEDULE-OFFER", r"i have a (morning|afternoon) window|advisor available"),
 ("E-BOOKED", r"you'?re booked|done\. i have|yes let me book|i'll book a warranty"),
 ("E-WAITLIST", r"waitlist"),
 ("E-RESCHEDULED", r"\bmoved\b"),
 ("E-CANCEL-DONE", r"no cancellation fee"),
 ("E-PAYLINK", r"secure (payment )?link|it'll come by text|sent\. you should"),
 ("E-EMAIL-COPY", r"sending that to the email on file"),
 ("E-AUTORENEW-OFF", r"auto-?renew is off"),
 ("E-UPGRADED", r"you'?re upgraded"),
 ("E-MEMBER-ADDED", r"want me to add it"),
 ("E-WARRANTY-BOOK", r"warranty diagnostic at no charge|warranty recall"),
 ("E-FEE-WAIVED", r"fee is waived for the delay"),
 ("E-REGISTRATION-CLAIM", r"i see it was registered on"),
 ("E-XFER-FORM", r"transfer form"),
 ("E-BALANCE-READ", r"open balance of"),
 ("E-INVOICE-LINES", r"from the service visit|difference is the"),
 ("E-PENDING-HOLD", r"two authorizations"),
 ("E-TERM-READ", r"your term ends"),
 ("E-PROMISE-1BD-BILLING", r"billing supervisor to review and they'?ll call you back within one business day"),
 ("E-PROMISE-TODAY-MGR", r"she'?ll call you back today"),
 ("E-PROMISE-2BD-REFUND", r"within two business days"),
 ("E-PROMISE-1BD-COMMERCIAL", r"estimator call you|someone will reach out within one business day"),
 ("E-CAREERS-REDIRECT", r"careers page"),
 ("E-PASS-ALONG", r"pass along that you called"),
 ("E-TECH-CALL", r"have him call you directly"),
 ("E-RANGE-QUOTE", r"\$8000 and \$16000|typically \$600"),
 ("E-LABOR-BILLABLE", r"labor would be billable"),
]
def events(call):
    a = " ".join(AG(call)).lower().replace("’", "'")
    a = re.sub(r"\b(um|uh),? ?", "", a)          # strip STT filler so phrases match across noise
    a = a.replace(",", "")                        # ...and the stray commas it leaves ("the, phone number")
    return [e for e, rx in EVENT_RULES if re.search(rx, a)]

def customer_flags(call):
    cu = " ".join(CU(call)).lower()
    fl = []
    if re.search(r"nobody told me about that", cu): fl.append("C-UNVERIFIED-CLAIM-NOT-TOLD")
    if re.search(r"that'?s not what i agreed to", cu): fl.append("C-UNVERIFIED-CLAIM-QUOTE")
    if re.search(r"today\. not next week", cu): fl.append("C-DEMANDS-TODAY")
    if re.search(r"i'?d better", cu): fl.append("C-DOUBTS-PROMISE")
    if re.search(r"let me think about it", cu): fl.append("C-UNDECIDED")
    if re.search(r"can you do anything earlier", cu): fl.append("C-WANTS-EARLIER")
    if re.search(r"(attorney|lawyer|sue |chargeback|legal)", cu): fl.append("C-LEGAL-THREAT")
    if re.search(r"i'?m a member", cu): fl.append("C-CLAIMS-MEMBER")
    return fl

NOISE_PAT = {"driving": r"i'?m driving", "cutout": r"you cut out", "hear": r"can you hear me", "dog": r"my dog is barking"}
def noise_tags(call):
    cu = " ".join(CU(call)).lower().replace("’", "'")
    return [k for k, rx in NOISE_PAT.items() if re.search(rx, cu)]

def template_key(call):
    """Collapse wrappers so that 'book a repair / schedule a service call / hi...' variants of one symptom share a key."""
    req = norm(first_request(call))
    req = re.sub(r"\b(um|uh)\b ?", "", req)
    req = re.sub(r"\b(yeah i need to schedule a service call|im calling to book a repair|hey so|hi|and id like to get someone out to look at it|whats the soonest you can get a tech out)\b", "", req)
    return re.sub(r"\s+", " ", req).strip()

def main(outdir=None):
    calls = load()
    rows = []
    for cid, c in sorted(calls.items()):
        cat = initial_category(c)
        rows.append(dict(call_id=cid, initial=cat, events="|".join(events(c)),
            flags="|".join(customer_flags(c)), noise="|".join(noise_tags(c)),
            template=template_key(c), n_turns=len(c["turns"]),
            duration=c["head"].get("Duration", ""), agent=c["head"].get("Agent", "")))
    out = os.path.join(outdir or os.path.dirname(os.path.abspath(__file__)), "call_classification.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows
# ---------------------------------------------------------------------------------------------
# Extensions: driver families, evidence-based support level, secondary requests, summary printer
# ---------------------------------------------------------------------------------------------
FAMILY = {
 "SCH-HVAC":"F1 New service booking","SCH-PLUMB":"F1 New service booking","SCH-TUNEUP":"F1 New service booking","SCH-BURNING":"F1 New service booking",
 "SCH-RESCHED":"F2 Existing-appointment management","SCH-CONFIRM":"F2 Existing-appointment management","SCH-CANCEL":"F2 Existing-appointment management","SCH-LATE":"F2 Existing-appointment management",
 "BILL-BALANCE":"F3 Billing information and payments","BILL-PAY":"F3 Billing information and payments","BILL-AUTOPAY":"F3 Billing information and payments","BILL-EXPLAIN":"F3 Billing information and payments","BILL-DUP":"F3 Billing information and payments",
 "BILL-DISPUTE":"F4 Billing disputes and refunds","BILL-REFUND":"F4 Billing disputes and refunds",
 "MEM-CANCEL":"F5 Comfort Club membership","MEM-RENEW":"F5 Comfort Club membership","MEM-INCLUDE":"F5 Comfort Club membership","MEM-PRICE":"F5 Comfort Club membership","MEM-UPGRADE":"F5 Comfort Club membership","MEM-DISCOUNT":"F5 Comfort Club membership",
 "WAR-CLAIM":"F6 Warranty","WAR-REPEAT":"F6 Warranty","WAR-PARTS":"F6 Warranty","WAR-TRANSFER":"F6 Warranty","WAR-REGISTER":"F6 Warranty",
 "EST-REPLACE":"F7 System-replacement estimate",
 "COMPLAINT-REPEAT":"F8 Service complaints","COMPLAINT-CONDUCT":"F8 Service complaints","COMPLAINT-OPINION":"F8 Service complaints",
 "SAF-GAS":"F9 Safety","SAF-CO":"F9 Safety","SAF-SPARK":"F9 Safety",
 "COMMERCIAL":"F10 Out of residential scope","HIRING":"F10 Out of residential scope","WRONG-NO":"F10 Out of residential scope",
 "MULTI-REPAIR-PLAN":"F11 Two-part request (booking + membership)",
}
# Evidence-based CANDIDATE support level (proposal, not an approved scope): what the issued KB + DB can support.
SUPPORT = {
 "KB-only":["MEM-INCLUDE","MEM-PRICE","MEM-DISCOUNT","WAR-TRANSFER","HIRING","WRONG-NO"],
 "DB read + KB":["BILL-BALANCE","BILL-EXPLAIN","SCH-CONFIRM","MEM-RENEW","WAR-CLAIM","WAR-PARTS"],
 "DB write (booking) + KB":["SCH-HVAC","SCH-PLUMB","SCH-TUNEUP","SCH-RESCHED","SCH-CANCEL","EST-REPLACE","MULTI-REPAIR-PLAN"],
 "Person required by policy":["BILL-DISPUTE","BILL-REFUND","COMPLAINT-REPEAT","COMPLAINT-CONDUCT","COMPLAINT-OPINION","COMMERCIAL","SCH-LATE"],
 "Safety protocol (instruction first, then flag)":["SAF-GAS","SAF-CO","SAF-SPARK"],
 "Needs a system the issued materials lack":["BILL-PAY","BILL-AUTOPAY","MEM-CANCEL","MEM-UPGRADE","BILL-DUP","WAR-REGISTER","WAR-REPEAT"],
 "Policy gap (KB silent)":["SCH-BURNING"],
}
SUPPORT_OF = {c: k for k, v in SUPPORT.items() for c in v}
SECONDARY_RULES = [  # (secondary id, categories it can attach to, regex on later customer turns)
 ("SEC-SCHEDULE-REQUEST", {"WAR-PARTS","WAR-REPEAT","MULTI-REPAIR-PLAN"}, r"let'?s schedule it|can you get someone out|book the visit"),
 ("SEC-PRICE-QUESTION",   {"MEM-INCLUDE","WAR-PARTS"}, r"how much is (it|labor)"),
 ("SEC-COVERAGE-QUESTION",{"MEM-INCLUDE"}, r"does it cover plumbing"),
 ("SEC-CANCEL-QUESTION",  {"MEM-RENEW"}, r"can still cancel"),
 ("SEC-COPY-REQUEST",     {"BILL-EXPLAIN"}, r"email me an itemized copy"),
 ("SEC-EARLIER-SLOT",     {"SCH-HVAC","SCH-PLUMB","SCH-TUNEUP","SCH-BURNING"}, r"anything earlier"),
 ("SEC-OLD-PRICE-CLAIM",  {"MEM-PRICE"}, r"i thought it was"),
 ("SEC-NOT-TOLD-CLAIM",   {"BILL-DISPUTE"}, r"nobody told me"),
]
def secondary(call, cat):
    cu = " ".join(CU(call)[1:]).lower().replace("’", "'")
    return [sid for sid, cats, rx in SECONDARY_RULES if cat in cats and re.search(rx, cu)]
STRICT_MULTI = {"MULTI-REPAIR-PLAN", "WAR-PARTS", "WAR-REPEAT"}   # second request in a different family

def enrich(rows, calls):
    for r in rows:
        r["family"] = FAMILY[r["initial"]]
        r["support_level"] = SUPPORT_OF[r["initial"]]
        r["secondary"] = "|".join(secondary(calls[r["call_id"]], r["initial"]))
        r["phone_spoken"] = int(bool(re.search(r"\d{3}-\d{3}-\d{4}", calls[r["call_id"]]["text"])))
    return rows

def summary(rows):
    n = len(rows); cnt = collections.Counter(r["initial"] for r in rows)
    fam = collections.Counter(r["family"] for r in rows)
    print(f"\n== FAMILIES (denominator {n})")
    for k, v in sorted(fam.items(), key=lambda x: -x[1]): print(f"{v:4d} {v/n:6.1%} {k}")
    print("\n== SUPPORT LEVEL (candidate, by primary category)")
    sl = collections.Counter(r["support_level"] for r in rows)
    for k, v in sorted(sl.items(), key=lambda x: -x[1]): print(f"{v:4d} {v/n:6.1%} {k}")
    print("\n== SECONDARY REQUESTS (mentions)")
    sc = collections.Counter(s for r in rows for s in r["secondary"].split("|") if s)
    for k, v in sc.most_common(): print(f"{v:4d} {k}")
    sm = [r for r in rows if r["initial"] in STRICT_MULTI]
    print("strict multi-request calls:", len(sm), f"{len(sm)/n:.1%}")
    print("\n== EVENTS")
    ev = collections.Counter(e for r in rows for e in r["events"].split("|") if e)
    for k, v in sorted(ev.items()): print(f"{v:4d} {k}")
    print("\n== PHONE NUMBER SPOKEN IN CALL, handoff-type categories")
    for cat in ["SAF-GAS","SAF-CO","SAF-SPARK","BILL-DISPUTE","BILL-REFUND","COMPLAINT-REPEAT","COMPLAINT-CONDUCT","COMPLAINT-OPINION","COMMERCIAL","SCH-LATE"]:
        rs = [r for r in rows if r["initial"] == cat]
        print(f"  {cat:20s} {sum(r['phone_spoken'] for r in rs)}/{len(rs)}")
    sig = collections.Counter(tuple(e for e in r["events"].split("|") if e and not e.startswith("E-IDENT")) for r in rows)
    print("\ndistinct agent-side signatures:", len(sig), "| distinct collapsed opening templates:", len({r['template'] for r in rows}))

if __name__ == "__main__":
    calls = load()
    rows = enrich(main(), calls)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "handoff-inventory-call-map.csv")
    keep = ["call_id","family","initial","support_level","secondary","events","flags","noise","phone_spoken","template","n_turns","duration","agent"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keep, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    summary(rows)
