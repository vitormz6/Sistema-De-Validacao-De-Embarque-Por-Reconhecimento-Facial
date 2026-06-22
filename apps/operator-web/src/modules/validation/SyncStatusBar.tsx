import { useQuery } from "@tanstack/react-query";

import { syncApi } from "@/api/syncApi";

import styles from "./SyncStatusBar.module.css";

const POLL_INTERVAL_MS = 10_000;

export function SyncStatusBar() {
  const { data } = useQuery({
    queryKey: ["sync-status"],
    queryFn: syncApi.getStatus,
    refetchInterval: POLL_INTERVAL_MS,
  });

  const isOffline = data?.is_offline ?? false;
  const pending = data?.pending_validations ?? 0;

  return (
    <div className={styles.bar}>
      <span className={styles.title}>Validação de Embarque</span>
      <span className={styles.spacer} />
      <span className={styles.indicator}>
        <span
          className={`${styles.dot} ${isOffline ? styles.dotOffline : styles.dotOnline}`}
        />
        {isOffline ? "Offline" : "Online"}
      </span>
      {pending > 0 && (
        <span className={styles.pending}>
          {pending} pendente{pending !== 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}
