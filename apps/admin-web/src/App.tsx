import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/app/AppLayout";
import { NotFoundPage } from "@/app/NotFoundPage";
import { AuthProvider } from "@/modules/auth/AuthContext";
import { LoginPage } from "@/modules/auth/LoginPage";
import { ProtectedRoute } from "@/modules/auth/ProtectedRoute";
import { DashboardPage } from "@/modules/dashboard/DashboardPage";
import { PassengerDetailPage } from "@/modules/passengers/PassengerDetailPage";
import { PassengersListPage } from "@/modules/passengers/PassengersListPage";
import { ValidationsListPage } from "@/modules/validations/ValidationsListPage";

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/passengers" element={<PassengersListPage />} />
          <Route path="/passengers/:passengerId" element={<PassengerDetailPage />} />
          <Route path="/validations" element={<ValidationsListPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  );
}
