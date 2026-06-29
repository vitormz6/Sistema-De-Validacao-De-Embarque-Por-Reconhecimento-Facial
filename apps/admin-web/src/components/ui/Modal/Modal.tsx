import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { Button } from "../Button";
import { CloseIcon } from "../icons";
import styles from "./Modal.module.css";

interface ModalProps {
  open: boolean;
  title: ReactNode;
  children: ReactNode;
  onCancel: () => void;
  onOk?: () => void;
  okText?: string;
  okVariant?: "primary" | "danger";
  cancelText?: string;
  confirmLoading?: boolean;
}

export function Modal({
  open,
  title,
  children,
  onCancel,
  onOk,
  okText = "Confirmar",
  okVariant = "primary",
  cancelText = "Cancelar",
  confirmLoading,
}: ModalProps) {
  useEffect(() => {
    if (!open) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onCancel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onCancel]);

  if (!open) {
    return null;
  }

  return createPortal(
    <div className={styles.overlay} onMouseDown={onCancel}>
      <div className={styles.panel} onMouseDown={(event) => event.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>
          <button type="button" className={styles.closeButton} onClick={onCancel} aria-label="Fechar">
            <CloseIcon />
          </button>
        </div>

        <div className={styles.body}>{children}</div>

        <div className={styles.footer}>
          <Button variant="secondary" onClick={onCancel}>
            {cancelText}
          </Button>
          {onOk && (
            <Button variant={okVariant} onClick={onOk} loading={confirmLoading}>
              {okText}
            </Button>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
