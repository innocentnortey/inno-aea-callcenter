import * as Menu from "@radix-ui/react-dropdown-menu";
import { Button, IconChevron } from "@/components/ui";
import type { ActionPlan, MenuKey, PlanItem } from "./actionPlan";

export interface SplitButtonProps {
  primary: ActionPlan["primary"];
  menu: PlanItem<MenuKey>[];
  onPrimary(): void;
  onMenu(key: MenuKey): void;
  busy: boolean;
  moreLabel?: string;
}

function MenuItems({ menu, onMenu }: { menu: PlanItem<MenuKey>[]; onMenu(key: MenuKey): void }) {
  return (
    <Menu.Portal>
      <Menu.Content align="end" sideOffset={4} className="z-20 min-w-[220px] rounded-card border border-border-hair bg-surface p-1 shadow-[var(--elev-frame)]">
        {menu.map((m) => (
          <Menu.Item
            key={m.key}
            disabled={!m.enabled}
            aria-disabled={!m.enabled || undefined}
            onSelect={() => onMenu(m.key)}
            className="flex min-h-[var(--target-min)] cursor-pointer flex-col justify-center rounded-control px-3 py-1 text-ui outline-none data-[highlighted]:bg-surface-selected data-[disabled]:cursor-not-allowed data-[disabled]:text-text-muted"
          >
            <span>{m.label}</span>
            {!m.enabled && m.reason ? <span className="text-small text-text-muted">{m.reason}</span> : null}
          </Menu.Item>
        ))}
      </Menu.Content>
    </Menu.Portal>
  );
}

export function SplitButton({ primary, menu, onPrimary, onMenu, busy, moreLabel = "More actions" }: SplitButtonProps) {
  if (!primary) {
    if (!menu.some((m) => m.enabled)) return null;
    return (
      <Menu.Root>
        <Menu.Trigger asChild>
          <Button variant="secondary" density="console">{moreLabel}</Button>
        </Menu.Trigger>
        <MenuItems menu={menu} onMenu={onMenu} />
      </Menu.Root>
    );
  }
  return (
    <div className="inline-flex overflow-hidden rounded-control">
      <Button variant="primary" density="console" className="rounded-none" loading={busy} onClick={onPrimary}>{primary.label}</Button>
      <span className="w-px bg-[var(--btn-primary-split-rule)]" aria-hidden="true" />
      <Menu.Root>
        <Menu.Trigger asChild>
          <Button variant="primary" density="console" className="rounded-none px-2" aria-label="More actions" disabled={busy}>
            <IconChevron size={16} strokeWidth={1.8} aria-hidden="true" />
          </Button>
        </Menu.Trigger>
        <MenuItems menu={menu} onMenu={onMenu} />
      </Menu.Root>
    </div>
  );
}
