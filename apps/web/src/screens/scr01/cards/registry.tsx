import type { RendererMap } from "../contract";
import { AccountCard } from "./AccountCard";
import { BurningCheckCard, QuickChecksCard, UrgencyQuestionsCard } from "./ChoiceCards";
import { ChangeRequestCard } from "./ChangeRequestCard";
import { CodePromptCard } from "./CodePromptCard";
import { EmergencyLineCard } from "./EmergencyLineCard";
import { ErrorCard } from "./ErrorCard";
import { HandoffCard } from "./HandoffCard";
import { LiveQueuedCard } from "./LiveQueuedCard";
import { LocatePromptCard } from "./LocatePromptCard";
import { FailureOfferCard, NoInfoCard, NoticeCard } from "./NoticeCards";
import { ConditionalSafetyCard, SafetyCard } from "./SafetyCard";
import { SessionEndedCard } from "./SessionEndedCard";
import { SlotCard } from "./SlotCard";
import { SourceChipCard, TextCard } from "./TextCard";
import { AppointmentCard, CancelledCard, ConfirmationCard } from "./VisitCards";
import { WherePromptCard } from "./WherePromptCard";

// Each entry is a plain arrow returning an element, so hooks run inside the card, not in renderBlock's call.
export const cardRenderers: RendererMap = {
  text: (p) => <TextCard {...p} />,
  source_chip: (p) => <SourceChipCard {...p} />,
  safety: (p) => <SafetyCard {...p} />,
  conditional_safety: (p) => <ConditionalSafetyCard {...p} />,
  burning_check: (p) => <BurningCheckCard {...p} />,
  emergency_line: (p) => <EmergencyLineCard {...p} />,
  quick_checks: (p) => <QuickChecksCard {...p} />,
  urgency_questions: (p) => <UrgencyQuestionsCard {...p} />,
  where_prompt: (p) => <WherePromptCard {...p} />,
  locate_prompt: (p) => <LocatePromptCard {...p} />,
  code_prompt: (p) => <CodePromptCard {...p} />,
  slot_card: (p) => <SlotCard {...p} />,
  confirmation: (p) => <ConfirmationCard {...p} />,
  appointment: (p) => <AppointmentCard {...p} />,
  cancelled: (p) => <CancelledCard {...p} />,
  account_card: (p) => <AccountCard {...p} />,
  change_request: (p) => <ChangeRequestCard {...p} />,
  handoff: (p) => <HandoffCard {...p} />,
  live_queued: (p) => <LiveQueuedCard {...p} />,
  failure_offer: (p) => <FailureOfferCard {...p} />,
  no_info: (p) => <NoInfoCard {...p} />,
  notice: (p) => <NoticeCard {...p} />,
  error: (p) => <ErrorCard {...p} />,
  session_ended: (p) => <SessionEndedCard {...p} />,
};
