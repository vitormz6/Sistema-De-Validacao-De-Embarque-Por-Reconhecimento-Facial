import type { ReactNode } from "react";

import styles from "./Descriptions.module.css";

export interface DescriptionItem {
  label: string;
  value: ReactNode;
}

interface DescriptionsProps {
  items: DescriptionItem[];
}

export function Descriptions({ items }: DescriptionsProps) {
  return (
    <dl className={styles.list}>
      {items.map((item) => (
        <div key={item.label} className={styles.row}>
          <dt className={styles.label}>{item.label}</dt>
          <dd className={styles.value}>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
