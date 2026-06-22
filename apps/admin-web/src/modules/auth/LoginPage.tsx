import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";

import { useAuth } from "./AuthContext";
import { loginSchema, type LoginFormValues } from "./loginSchema";
import styles from "./LoginPage.module.css";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setSubmitError(null);
    try {
      await login(values);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmitError(extractErrorMessage(error));
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <h1 className={styles.title}>Boarding Face Validation</h1>

        <form onSubmit={handleSubmit(onSubmit)}>
          <FormField label="E-mail" error={errors.email?.message}>
            <Controller
              name="email"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  aria-label="E-mail"
                  autoComplete="email"
                  autoFocus
                  error={Boolean(errors.email)}
                />
              )}
            />
          </FormField>

          <FormField label="Senha" error={errors.password?.message}>
            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <PasswordInput
                  {...field}
                  aria-label="Senha"
                  autoComplete="current-password"
                  error={Boolean(errors.password)}
                />
              )}
            />
          </FormField>

          {submitError && (
            <Alert type="error" message={submitError} className={styles.alert} />
          )}

          <Button type="submit" variant="primary" block loading={isSubmitting}>
            Entrar
          </Button>
        </form>
      </div>
    </div>
  );
}
