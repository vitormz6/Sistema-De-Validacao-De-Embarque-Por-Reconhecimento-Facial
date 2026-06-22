import styles from "./Skeleton.module.css";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  rows?: number;
}

export function Skeleton({ width = "100%", height = 14, rows = 1 }: SkeletonProps) {
  return (
    <div className={styles.stack}>
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className={styles.block} style={{ width, height }} />
      ))}
    </div>
  );
}
