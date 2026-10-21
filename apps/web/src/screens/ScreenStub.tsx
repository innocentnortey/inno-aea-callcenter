import { useEffect } from "react";
import { useParams } from "react-router";
import { screenById, type ScreenId } from "@/routes";
import { AppFrame } from "@/components/shell/AppFrame";
import { ConsoleHeader, DemoBar, DemoPageHeader, Main } from "@/components/shell/chrome";
import { RoleGate } from "@/components/shell/RoleGate";
import { RoleSwitch } from "@/components/shell/RoleSwitch";
import { realStates } from "./matrix";

/** Stands in for a screen until its group builds it: ids, route and state names only, no data. */
export function ScreenStub({ id }: { id: ScreenId }) {
  const def = screenById(id);
  const params = useParams();
  const states = realStates(id);
  useEffect(() => { document.title = `${def.id} · ${def.title} · Meridian`; }, [def]);

  const body = (
    <>
      <p>Stub: this screen is built by {def.group}.</p>
      <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-ui">
        <dt className="text-text-muted">Route</dt>
        <dd className="t-ref">{def.path}</dd>
        {params.reference ? (<><dt className="text-text-muted">Reference</dt><dd className="t-ref">{params.reference}</dd></>) : null}
        <dt className="text-text-muted">Real states</dt>
        <dd>{states.join(", ")}</dd>
      </dl>
    </>
  );
  const heading = <h1 className="t-title">{def.id} {"·"} {def.title}</h1>;

  return (
    <AppFrame variant={def.frame}>
      {def.frame === "console" ? <ConsoleHeader /> : null}
      {def.frame === "page" ? <DemoPageHeader title={def.title} /> : null}
      {def.frame === "chat" ? (<header><DemoBar /><div className="px-4 py-2"><RoleSwitch variant="row" /></div></header>) : null}
      <Main className="p-4">
        {heading}
        {def.frame === "console" ? <RoleGate allow={def.roles}>{body}</RoleGate> : body}
      </Main>
    </AppFrame>
  );
}
