import { useState, type ReactNode } from "react";

import styles from "./Tabs.module.css";

export interface TabItem {
  key: string;
  label: string;
  children: ReactNode;
}

interface TabsProps {
  items: TabItem[];
  defaultActiveKey?: string;
}

export function Tabs({ items, defaultActiveKey }: TabsProps) {
  const [activeKey, setActiveKey] = useState(defaultActiveKey ?? items[0]?.key);
  const active = items.find((item) => item.key === activeKey);

  return (
    <div>
      <div className={styles.tabList} role="tablist">
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={item.key === activeKey}
            className={[styles.tab, item.key === activeKey ? styles.active : ""].join(" ")}
            onClick={() => setActiveKey(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className={styles.panel}>{active?.children}</div>
    </div>
  );
}
