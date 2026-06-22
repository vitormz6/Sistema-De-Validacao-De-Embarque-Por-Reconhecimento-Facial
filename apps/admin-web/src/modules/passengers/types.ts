/** Mirrors central-api's app/modules/passengers/schema.py. */

export type PassengerStatus = "ACTIVE" | "BLOCKED" | "INACTIVE";

export interface Passenger {
  id: string;
  full_name: string;
  document_number: string;
  birth_date: string | null;
  status: PassengerStatus;
  created_at: string;
  updated_at: string;
}

export interface PassengerCreateInput {
  full_name: string;
  document_number: string;
  birth_date?: string | null;
}

export interface PassengerUpdateInput {
  full_name?: string;
  document_number?: string;
  birth_date?: string | null;
  status?: PassengerStatus;
}

export interface PassengerListResponse {
  items: Passenger[];
  total: number;
  page: number;
  page_size: number;
}

export interface PassengerListParams {
  page?: number;
  page_size?: number;
  status?: PassengerStatus;
  search?: string;
}
