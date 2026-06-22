import { z } from "zod";

const TICKET_TYPES = [
  "SINGLE",
  "MONTHLY",
  "STUDENT",
  "EMPLOYEE",
  "VALE_TRANSPORTE",
  "SPECIAL",
] as const;

/** Mirrors central-api's TicketCreate validation (app/modules/tickets/schema.py),
 * including the `valid_until > valid_from` rule. */
export const ticketFormSchema = z
  .object({
    ticket_type: z.enum(TICKET_TYPES),
    valid_from: z.string().min(1, "Informe o início da validade."),
    valid_until: z.string().min(1, "Informe o fim da validade."),
  })
  .refine((data) => new Date(data.valid_until) > new Date(data.valid_from), {
    message: "O fim da validade deve ser depois do início.",
    path: ["valid_until"],
  });

export type TicketFormValues = z.infer<typeof ticketFormSchema>;
