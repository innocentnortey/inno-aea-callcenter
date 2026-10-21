import { Button, Checkbox, Field, TextInput } from "@/components/ui";
import type { LoginApi } from "./useLogin";
import { HINT, PASSWORD, SHOW, SIGN_IN, SIGNING_IN, USERNAME } from "./copy";

const MESSAGE_ID = "login-message";

export function LoginForm({ api }: { api: LoginApi }) {
  const describe = (own: string | undefined) => [own, api.invalid ? MESSAGE_ID : undefined].filter(Boolean).join(" ") || undefined;
  return (
    <form
      method="post"
      className="mt-4 flex flex-col gap-4"
      onSubmit={(e) => { e.preventDefault(); void api.submit(); }}
    >
      <Field label={USERNAME} hint={HINT}>
        {(ids) => (
          <TextInput
            ref={api.usernameRef}
            id={ids.id}
            name="username"
            autoComplete="username"
            spellCheck={false}
            autoCapitalize="none"
            value={api.username}
            readOnly={api.pending}
            invalid={api.invalid}
            aria-describedby={describe(ids.describedBy)}
            onChange={(e) => api.setUsername(e.target.value)}
          />
        )}
      </Field>
      <Field label={PASSWORD} hint={HINT}>
        {(ids) => (
          <TextInput
            ref={api.passwordRef}
            id={ids.id}
            name="password"
            type={api.show ? "text" : "password"}
            autoComplete="current-password"
            spellCheck={false}
            autoCapitalize="none"
            value={api.password}
            readOnly={api.pending}
            invalid={api.invalid}
            aria-describedby={describe(ids.describedBy)}
            onChange={(e) => api.setPassword(e.target.value)}
          />
        )}
      </Field>
      <Checkbox label={SHOW} checked={api.show} onChange={(e) => api.setShow(e.target.checked)} />
      <Button type="submit" variant="primary" disabled={!api.canSubmit} aria-busy={api.pending || undefined}>
        {api.pending ? SIGNING_IN : SIGN_IN}
      </Button>
    </form>
  );
}
