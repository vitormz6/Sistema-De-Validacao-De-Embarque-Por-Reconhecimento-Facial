import { httpClient } from "@/app/httpClient";

import type {
  BoardingValidation,
  ValidationListParams,
  ValidationListResponse,
  ValidationStats,
} from "./types";

export const validationsApi = {
  async list(params: ValidationListParams): Promise<ValidationListResponse> {
    const response = await httpClient.get<ValidationListResponse>("/validations", { params });
    return response.data;
  },

  async getById(id: string): Promise<BoardingValidation> {
    const response = await httpClient.get<BoardingValidation>(`/validations/${id}`);
    return response.data;
  },

  async getStats(): Promise<ValidationStats> {
    const response = await httpClient.get<ValidationStats>("/validations/stats");
    return response.data;
  },
};
