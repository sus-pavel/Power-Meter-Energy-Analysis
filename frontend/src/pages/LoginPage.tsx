import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { Activity, LogIn } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/ErrorState";

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: Location } | null)?.from?.pathname || "/dashboard";
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch {
      setError("Invalid username or password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-background md:grid-cols-[420px_1fr]">
      <section className="flex min-h-screen flex-col justify-between border-r border-border bg-card px-8 py-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <p className="text-base font-semibold text-foreground">PowerMeter</p>
            <p className="text-xs text-muted-foreground">Application Console</p>
          </div>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Sign in</h1>
            <p className="mt-1 text-sm text-muted-foreground">Use your local PowerMeter account.</p>
          </div>
          {error ? <ErrorState title="Login failed" message={error} /> : null}
          <label className="block text-sm font-medium text-foreground">
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border border-border bg-background px-3 text-sm outline-none focus:border-primary"
              autoComplete="username"
            />
          </label>
          <label className="block text-sm font-medium text-foreground">
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border border-border bg-background px-3 text-sm outline-none focus:border-primary"
              type="password"
              autoComplete="current-password"
            />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex h-10 w-full items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <LogIn className="mr-2 h-4 w-4" />
            {submitting ? "Signing in" : "Sign in"}
          </button>
        </form>
        <p className="text-xs text-muted-foreground">Local-first monitoring backend required.</p>
      </section>
      <section className="hidden bg-[linear-gradient(135deg,#f8fafc_0%,#e2e8f0_55%,#d7e9ec_100%)] p-10 md:flex md:flex-col md:justify-end">
        <div className="max-w-xl border-l-4 border-primary pl-5">
          <p className="text-sm font-medium uppercase text-muted-foreground">Industrial energy operations</p>
          <p className="mt-3 text-3xl font-semibold text-foreground">Monitor devices, discovery, and analytics from a controlled local console.</p>
        </div>
      </section>
    </div>
  );
}
