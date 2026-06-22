import type { ReactNode } from "react";

import styles from "./Tag.module.css";

export type TagVariant = "default" | "success" | "danger" | "warning" | "info";

interface TagProps {
  variant?: TagVariant;
  children: ReactNode;
}

export function Tag({ variant = "default", children }: TagProps) {
  return <span className={[styles.tag, styles[variant]].join(" ")}>{children}</span>;
}
