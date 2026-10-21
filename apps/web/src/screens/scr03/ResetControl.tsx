import { ResultLine } from "@/components/shared/states";
import { Button, Card, CardBody, CardHeader, Dialog } from "@/components/ui";
import type { useResetDemo } from "./useResetDemo";
import { CANCEL, RESETTING, RESET_BUTTON, RESET_CONSEQUENCE, RESET_TITLE } from "./copy";

export function ResetControl({ api }: { api: ReturnType<typeof useResetDemo> }) {
  return (
    <Card>
      <CardHeader as="h2" title="Reset the demo" />
      <CardBody>
        <p className="text-body">{RESET_CONSEQUENCE}</p>
        <div className="mt-3">
          <Button disabled={api.busy} onClick={() => api.setOpen(true)}>{api.busy ? RESETTING : RESET_BUTTON}</Button>
        </div>
        <div className="mt-2">{api.result ? <ResultLine>{api.result}</ResultLine> : null}</div>
        <Dialog open={api.open} onClose={() => api.setOpen(false)} title={RESET_TITLE} initialFocus="cancel">
          <p className="text-body">{RESET_CONSEQUENCE}</p>
          <div className="mt-4 flex justify-end gap-3">
            <Button data-dialog-cancel onClick={() => api.setOpen(false)}>{CANCEL}</Button>
            <Button variant="primary" onClick={() => void api.confirm()}>{RESET_BUTTON}</Button>
          </div>
        </Dialog>
      </CardBody>
    </Card>
  );
}
