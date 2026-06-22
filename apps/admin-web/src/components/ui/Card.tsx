import type { ReactNode } from "react";

import styles from "./Card.module.css";

interface CardProps {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({ title, actions, children, className }: CardProps) {
  return (
    <div className={[styles.card, className].filter(Boolean).join(" ")}>
      {(title || actions) && (
        <div className={styles.header}>
          {title && <h3 className={styles.title}>{title}</h3>}
          {actions}
        </div>
      )}
      <div className={styles.body}>{children}</div>
    </div>
  );
}
