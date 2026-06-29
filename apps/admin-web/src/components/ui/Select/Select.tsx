import { forwardRef, type SelectHTMLAttributes } from "react";

import { ChevronDownIcon } from "../icons";
import styles from "./Select.module.css";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  options: SelectOption[];
  placeholder?: string;
}

/** Native <select>, styled — a hand-rolled listbox would need to
 * reimplement keyboard navigation and screen-reader semantics the
 * browser already gives us for free. */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { options, placeholder, className, value, ...rest },
  ref,
) {
  return (
    <div className={[styles.wrapper, className].filter(Boolean).join(" ")}>
      <select ref={ref} className={styles.select} value={value ?? ""} {...rest}>
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDownIcon className={styles.chevron} />
    </div>
  );
});
