import { describe, expect, it } from "vitest";

import { loginSchema } from "./loginSchema";

describe("loginSchema", () => {
  it("accepts a valid email and an 8+ character password", () => {
    const result = loginSchema.safeParse({ email: "admin@example.com", password: "senha-forte" });
    expect(result.success).toBe(true);
  });

  it("rejects an invalid email", () => {
    const result = loginSchema.safeParse({ email: "not-an-email", password: "senha-forte" });
    expect(result.success).toBe(false);
  });

  it("rejects a password shorter than 8 characters", () => {
    const result = loginSchema.safeParse({ email: "admin@example.com", password: "short" });
    expect(result.success).toBe(false);
  });

  it("rejects an empty email", () => {
    const result = loginSchema.safeParse({ email: "", password: "senha-forte" });
    expect(result.success).toBe(false);
  });
});
