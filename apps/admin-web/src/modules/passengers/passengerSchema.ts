import { z } from "zod";

/** Mirrors central-api's PassengerCreate/PassengerUpdate validation
 * (app/modules/passengers/schema.py) so the form fails the same inputs
 * client-side that the API would reject anyway. */
export const passengerFormSchema = z.object({
  full_name: z
    .string()
    .min(3, "Mínimo de 3 caracteres.")
    .max(160, "Máximo de 160 caracteres."),
  document_number: z
    .string()
    .min(3, "Mínimo de 3 caracteres.")
    .max(32, "Máximo de 32 caracteres."),
  birth_date: z.string().optional().nullable(),
});

export type PassengerFormValues = z.infer<typeof passengerFormSchema>;
