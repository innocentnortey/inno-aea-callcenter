import { Button } from "@/components/ui";
import { ALREADY, CONTINUE, SIGN_OUT } from "./copy";

export function AlreadySignedIn({ onContinue, onSignOut }: { onContinue(): void; onSignOut(): void }) {
  return (
    <div className="mt-4 flex flex-col gap-3">
      <p className="text-body">{ALREADY}</p>
      <div className="flex gap-3">
        <Button variant="primary" onClick={onContinue}>{CONTINUE}</Button>
        <Button onClick={onSignOut}>{SIGN_OUT}</Button>
      </div>
    </div>
  );
}
