// Static copy written from docs/design/key-metrics-registry.md (volume, tool and model failure rate, latency, spend,
// live AI-resolved rate). It describes what each measure counts; it never holds a number.
export const DEFINITIONS: { heading: string; items: { term: string; text: string }[] }[] = [
  {
    heading: "Health",
    items: [
      { term: "Conversations", text: "Live conversations started since the last reset. Tests and load runs are not counted." },
      { term: "Turns", text: "Customer messages the assistant replied to." },
      { term: "Failures", text: "Turns that ended in a handoff because of a model error, a tool error or a timeout, out of all turns. Retried rate-limit responses are counted apart." },
      { term: "Latency p50 and p95", text: "How long a customer waits for a reply, measured on live turns. p50 is the typical turn; p95 is the slowest 1 in 20. Shown once at least 20 turns exist." },
      { term: "Spend today", text: "Model-call cost since midnight Austin time, against the $30 daily cap. At the cap, new chats hand off and no model calls run until tomorrow." },
      { term: "Last restart", text: "The last time the health check restarted the service." },
      { term: "Trace export", text: "How many turns have had their trace sent. Traces themselves are never shown here." },
    ],
  },
  {
    heading: "Correctness",
    items: [
      { term: "Containment estimate", text: "An estimate, not a measured number: live conversations that ended resolved by the assistant and were not flagged wrong by staff, out of live conversations on a handled topic. The measured number is on the Evaluation page." },
      { term: "Escalations by reason", text: "Conversations handed to a person, grouped by the reason on the case." },
    ],
  },
];
