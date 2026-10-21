import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router";
import * as Tabs from "@radix-ui/react-tabs";
import { AppFrame } from "@/components/shell/AppFrame";
import { ConsoleHeader, Main } from "@/components/shell/chrome";
import { RoleGate } from "@/components/shell/RoleGate";
import { EmptyState, ErrorLine, StaleLine } from "@/components/shared/states";
import { Button, IconBack, Skeleton } from "@/components/ui";
import { HOME_BY_ROLE } from "@/lib/roles";
import { screenById } from "@/routes";
import { useDemoStatus } from "@/state/demoStatus";
import { useSession } from "@/state/session";
import { ActionArea, barFormKey, type FormKey } from "./ActionArea";
import { ActionResult } from "./ActionResult";
import { ActivityLog } from "./ActivityLog";
import { planActions, type BarKey, type MenuKey } from "./actionPlan";
import { AssignForm, CloseForm, ContactForm, FlagForm, PriorityForm, ReleaseForm, ResolveForm, WaitForm, type FormProps } from "./ActionForms";
import { BriefView } from "./BriefView";
import { CaseHeader } from "./CaseHeader";
import { EvidenceColumn, type EvidenceTab } from "./EvidenceColumn";
import { LifecycleLine } from "./LifecycleLine";
import { PromiseCard } from "./PromiseCard";
import { RailColumn } from "./RailColumn";
import { useCase } from "./useCase";
import { RESULT_ID, useCaseActions } from "./useCaseActions";
import { useCaseStream } from "./useCaseStream";
import { useMediaQuery } from "./useMediaQuery";

function CaseSkeleton({ reference }: { reference: string | undefined }) {
  return (
    <div className="flex flex-col gap-3 p-4" aria-busy="true">
      <h1 className="sr-only">Case {reference}</h1>
      <Skeleton height={96} />
      {Array.from({ length: 8 }, (_, i) => <Skeleton key={i} height={96} />)}
    </div>
  );
}

function CaseBody() {
  const { reference } = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { role } = useSession();
  const { clock } = useDemoStatus();
  const c = useCase(reference);
  useCaseStream(reference, !!c.state.detail, c.dispatch);
  const detail = c.state.detail;
  const r = role ?? "representative";
  const act = useCaseActions({ reference, state: c.state, dispatch: c.dispatch, reload: c.reload, role: r });
  const phone = useMediaQuery("(max-width: 699px)", false);
  const reduced = useMediaQuery("(prefers-reduced-motion: reduce)", false);
  const narrow = useMediaQuery("(max-width: 1099px)", false);
  const [tab, setTab] = useState<EvidenceTab>(search.get("tab") === "conversation" ? "conversation" : "sources");
  const [phoneTab, setPhoneTab] = useState<"brief" | "evidence">("brief");
  const [highlight, setHighlight] = useState<string | null>(null);
  const focusMessage = search.get("message");

  const joined = detail?.live.state === "joined";
  useEffect(() => { if (joined) setTab("conversation"); }, [joined]);
  // Once per (case, message): depending on `!!detail`, not `detail`, so later case updates never re-force the tabs.
  const hasDetail = !!detail;
  useEffect(() => {
    if (!focusMessage || !hasDetail) return;
    setTab("conversation");
    setPhoneTab("evidence");
    const t = setTimeout(() => {
      const el = document.getElementById(`msg-${focusMessage}`);
      el?.scrollIntoView?.({ block: "center" });
      el?.focus({ preventScroll: true });
    }, 50);
    return () => clearTimeout(t);
  }, [focusMessage, hasDetail]);

  const onJump = (id: string) => {
    setTab("sources");
    setPhoneTab("evidence");
    setTimeout(() => {
      const el = document.getElementById(`src-${id}`);
      el?.scrollIntoView?.({ block: "nearest", behavior: reduced ? "auto" : "smooth" });
      el?.focus();
      setHighlight(id);
      setTimeout(() => setHighlight(null), 1200);
    }, 0);
  };

  const rail = role === "representative" || role === "supervisor";
  const railNode = rail ? (
    <nav aria-label="Queue" id="queue-rail" className="border-b border-border-hair p-4 min-[1100px]:border-b-0 min-[1100px]:border-r">
      <RailColumn currentRef={reference} collapsible={narrow} />
    </nav>
  ) : null;
  const home = rail ? "/staff/queue" : HOME_BY_ROLE.owner;
  const back = (
    <Link to={home} onClick={(e) => { if (location.key !== "default") { e.preventDefault(); navigate(-1); } }} className="link-text inline-flex items-center gap-1 text-ui">
      <IconBack size={16} strokeWidth={1.8} aria-hidden="true" />{rail ? "Back to queue" : "Back"}
    </Link>
  );

  let main: React.ReactNode;
  let evidence: React.ReactNode = null;
  if (!reference) {
    main = <><h1 className="sr-only">Case view</h1><EmptyState title="Pick a case from the queue." /></>;
  } else if (c.error?.code === "CASE_NOT_FOUND") {
    main = (
      <div className="flex flex-col gap-2 p-4">
        <h1 className="t-title">Case not found</h1>
        <p className="text-body">No case {reference}. It may have been cleared by a demo reset.</p>
        <div><Button variant="secondary" density="console" onClick={() => navigate("/staff/queue")}>Back to the queue</Button></div>
      </div>
    );
  } else if (c.error && !detail) {
    main = <div className="p-4"><h1 className="sr-only">Case {reference}</h1><ErrorLine message="The case didn't load. Try again." onRetry={() => void c.reload()} /></div>;
  } else if (!detail) {
    main = <CaseSkeleton reference={reference} />;
    evidence = <div className="p-4"><Skeleton height={240} /></div>;
  } else {
    const plan = planActions(detail, r);
    const nowIso = clock?.now ?? detail.as_of;
    const onBar = (k: BarKey) => (k === "join_chat" ? void act.joinChat() : act.setForm(barFormKey(k)));
    const onMenu = (k: MenuKey) => (k === "start" ? void act.startNow() : act.setForm(k));
    const onPrimary = () => {
      const kind = plan.primary?.kind;
      if (kind === "claim") void act.claimNow();
      else if (kind === "claim_and_join") void act.claimAndJoinNow();
      else if (kind === "start") void act.startNow();
      else if (kind === "resolve") act.setForm("resolve");
    };
    const fp: FormProps = { onSubmit: (s) => void act.submit(s), onCancel: () => act.setForm(null), busy: act.busy, version: act.version };
    const lastAssistant = [...c.state.messages].reverse().find((m) => m.speaker.kind === "assistant")?.message_id ?? null;
    const forms: Record<FormKey, React.ReactNode> = {
      release: <ReleaseForm {...fp} />, wait: <WaitForm {...fp} nowIso={nowIso} />, resolve: <ResolveForm {...fp} />, close_unresolved: <CloseForm {...fp} />,
      log_call: <ContactForm {...fp} kind="call" />, log_email: <ContactForm {...fp} kind="email" />,
      flag: <FlagForm {...fp} reference={detail.case.reference} lastAssistantMessageId={lastAssistant} />,
      assign: <AssignForm {...fp} />, change_priority: <PriorityForm {...fp} />,
    };
    main = (
      <div className="flex flex-col gap-4 p-4">
        {back}
        <CaseHeader detail={detail} nowIso={nowIso} plan={plan} onPrimary={onPrimary} onMenu={onMenu} busy={act.busy} />
        <LifecycleLine lifecycle={detail.case.lifecycle} staffedPath={detail.case.lifecycle === "live_queued" || detail.live.state !== "not_live"} />
        {c.state.changedElsewhere ? <StaleLine actionLabel="Reload" onAction={() => void c.reload()}>This case changed. Show the latest.</StaleLine> : null}
        <PromiseCard promise={detail.promise} />
        <BriefView brief={detail.brief} sources={detail.sources} onJump={onJump} />
        <ActionArea
          plan={plan} onBar={onBar} form={act.form ? forms[act.form] : null}
          error={act.error} onReload={() => { act.clearError(); void c.reload(); }}
          result={act.result ? <ActionResult id={RESULT_ID}>{act.result}</ActionResult> : null}
          log={<ActivityLog activities={detail.activities} />}
        />
      </div>
    );
    evidence = (
      <EvidenceColumn
        sources={detail.sources} asOf={detail.as_of} highlight={highlight} tab={tab} onTab={setTab} otherCases={detail.other_cases}
        conversation={{
          messages: c.state.messages, events: c.state.events, focusMessage,
          liveBox: plan.liveBox === "hidden" ? null : {
            mode: plan.liveBox, ownerName: detail.case.owner, onSend: (t) => act.liveSend(t), onHandBack: () => void act.liveEnd("hand_back"),
            onClose: () => void act.liveEnd("close"), error: act.liveError, endedByReset: c.state.endedByReset, busy: act.busy,
          },
        }}
      />
    );
  }

  return (
    <div className="flex flex-col min-[1100px]:grid min-[1100px]:grid-cols-[var(--col-queue)_minmax(0,1fr)_var(--col-evidence)]">
      {rail ? <a href="#queue-rail" className="skip-link">Go to queue</a> : null}
      {railNode}
      {phone && evidence ? (
        <Tabs.Root value={phoneTab} onValueChange={(v) => setPhoneTab(v as "brief" | "evidence")}>
          <Tabs.List aria-label="Case sections" className="flex border-b border-border-hair">
            <Tabs.Trigger value="brief" className="min-h-[var(--target-min)] flex-1 text-ui font-semibold data-[state=active]:border-b-2">Brief</Tabs.Trigger>
            <Tabs.Trigger value="evidence" className="min-h-[var(--target-min)] flex-1 text-ui font-semibold data-[state=active]:border-b-2">Evidence</Tabs.Trigger>
          </Tabs.List>
          <Tabs.Content value="brief">{main}</Tabs.Content>
          <Tabs.Content value="evidence">{evidence}</Tabs.Content>
        </Tabs.Root>
      ) : (
        <>
          <div className="min-w-0">{main}</div>
          {evidence ? <div className="border-t border-border-hair min-[1100px]:border-l min-[1100px]:border-t-0">{evidence}</div> : null}
        </>
      )}
    </div>
  );
}

export default function Scr06() {
  const def = screenById("SCR-6");
  const { reference } = useParams();
  const { role } = useSession();
  useEffect(() => { document.title = `${def.id} · ${def.title} · Meridian`; }, [def]);
  const blocked = role !== null && !def.roles.includes(role); // the role panel has no heading of its own; CaseBody supplies the h1 otherwise
  return (
    <AppFrame variant="console">
      <ConsoleHeader />
      <Main>
        {blocked ? <h1 className="sr-only">Case {reference}</h1> : null}
        <RoleGate allow={def.roles}>
          <CaseBody key={reference ?? "none"} />
        </RoleGate>
      </Main>
    </AppFrame>
  );
}
