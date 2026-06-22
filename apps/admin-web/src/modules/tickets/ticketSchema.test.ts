import { describe, expect, it } from "vitest";

import { ticketFormSchema } from "./ticketSchema";

describe("ticketFormSchema", () => {
  it("accepts a valid window where valid_until is after valid_from", () => {
    const result = ticketFormSchema.safeParse({
      ticket_type: "SINGLE",
      valid_from: "2026-06-21T00:00:00.000Z",
      valid_until: "2026-06-22T00:00:00.000Z",
    });
    expect(result.success).toBe(true);
  });

  it("rejects when valid_until is before valid_from", () => {
    const result = ticketFormSchema.safeParse({
      ticket_type: "SINGLE",
      valid_from: "2026-06-22T00:00:00.000Z",
      valid_until: "2026-06-21T00:00:00.000Z",
    });
    expect(result.success).toBe(false);
  });

  it("rejects when valid_until equals valid_from", () => {
    const sameInstant = "2026-06-21T12:00:00.000Z";
    const result = ticketFormSchema.safeParse({
      ticket_type: "SINGLE",
      valid_from: sameInstant,
      valid_until: sameInstant,
    });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown ticket_type", () => {
    const result = ticketFormSchema.safeParse({
      ticket_type: "NOT_A_REAL_TYPE",
      valid_from: "2026-06-21T00:00:00.000Z",
      valid_until: "2026-06-22T00:00:00.000Z",
    });
    expect(result.success).toBe(false);
  });
});
