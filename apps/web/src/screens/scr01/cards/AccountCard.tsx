import { Card, CardHeader, CardRow, IconDoc } from "@/components/ui";
import type { BlockProps } from "../contract";
import { formatMonthDayYear } from "./parts/dates";
import { SourceChipView } from "./SourceChipView";

export function AccountCard({ block }: BlockProps<"account_card">) {
  const title = block.kind === "invoice" ? `Invoice ${block.invoice?.invoice_id ?? ""}`.trim() : block.kind === "membership" ? "Membership" : "Warranty";
  const inv = block.invoice;
  return (
    <Card>
      <CardHeader icon={<IconDoc size={16} strokeWidth={1.8} aria-hidden="true" />} title={title} />
      <div className="p-3">
        {block.kind === "invoice" && inv ? (
          <div className="space-y-3">
            <div>
              <p className="t-time-hero">{inv.balance.display}</p>
              <p className="text-small text-text-muted">{`Balance · ${inv.paid ? "paid" : "unpaid"} · due ${formatMonthDayYear(inv.due_on)}`}</p>
            </div>
            <table className="w-full text-ui">
              <caption className="sr-only">Invoice lines</caption>
              <tbody>
                {inv.lines.map((l) => (
                  <tr key={l.description} className="align-top">
                    <td className="py-1 pr-2">
                      {l.description}
                      {l.source ? <SourceChipView source={l.source} /> : null}
                    </td>
                    <td className="py-1 text-right tabular-nums">{l.amount.display}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-text font-semibold">
                  <th scope="row" className="py-1 pr-2 text-left">Total</th>
                  <td className="py-1 text-right tabular-nums">{inv.total.display}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        ) : null}
        {block.kind === "membership" && block.membership ? (
          <>
            <CardRow label="Tier">{block.membership.tier}</CardRow>
            <CardRow label="Renewal date">{formatMonthDayYear(block.membership.renewal_date)}</CardRow>
          </>
        ) : null}
        {block.kind === "warranty" && block.warranty ? (
          <div className="space-y-2">
            <CardRow label="Install date">{formatMonthDayYear(block.warranty.install_date)}</CardRow>
            <p className="text-ui">{block.warranty.sentence}</p>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
