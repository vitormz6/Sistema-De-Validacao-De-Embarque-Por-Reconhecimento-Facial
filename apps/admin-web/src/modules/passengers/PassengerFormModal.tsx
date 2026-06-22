import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { DateInput } from "@/components/ui/DateInput";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";

import { passengerFormSchema, type PassengerFormValues } from "./passengerSchema";
import type { Passenger } from "./types";

interface PassengerFormModalProps {
  open: boolean;
  /** Present when editing an existing passenger; absent when creating one
   * — the only thing that changes between the two modes. */
  passenger?: Passenger;
  onSubmit: (values: PassengerFormValues) => Promise<void>;
  onCancel: () => void;
}

export function PassengerFormModal({
  open,
  passenger,
  onSubmit,
  onCancel,
}: PassengerFormModalProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isSubmitting, errors },
  } = useForm<PassengerFormValues>({
    resolver: zodResolver(passengerFormSchema),
    defaultValues: { full_name: "", document_number: "", birth_date: null },
  });

  useEffect(() => {
    if (open) {
      reset({
        full_name: passenger?.full_name ?? "",
        document_number: passenger?.document_number ?? "",
        birth_date: passenger?.birth_date ?? null,
      });
      setSubmitError(null);
    }
  }, [open, passenger, reset]);

  const submit = async (values: PassengerFormValues) => {
    setSubmitError(null);
    try {
      await onSubmit(values);
    } catch (error) {
      setSubmitError(extractErrorMessage(error));
    }
  };

  if (!open) {
    return null;
  }

  return (
    <Modal
      open={open}
      title={passenger ? "Editar passageiro" : "Novo passageiro"}
      onCancel={onCancel}
      onOk={handleSubmit(submit)}
      confirmLoading={isSubmitting}
      okText={passenger ? "Salvar" : "Cadastrar"}
    >
      <FormField label="Nome completo" error={errors.full_name?.message}>
        <Controller
          name="full_name"
          control={control}
          render={({ field }) => (
            <Input {...field} autoFocus error={Boolean(errors.full_name)} />
          )}
        />
      </FormField>

      <FormField label="Documento" error={errors.document_number?.message}>
        <Controller
          name="document_number"
          control={control}
          render={({ field }) => <Input {...field} error={Boolean(errors.document_number)} />}
        />
      </FormField>

      <FormField label="Data de nascimento (opcional)">
        <Controller
          name="birth_date"
          control={control}
          render={({ field }) => (
            <DateInput value={field.value ?? null} onChange={field.onChange} />
          )}
        />
      </FormField>

      {submitError && <Alert type="error" message={submitError} />}
    </Modal>
  );
}
