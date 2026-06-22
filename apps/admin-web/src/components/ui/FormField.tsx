import type { ReactNode } from "react";

import styles from "./FormField.module.css";

interface FormFieldProps {
  label?: string;
  error?: string;
  hint?: string;
  children: ReactNode;
  htmlFor?: string;
}

export function FormField({ label, error, hint, children, htmlFor }: FormFieldProps) {
  return (
    <div className={styles.field}>
      {label && (
        <label className={styles.label} htmlFor={htmlFor}>
          {label}
        </label>
      )}
      {children}
      {error ? (
        <span className={styles.errorText}>{error}</span>
      ) : hint ? (
        <span className={styles.hintText}>{hint}</span>
      ) : null}
    </div>
  );
}
