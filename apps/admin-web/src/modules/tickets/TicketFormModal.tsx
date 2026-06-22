import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { DateTimeInput } from "@/components/ui/DateInput";
import { FormField } from "@/components/ui/FormField";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";

import { ticketFormSchema, type TicketFormValues } from "./ticketSchema";

interface TicketFormModalProps {
  open: boolean;
  onSubmit: (values: TicketFormValues) => Promise<void>;
  onCancel: () => void;
}

const TICKET_TYPE_OPTIONS = [
  { value: "SINGLE", label: "Avulsa" },
  { value: "MONTHLY", label: "Mensal" },
  { value: "STUDENT", label: "Estudante" },
  { value: "EMPLOYEE", label: "Funcionário" },
  { value: "VALE_TRANSPORTE", label: "Vale-transporte" },
  { value: "SPECIAL", label: "Especial" },
];

export function TicketFormModal({ open, onSubmit, onCancel }: TicketFormModalProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isSubmitting, errors },
  } = useForm<TicketFormValues>({
    resolver: zodResolver(ticketFormSchema),
    defaultValues: { ticket_type: "SINGLE", valid_from: "", valid_until: "" },
  });

  useEffect(() => {
    if (open) {
      reset({ ticket_type: "SINGLE", valid_from: "", valid_until: "" });
      setSubmitError(null);
    }
  }, [open, reset]);

  const submit = async (values: TicketFormValues) => {
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
      title="Nova passagem"
      onCancel={onCancel}
      onOk={handleSubmit(submit)}
      confirmLoading={isSubmitting}
      okText="Cadastrar"
    >
      <FormField label="Tipo">
        <Controller
          name="ticket_type"
          control={control}
          render={({ field }) => <Select {...field} options={TICKET_TYPE_OPTIONS} />}
        />
      </FormField>

      <FormField label="Válida a partir de" error={errors.valid_from?.message}>
        <Controller
          name="valid_from"
          control={control}
          render={({ field }) => (
            <DateTimeInput
              value={field.value || null}
              onChange={field.onChange}
              error={Boolean(errors.valid_from)}
            />
          )}
        />
      </FormField>

      <FormField label="Válida até" error={errors.valid_until?.message}>
        <Controller
          name="valid_until"
          control={control}
          render={({ field }) => (
            <DateTimeInput
              value={field.value || null}
              onChange={field.onChange}
              error={Boolean(errors.valid_until)}
            />
          )}
        />
      </FormField>

      {submitError && <Alert type="error" message={submitError} />}
    </Modal>
  );
}
