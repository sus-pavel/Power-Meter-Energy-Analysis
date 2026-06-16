import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
}

export function ErrorState({ title = "Request failed", message = "Check the backend connection and try again." }: ErrorStateProps) {
  return (
    <div className="rounded-md border border-destructive/30 bg-red-50 px-4 py-3 text-sm text-red-900">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4" />
        <div>
          <p className="font-medium">{title}</p>
          <p className="mt-1 text-red-800">{message}</p>
        </div>
      </div>
    </div>
  );
}
