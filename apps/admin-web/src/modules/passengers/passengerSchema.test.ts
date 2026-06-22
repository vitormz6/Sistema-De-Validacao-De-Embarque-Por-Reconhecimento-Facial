import { describe, expect, it } from "vitest";

import { passengerFormSchema } from "./passengerSchema";

describe("passengerFormSchema", () => {
  it("accepts a valid passenger without a birth date", () => {
    const result = passengerFormSchema.safeParse({
      full_name: "Maria Silva",
      document_number: "12345678900",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a full_name shorter than 3 characters", () => {
    const result = passengerFormSchema.safeParse({
      full_name: "Jo",
      document_number: "12345678900",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a document_number shorter than 3 characters", () => {
    const result = passengerFormSchema.safeParse({
      full_name: "Maria Silva",
      document_number: "12",
    });
    expect(result.success).toBe(false);
  });

  it("accepts an explicit null birth_date", () => {
    const result = passengerFormSchema.safeParse({
      full_name: "Maria Silva",
      document_number: "12345678900",
      birth_date: null,
    });
    expect(result.success).toBe(true);
  });
});
