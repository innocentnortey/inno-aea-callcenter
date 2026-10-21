import { useEffect, useId } from "react";
import { Link } from "react-router";
import type { components } from "@/api/types.gen";
import { useAnnounce } from "@/components/ui/LiveRegion";
import { caseHref } from "@/routes";
import { pluralize } from "../reads/format";

type Owner = components["schemas"]["OwnerMetricsResponse"];

export function OpenCases({ id, title, refs, cases }: { id: string; title: string; refs: string[]; cases: Owner["cases"] }) {
  const announce = useAnnounce();
  const headId = useId();
  useEffect(() => {
    announce(`${refs.length} ${pluralize(refs.length, "case", "cases")} listed.`);
    // announce once per opened list (the component is keyed by the list)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <section id={id} aria-labelledby={headId} className="rounded-card border border-border-hair bg-surface-well p-3">
      <h3 id={headId} className="t-card-title mb-2">{title}</h3>
      <ul className="flex flex-col gap-1 text-ui">
        {refs.map((ref) => {
          const c = cases.find((x) => x.reference === ref);
          return (
            <li key={ref}>
              <Link to={caseHref(ref)} className="t-ref link-text">{ref}</Link>
              {c ? ` · ${c.reason} · ${c.status}` : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
