import { httpClient } from "@/app/httpClient";

import type {
  Passenger,
  PassengerCreateInput,
  PassengerListParams,
  PassengerListResponse,
  PassengerUpdateInput,
} from "./types";

export const passengersApi = {
  async list(params: PassengerListParams): Promise<PassengerListResponse> {
    const response = await httpClient.get<PassengerListResponse>("/passengers", { params });
    return response.data;
  },

  async getById(id: string): Promise<Passenger> {
    const response = await httpClient.get<Passenger>(`/passengers/${id}`);
    return response.data;
  },

  async create(payload: PassengerCreateInput): Promise<Passenger> {
    const response = await httpClient.post<Passenger>("/passengers", payload);
    return response.data;
  },

  async update(id: string, payload: PassengerUpdateInput): Promise<Passenger> {
    const response = await httpClient.put<Passenger>(`/passengers/${id}`, payload);
    return response.data;
  },

  async block(id: string): Promise<Passenger> {
    const response = await httpClient.post<Passenger>(`/passengers/${id}/block`);
    return response.data;
  },

  async activate(id: string): Promise<Passenger> {
    const response = await httpClient.post<Passenger>(`/passengers/${id}/activate`);
    return response.data;
  },
};
