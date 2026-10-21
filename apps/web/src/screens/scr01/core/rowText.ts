import type { ChatAction } from "../contract";
import type { Entry } from "./model";
import { optionLabel } from "./replyGroups";

/** The words in the customer's own row. Code digits and form values are never echoed (data classes). */
export function customerRowText(action: ChatAction, entries: Entry[]): string {
  switch (action.kind) {
    case "text": return action.text.trim();
    case "choice": return optionLabel(entries, action.cardId, action.option) ?? "Choice sent";
    case "code": return "Code entered";
    case "form": return "Details sent";
    case "person": return "Talk to a person";
    default: return "";
  }
}
