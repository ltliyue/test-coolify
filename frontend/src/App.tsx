import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import AcceptInvite from "./pages/auth/AcceptInvite";
import Dashboard from "./pages/Dashboard";
import Personas from "./pages/Personas";
import Creatives from "./pages/Creatives";
import Campaigns from "./pages/Campaigns";
import Attribution from "./pages/Attribution";
import AudienceExport from "./pages/AudienceExport";
import Integrations from "./pages/Integrations";
import Imports from "./pages/Imports";
import Notifications from "./pages/Notifications";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Forbidden from "./pages/Forbidden";
import TeamPage from "./pages/settings/Team";
import ClientsPage from "./pages/settings/Clients";
import AgencyPermissionsMatrix from "./pages/settings/AgencyPermissionsMatrix";
import PlatformAgencies from "./pages/platform/Agencies";
import PlatformUsersPage from "./pages/platform/PlatformUsers";
import PlatformDashboard from "./pages/platform/Dashboard";
import PlatformSettings from "./pages/platform/Settings";
import PermissionsMatrix from "./pages/platform/PermissionsMatrix";
import PlatformRolesAdmin from "./pages/platform/RolesAdmin";
import AgencyRolesAdmin from "./pages/settings/AgencyRolesAdmin";
import {
  AuditLogForCurrentAgency,
  AuditLogPlatform,
} from "./pages/settings/AuditLog";
import ClientPortal from "./pages/client/ClientPortal";
import MyPersonas from "./pages/client/MyPersonas";
import MyReports from "./pages/client/MyReports";

import AppShell from "./components/layout/AppShell";
import ProtectedRoute from "./routes/ProtectedRoute";
import { PermissionGate } from "./components/PermissionGate";
import { PermissionSwitch } from "./components/PermissionSwitch";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/accept-invite" element={<AcceptInvite />} />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route
          path="/"
          element={
            <PermissionSwitch
              cases={[
                {
                  code: "platform.agency.view",
                  element: <PlatformDashboard />,
                },
                { code: "portal.access", element: <ClientPortal /> },
              ]}
              default={<Dashboard />}
            />
          }
        />
        <Route path="/403" element={<Forbidden />} />
        <Route path="/personas" element={<Personas />} />
        <Route
          path="/client/personas"
          element={
            <PermissionGate code="portal.access" redirect="/403">
              <MyPersonas />
            </PermissionGate>
          }
        />
        <Route
          path="/client/reports"
          element={
            <PermissionGate code="portal.access" redirect="/403">
              <MyReports />
            </PermissionGate>
          }
        />
        <Route path="/creatives" element={<Creatives />} />
        <Route path="/campaigns" element={<Campaigns />} />
        <Route path="/attribution" element={<Attribution />} />
        <Route path="/audience-export" element={<AudienceExport />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/imports" element={<Imports />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/reports" element={<Reports />} />
        <Route
          path="/settings"
          element={
            <PermissionSwitch
              cases={[
                {
                  code: "platform.agency.view",
                  element: <PlatformSettings />,
                },
              ]}
              default={<Settings />}
            />
          }
        />
        <Route path="/settings/profile" element={<Settings />} />
        <Route path="/settings/agency" element={<Settings />} />
        <Route path="/settings/brand" element={<Settings />} />
        <Route path="/settings/compliance" element={<Settings />} />
        <Route path="/settings/team" element={<TeamPage />} />
        <Route path="/settings/clients" element={<ClientsPage />} />
        <Route
          path="/settings/permissions"
          element={
            <PermissionGate code="settings.permissions.manage" redirect="/403">
              <AgencyPermissionsMatrix />
            </PermissionGate>
          }
        />
        <Route
          path="/platform/agencies"
          element={
            <PermissionGate code="platform.agency.view" redirect="/403">
              <PlatformAgencies />
            </PermissionGate>
          }
        />
        <Route
          path="/platform/users"
          element={
            <PermissionGate code="platform.users.view" redirect="/403">
              <PlatformUsersPage />
            </PermissionGate>
          }
        />
        <Route
          path="/platform/permissions"
          element={
            <PermissionGate code="platform.permissions.manage" redirect="/403">
              <PermissionsMatrix />
            </PermissionGate>
          }
        />
        <Route
          path="/platform/roles"
          element={
            <PermissionGate code="platform.permissions.manage" redirect="/403">
              <PlatformRolesAdmin />
            </PermissionGate>
          }
        />
        <Route
          path="/settings/roles"
          element={
            <PermissionGate code="settings.permissions.manage" redirect="/403">
              <AgencyRolesAdmin />
            </PermissionGate>
          }
        />
        <Route
          path="/settings/audit"
          element={
            <PermissionGate code="audit.read" redirect="/403">
              <AuditLogForCurrentAgency />
            </PermissionGate>
          }
        />
        <Route
          path="/platform/audit"
          element={
            <PermissionGate code="platform.audit.read" redirect="/403">
              <AuditLogPlatform />
            </PermissionGate>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
