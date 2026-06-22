import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

import styles from "./Input.module.css";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  suffix?: ReactNode;
  /** Applied to the outer wrapper (for sizing/positioning), not the
   * native <input> itself — most callers want to size the whole control. */
  wrapperClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { error, suffix, className, wrapperClassName, ...rest },
  ref,
) {
  return (
    <div
      className={[styles.wrapper, error ? styles.error : "", wrapperClassName]
        .filter(Boolean)
        .join(" ")}
    >
      <input ref={ref} className={[styles.input, className].filter(Boolean).join(" ")} {...rest} />
      {suffix && <span className={styles.suffix}>{suffix}</span>}
    </div>
  );
});
