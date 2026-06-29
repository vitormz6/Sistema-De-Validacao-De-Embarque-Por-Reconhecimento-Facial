import type { ReactNode } from "react";

import { AlertCircleIcon, AlertTriangleIcon, CheckIcon } from "../icons";
import styles from "./Alert.module.css";

export type AlertType = "info" | "success" | "warning" | "error";

interface AlertProps {
  type?: AlertType;
  message: ReactNode;
  className?: string;
}

const ICONS: Record<AlertType, ReactNode> = {
  info: <AlertCircleIcon />,
  success: <CheckIcon />,
  warning: <AlertTriangleIcon />,
  error: <AlertTriangleIcon />,
};

export function Alert({ type = "info", message, className }: AlertProps) {
  return (
    <div className={[styles.alert, styles[type], className].filter(Boolean).join(" ")}>
      <span className={styles.icon}>{ICONS[type]}</span>
      <span>{message}</span>
    </div>
  );
}
