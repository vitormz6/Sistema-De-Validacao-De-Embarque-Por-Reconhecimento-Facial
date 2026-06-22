import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, type TableColumn } from "@/components/ui/Table";
import { Tag } from "@/components/ui/Tag";
import { ActivityIcon, CheckCircleIcon, XCircleIcon } from "@/components/ui/icons";
import { validationsApi } from "@/modules/validations/validationsApi";

import { dashboardApi } from "./dashboardApi";
import type { SyncDeviceStatus } from "./types";
import styles from "./DashboardPage.module.css";

function sumDenied(byStatus: Record<string, number>): number {
  return Object.entries(byStatus)
    .filter(([status]) => status !== "AUTHORIZED")
    .reduce((total, [, count]) => total + count, 0);
}

const STALE_THRESHOLD_HOURS = 24;

function isStale(device: SyncDeviceStatus): boolean {
  if (!device.last_push_at) return true;
  return dayjs().diff(dayjs(device.last_push_at), "hour") >= STALE_THRESHOLD_HOURS;
}

const DEVICE_COLUMNS: TableColumn<SyncDeviceStatus>[] = [
  { key: "device_id", title: "Dispositivo", render: (d) => d.device_id },
  {
    key: "last_pull_at",
    title: "Último pull",
    render: (d) => (d.last_pull_at ? dayjs(d.last_pull_at).format("DD/MM/YYYY HH:mm") : "—"),
  },
  {
    key: "last_push_at",
    title: "Último push",
    render: (d) => (d.last_push_at ? dayjs(d.last_push_at).format("DD/MM/YYYY HH:mm") : "—"),
  },
  {
    key: "sync_status",
    title: "Status",
    render: (d) =>
      isStale(d) ? <Tag variant="warning">Atenção</Tag> : <Tag variant="success">Em dia</Tag>,
  },
];

interface StatCardProps {
  title: string;
  value: number;
  loading: boolean;
  icon: React.ReactNode;
  colorClass: string;
}

function StatCard({ title, value, loading, icon, colorClass }: StatCardProps) {
  return (
    <div className={`${styles.statCard} ${colorClass}`}>
      <div className={styles.statIcon}>{icon}</div>
      <div className={styles.statBody}>
        <span className={styles.statTitle}>{title}</span>
        {loading ? (
          <Skeleton rows={1} height={32} />
        ) : (
          <span className={styles.statValue}>{value.toLocaleString("pt-BR")}</span>
        )}
      </div>
    </div>
  );
}

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
  const totalCount = statsQuery.data?.total ?? 0;

  return (
    <div>
      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.heading}>Dashboard</h2>
          <p className={styles.subheading}>Visão geral do sistema de validação</p>
        </div>
      </div>

      {statsQuery.isError && (
        <Alert
          type="error"
          message={extractErrorMessage(statsQuery.error)}
          className={styles.alert}
        />
      )}

      <div className={styles.statsGrid}>
        <StatCard
          title="Validações autorizadas"
          value={authorizedCount}
          loading={statsQuery.isLoading}
          icon={<CheckCircleIcon />}
          colorClass={styles.statSuccess}
        />
        <StatCard
          title="Validações negadas"
          value={deniedCount}
          loading={statsQuery.isLoading}
          icon={<XCircleIcon />}
          colorClass={styles.statDanger}
        />
        <StatCard
          title="Total de validações"
          value={totalCount}
          loading={statsQuery.isLoading}
          icon={<ActivityIcon />}
          colorClass={styles.statNeutral}
        />
      </div>

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
