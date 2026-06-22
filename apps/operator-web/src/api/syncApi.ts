import { httpClient } from "@/api/httpClient";

import type { SyncStatusResponse } from "@/types";

export const syncApi = {
  async getStatus(): Promise<SyncStatusResponse> {
    const response = await httpClient.get<SyncStatusResponse>("/local/sync/status");
    return response.data;
  },
};
