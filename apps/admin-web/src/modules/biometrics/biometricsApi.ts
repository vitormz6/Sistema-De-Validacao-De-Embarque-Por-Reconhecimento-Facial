import { httpClient } from "@/app/httpClient";

import type { BiometricEnrollment } from "./types";

export const biometricsApi = {
  async enroll(passengerId: string, file: File): Promise<BiometricEnrollment> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await httpClient.post<BiometricEnrollment>(
      `/passengers/${passengerId}/biometrics/enroll`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return response.data;
  },

  async listHistory(passengerId: string): Promise<BiometricEnrollment[]> {
    const response = await httpClient.get<BiometricEnrollment[]>(
      `/passengers/${passengerId}/biometrics`,
    );
    return response.data;
  },

  async revoke(passengerId: string): Promise<BiometricEnrollment> {
    const response = await httpClient.post<BiometricEnrollment>(
      `/passengers/${passengerId}/biometrics/revoke`,
    );
    return response.data;
  },
};
