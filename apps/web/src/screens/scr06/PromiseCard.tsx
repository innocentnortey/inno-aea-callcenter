import type { components } from "@/api/types.gen";
import { Card, CardBody, CardHeader, CardRow, Disclosure, IconQuote, Tag } from "@/components/ui";
import { Time } from "@/components/shared/Time";
import { bestTimeLabel, channelLabel, PROMISE_STATUS_LABEL } from "./caseText";

type Promise_ = components["schemas"]["PromiseRecord"];

export function PromiseCard({ promise }: { promise: Promise_ }) {
  const f = promise.follow_up;
  const last = promise.history.at(-1);
  return (
    <Card aria-labelledby="promise-h">
      <CardHeader as="h2" icon={<IconQuote size={16} strokeWidth={1.8} aria-hidden="true" />} title={<span id="promise-h">Promise shown to the customer</span>} meta={<Tag tone="strong">{PROMISE_STATUS_LABEL[promise.status]}</Tag>} />
      <CardBody>
        <p className="t-lead">{promise.text}</p>
        {promise.status === "changed" && last ? <p className="mt-2 text-ui">Changed: {last.reason}</p> : null}
        <div className="mt-2">
          <CardRow label="Due"><Time iso={promise.due_at} format="short" fallback={promise.due_label ?? ""} /></CardRow>
          <CardRow label="Follow up by">{f ? channelLabel(f.channel) : "Not chosen yet"}</CardRow>
          <CardRow label="Destination">
            {f ? <span className="inline-flex flex-wrap items-center justify-end gap-2">{f.destination_label}<Tag>{f.on_record ? "On record" : "Not on record"}</Tag></span> : "Not chosen yet"}
          </CardRow>
          <CardRow label="Best time">{bestTimeLabel(f ? f.window : null)}</CardRow>
        </div>
        {promise.history.length > 0 ? (
          <Disclosure summary={<span className="text-ui font-semibold">History ({promise.history.length})</span>}>
            <ul className="flex flex-col gap-1 pb-2 text-ui">
              {promise.history.map((h, i) => (
                <li key={i}><Time iso={h.at} format="short" /> {"·"} {h.text} ({h.reason})</li>
              ))}
            </ul>
          </Disclosure>
        ) : null}
      </CardBody>
    </Card>
  );
}
