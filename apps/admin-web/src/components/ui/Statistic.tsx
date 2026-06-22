import { Skeleton } from "./Skeleton";
import styles from "./Statistic.module.css";

interface StatisticProps {
  title: string;
  value: number | string;
  loading?: boolean;
  tone?: "default" | "success" | "danger";
}

export function Statistic({ title, value, loading, tone = "default" }: StatisticProps) {
  return (
    <div className={styles.wrapper}>
      <span className={styles.title}>{title}</span>
      {loading ? (
        <Skeleton width={80} height={28} />
      ) : (
        <span className={[styles.value, styles[tone]].join(" ")}>{value}</span>
      )}
    </div>
  );
}
