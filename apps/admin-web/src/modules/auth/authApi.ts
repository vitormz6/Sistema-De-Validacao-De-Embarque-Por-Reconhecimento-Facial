import { httpClient } from "@/app/httpClient";

import type { LoginRequest, TokenResponse, User } from "./types";

export const authApi = {
  async login(payload: LoginRequest): Promise<TokenResponse> {
    const response = await httpClient.post<TokenResponse>("/auth/login", payload);
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await httpClient.get<User>("/auth/me");
    return response.data;
  },
};
