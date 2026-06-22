import { httpClient } from "@/app/httpClient";

import type { SyncDeviceListResponse } from "./types";

export const dashboardApi = {
  async listDevices(): Promise<SyncDeviceListResponse> {
    const response = await httpClient.get<SyncDeviceListResponse>("/sync/devices");
    return response.data;
  },
};
