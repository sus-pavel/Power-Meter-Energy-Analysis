import { Link } from "react-router-dom";
import { AlertTriangle, Ban, FileQuestion, ServerCrash } from "lucide-react";

function ErrorPage({ code, title, message, icon }: { code: string; title: string; message: string; icon: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-md rounded-md border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-muted text-primary">{icon}</div>
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">{code}</p>
            <h1 className="text-xl font-semibold text-foreground">{title}</h1>
          </div>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">{message}</p>
        <Link className="mt-5 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground" to="/dashboard">
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}

export function ForbiddenPage() {
  return <ErrorPage code="403" title="Access denied" message="Your role is not allowed to open this section." icon={<Ban className="h-5 w-5" />} />;
}

export function NotFoundPage() {
  return <ErrorPage code="404" title="Page not found" message="The requested application route does not exist." icon={<FileQuestion className="h-5 w-5" />} />;
}

export function ServerErrorPage() {
  return <ErrorPage code="500" title="Application error" message="The application shell encountered an unexpected state." icon={<ServerCrash className="h-5 w-5" />} />;
}

export function UnauthorizedPage() {
  return <ErrorPage code="401" title="Session required" message="Sign in before opening the PowerMeter console." icon={<AlertTriangle className="h-5 w-5" />} />;
}
