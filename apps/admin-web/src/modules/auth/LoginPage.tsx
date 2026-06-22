import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { PlaneIcon } from "@/components/ui/icons";
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
      <div className={styles.hero}>
        <div className={styles.heroGlow} />

        <div className={styles.heroTop}>
          <div className={styles.heroBrandIcon}>
            <PlaneIcon />
          </div>
          <span className={styles.heroBrandName}>BFV Admin</span>
        </div>

        <div className={styles.heroBody}>
          <h1 className={styles.heroTitle}>
            Controle de embarque <em>inteligente</em>
          </h1>
          <p className={styles.heroDescription}>
            Gerencie passageiros, passagens e validações biométricas em tempo real com segurança e
            precisão.
          </p>
        </div>

        <div className={styles.heroFeatures}>
          <div className={styles.heroFeatureItem}>
            <span className={styles.heroFeatureDot} />
            Validação facial com reconhecimento biométrico
          </div>
          <div className={styles.heroFeatureItem}>
            <span className={styles.heroFeatureDot} />
            Sincronização de dispositivos de borda
          </div>
          <div className={styles.heroFeatureItem}>
            <span className={styles.heroFeatureDot} />
            Monitoramento de validações em tempo real
          </div>
        </div>
      </div>

      <div className={styles.panel}>
        <div className={styles.formHeader}>
          <h2 className={styles.formTitle}>Bem-vindo de volta</h2>
          <p className={styles.formSubtitle}>
            Insira suas credenciais para acessar o painel administrativo.
          </p>
        </div>

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
