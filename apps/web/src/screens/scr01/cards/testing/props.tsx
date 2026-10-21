import type { ReactElement } from "react";
import { vi, type Mock } from "vitest";
import { render } from "@testing-library/react";
import { AnnounceProvider } from "@/components/ui/LiveRegion";
import type { BlockOf, BlockProps, BlockType } from "../../contract";

export type TestProps<T extends BlockType> = BlockProps<T> & { dispatch: Mock; announce: Mock; landed: Mock };

export function makeProps<T extends BlockType>(block: BlockOf<T>, over: Partial<BlockProps<T>> = {}): TestProps<T> {
  return {
    block, settled: null, answered: false, disabled: false,
    dispatch: vi.fn().mockResolvedValue(undefined), announce: vi.fn(), landed: vi.fn(),
    ...over,
  } as TestProps<T>;
}
/** Cards need only the announce region; the session and router providers are not involved. */
export function renderCard(ui: ReactElement) { return render(<AnnounceProvider>{ui}</AnnounceProvider>); }
