import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Stack } from "@/components/ui/Stack";
import { Statistic } from "@/components/ui/Statistic";
import { Table, type TableColumn } from "@/components/ui/Table";
import { Tag } from "@/components/ui/Tag";
import { validationsApi } from "@/modules/validations/validationsApi";

import { dashboardApi } from "./dashboardApi";
import type { SyncDeviceStatus } from "./types";
import styles from "./DashboardPage.module.css";

/** Anything that isn't AUTHORIZED is, by definition, a denial — RF13 only
 * asks for the authorized/denied split, not a breakdown per denial reason. */
function sumDenied(byStatus: Record<string, number>): number {
  return Object.entries(byStatus)
    .filter(([status]) => status !== "AUTHORIZED")
    .reduce((total, [, count]) => total + count, 0);
}

/** A device that has never pushed, or hasn't pushed in over a day, likely
 * has a stuck sync-worker or has been offline for a while — flagged here
 * so an operator notices without having to read raw timestamps. */
const STALE_THRESHOLD_HOURS = 24;

function isStale(device: SyncDeviceStatus): boolean {
  if (!device.last_push_at) {
    return true;
  }
  return dayjs().diff(dayjs(device.last_push_at), "hour") >= STALE_THRESHOLD_HOURS;
}

const DEVICE_COLUMNS: TableColumn<SyncDeviceStatus>[] = [
  { key: "device_id", title: "Dispositivo", render: (device) => device.device_id },
  {
    key: "last_pull_at",
    title: "Último pull",
    render: (device) =>
      device.last_pull_at ? dayjs(device.last_pull_at).format("DD/MM/YYYY HH:mm") : "—",
  },
  {
    key: "last_push_at",
    title: "Último push",
    render: (device) =>
      device.last_push_at ? dayjs(device.last_push_at).format("DD/MM/YYYY HH:mm") : "—",
  },
  {
    key: "sync_status",
    title: "Status de sincronização",
    render: (device) =>
      isStale(device) ? <Tag variant="warning">Atenção</Tag> : <Tag variant="success">Em dia</Tag>,
  },
];

export function DashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["validation-stats"],
    queryFn: validationsApi.getStats,
  });

  const devicesQuery = useQuery({
    queryKey: ["sync-devices"],
    queryFn: dashboardApi.listDevices,
  });

  const authorizedCount = statsQuery.data?.by_status.AUTHORIZED ?? 0;
  const deniedCount = statsQuery.data ? sumDenied(statsQuery.data.by_status) : 0;

  return (
    <div>
      <h2 className={styles.heading}>Dashboard</h2>

      {statsQuery.isError && (
        <Alert
          type="error"
          message={extractErrorMessage(statsQuery.error)}
          className={styles.alert}
        />
      )}

      <Stack gap={16} wrap className={styles.statsRow}>
        <Card className={styles.statCard}>
          <Statistic
            title="Validações autorizadas"
            value={authorizedCount}
            loading={statsQuery.isLoading}
            tone="success"
          />
        </Card>
        <Card className={styles.statCard}>
          <Statistic
            title="Validações negadas"
            value={deniedCount}
            loading={statsQuery.isLoading}
            tone="danger"
          />
        </Card>
        <Card className={styles.statCard}>
          <Statistic
            title="Total de validações"
            value={statsQuery.data?.total ?? 0}
            loading={statsQuery.isLoading}
          />
        </Card>
      </Stack>

      <Card title="Sincronização por dispositivo">
        {devicesQuery.isError && (
          <Alert
            type="error"
            message={extractErrorMessage(devicesQuery.error)}
            className={styles.alert}
          />
        )}
        <Table
          rowKey={(device) => device.device_id}
          columns={DEVICE_COLUMNS}
          data={devicesQuery.data?.devices ?? []}
          loading={devicesQuery.isLoading}
          emptyText="Nenhum dispositivo sincronizou ainda."
        />
      </Card>
    </div>
  );
}
