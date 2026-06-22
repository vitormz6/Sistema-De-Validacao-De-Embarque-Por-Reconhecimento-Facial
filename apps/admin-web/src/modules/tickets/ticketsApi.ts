import { httpClient } from "@/app/httpClient";

import type { Ticket, TicketCreateInput, TicketListParams, TicketListResponse } from "./types";

export const ticketsApi = {
  async list(params: TicketListParams): Promise<TicketListResponse> {
    const response = await httpClient.get<TicketListResponse>("/tickets", { params });
    return response.data;
  },

  async create(payload: TicketCreateInput): Promise<Ticket> {
    const response = await httpClient.post<Ticket>("/tickets", payload);
    return response.data;
  },

  async block(id: string): Promise<Ticket> {
    const response = await httpClient.post<Ticket>(`/tickets/${id}/block`);
    return response.data;
  },

  async activate(id: string): Promise<Ticket> {
    const response = await httpClient.post<Ticket>(`/tickets/${id}/activate`);
    return response.data;
  },
};
