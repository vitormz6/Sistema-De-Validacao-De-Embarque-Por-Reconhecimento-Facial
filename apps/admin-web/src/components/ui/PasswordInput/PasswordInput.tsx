import { forwardRef, useState, type InputHTMLAttributes } from "react";

import { EyeIcon, EyeOffIcon } from "../icons";
import { Input } from "../Input";
import styles from "./PasswordInput.module.css";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  error?: boolean;
};

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput({ error, ...rest }, ref) {
    const [visible, setVisible] = useState(false);

    return (
      <Input
        ref={ref}
        type={visible ? "text" : "password"}
        error={error}
        suffix={
          <button
            type="button"
            className={styles.toggle}
            onClick={() => setVisible((current) => !current)}
            aria-label={visible ? "Ocultar senha" : "Mostrar senha"}
            tabIndex={-1}
          >
            {visible ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        }
        {...rest}
      />
    );
  },
);
