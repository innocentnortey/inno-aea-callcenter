import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { AppFrame } from "@/components/shell/AppFrame";
import { Main } from "@/components/shell/chrome";
import { Card, CardBody } from "@/components/ui";
import { HOME_BY_ROLE } from "@/lib/roles";
import { useSession } from "@/state/session";
import { AlreadySignedIn } from "./AlreadySignedIn";
import { LoginForm } from "./LoginForm";
import { resolveDestination } from "./destination";
import { useLogin } from "./useLogin";
import { BRAND, ENDED, FOOT, H1, STATEMENT } from "./copy";

export default function Scr12() {
  const [params] = useSearchParams();
  const returnTo = params.get("return_to");
  const navigate = useNavigate();
  const session = useSession();
  const api = useLogin(returnTo);
  useEffect(() => { document.title = "SCR-12 · Demo login · Meridian"; }, []);

  const alreadyIn = session.status === "ready" && session.session !== null && !api.leaving;
  useEffect(() => { if (!alreadyIn) api.usernameRef.current?.focus(); }, [alreadyIn, api.usernameRef]);

  const message = api.message || (params.get("reason") === "expired" ? ENDED : "");

  return (
    <AppFrame variant="auth">
      <Main className="p-4">
        <Card>
          <CardBody className="p-4">
            <p className="t-name">{BRAND}</p>
            <h1 className="t-title mt-1">{H1}</h1>
            <p className="mt-2 text-body">{STATEMENT}</p>
            <p id="login-message" aria-live="polite" className="mt-3 min-h-5 text-body">{message}</p>
            {alreadyIn ? (
              <AlreadySignedIn
                onContinue={() => navigate(resolveDestination(returnTo, HOME_BY_ROLE[session.session!.role]))}
                onSignOut={() => void session.signOut()}
              />
            ) : (
              <LoginForm api={api} />
            )}
            <p className="mt-4 text-small text-text-muted">{FOOT}</p>
          </CardBody>
        </Card>
      </Main>
    </AppFrame>
  );
}
