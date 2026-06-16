import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { useAuth } from "../auth/AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";
import { AdminPage } from "../pages/AdminPage";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DrpiPage } from "../pages/DrpiPage";
import { CandidateDetailsPage } from "../pages/CandidateDetailsPage";
import { CandidatesPage } from "../pages/CandidatesPage";
import { DeviceDetailsPage } from "../pages/DeviceDetailsPage";
import { DevicesPage } from "../pages/DevicesPage";
import { DiscoveryJobDetailsPage } from "../pages/DiscoveryJobDetailsPage";
import { DiscoveryPage } from "../pages/DiscoveryPage";
import { ForbiddenPage, NotFoundPage, ServerErrorPage, UnauthorizedPage } from "../pages/ErrorPages";
import { LoginPage } from "../pages/LoginPage";
import { OperationsPage } from "../pages/OperationsPage";
import { HistoryPage } from "../pages/HistoryPage";
import { SsaPage } from "../pages/SsaPage";

function RootRedirect() {
  const { isAuthenticated } = useAuth();
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/401" element={<UnauthorizedPage />} />
      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="/500" element={<ServerErrorPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/operations" element={<OperationsPage />} />
        <Route path="/devices" element={<DevicesPage />} />
        <Route path="/devices/:deviceId" element={<DeviceDetailsPage />} />
        <Route path="/discovery" element={<DiscoveryPage />} />
        <Route path="/discovery/jobs/:jobId" element={<DiscoveryJobDetailsPage />} />
        <Route path="/candidates" element={<CandidatesPage />} />
        <Route path="/candidates/:candidateId" element={<CandidateDetailsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/drpi" element={<DrpiPage />} />
        <Route path="/ssa" element={<SsaPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
