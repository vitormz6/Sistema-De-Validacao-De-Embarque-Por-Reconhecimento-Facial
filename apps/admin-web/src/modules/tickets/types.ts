/** Mirrors central-api's app/modules/tickets/schema.py. */

export type TicketType =
  | "SINGLE"
  | "MONTHLY"
  | "STUDENT"
  | "EMPLOYEE"
  | "VALE_TRANSPORTE"
  | "SPECIAL";

export type TicketStatus = "ACTIVE" | "EXPIRED" | "BLOCKED" | "CANCELLED";

export interface Ticket {
  id: string;
  passenger_id: string;
  ticket_type: TicketType;
  status: TicketStatus;
  valid_from: string;
  valid_until: string;
  created_at: string;
  updated_at: string;
}

export interface TicketCreateInput {
  passenger_id: string;
  ticket_type: TicketType;
  valid_from: string;
  valid_until: string;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface TicketListParams {
  page?: number;
  page_size?: number;
  passenger_id?: string;
  status?: TicketStatus;
}
