import { useCallback, useRef, useState, type RefObject } from "react";
import { useNavigate } from "react-router";
import { useAction } from "@/api/useOp";
import { ApiError } from "@/api/errors";
import { useSession } from "@/state/session";
import { resolveDestination } from "./destination";
import { REFUSED, UNREACHABLE } from "./copy";

const REFUSAL_CODES = ["LOGIN_FAILED", "LOGIN_RATE_LIMITED", "VALIDATION_ERROR"];

export interface LoginApi {
  username: string; setUsername(v: string): void;
  password: string; setPassword(v: string): void;
  show: boolean; setShow(v: boolean): void;
  pending: boolean; leaving: boolean;
  message: string; invalid: boolean; canSubmit: boolean;
  usernameRef: RefObject<HTMLInputElement | null>;
  passwordRef: RefObject<HTMLInputElement | null>;
  submit(): Promise<void>;
}

export function useLogin(returnTo: string | null): LoginApi {
  const navigate = useNavigate();
  const session = useSession();
  const login = useAction("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [message, setMessage] = useState("");
  const [invalid, setInvalid] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const canSubmit = username.trim() !== "" && password !== "" && !login.pending;

  const submit = useCallback(async () => {
    if (!canSubmit) return;
    try {
      const res = await login.run({ body: { username, password } });
      setLeaving(true); // before setSession, so the "already signed in" panel never flashes
      setPassword("");
      setMessage("");
      setInvalid(false);
      session.setSession(res.session);
      navigate(resolveDestination(returnTo, res.landing), { replace: true });
    } catch (e) {
      if (e instanceof ApiError && REFUSAL_CODES.includes(e.code)) {
        setMessage(REFUSED);
        setInvalid(true);
        setPassword("");
        passwordRef.current?.focus();
      } else {
        setMessage(UNREACHABLE);
        setInvalid(false);
      }
    }
  }, [canSubmit, login, username, password, session, navigate, returnTo]);

  return { username, setUsername, password, setPassword, show, setShow, pending: login.pending, leaving, message, invalid, canSubmit, usernameRef, passwordRef, submit };
}
