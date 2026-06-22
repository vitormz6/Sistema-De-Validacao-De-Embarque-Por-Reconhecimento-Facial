/** Mirrors central-api's app/modules/sync/schema.py (SyncStatusResponse). */

export interface SyncDeviceStatus {
  device_id: string;
  registered: boolean;
  last_pull_at: string | null;
  last_pull_cursor: string | null;
  last_push_at: string | null;
}

export interface SyncDeviceListResponse {
  devices: SyncDeviceStatus[];
}
