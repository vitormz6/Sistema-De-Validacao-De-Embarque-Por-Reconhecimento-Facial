/** Mirrors central-api's app/modules/validations/schema.py. */

export type ValidationStatus =
  | "AUTHORIZED"
  | "DENIED_NO_ACTIVE_TICKET"
  | "DENIED_LOW_CONFIDENCE"
  | "DENIED_FACE_NOT_FOUND"
  | "DENIED_SPOOF_SUSPECTED"
  | "DENIED_PASSENGER_BLOCKED";

export interface BoardingValidation {
  id: string;
  external_id: string;
  bus_id: string;
  route_id: string | null;
  passenger_id: string | null;
  ticket_id: string | null;
  status: ValidationStatus;
  confidence_score: number | null;
  similarity_distance: number | null;
  reason_code: string | null;
  is_offline: boolean;
  captured_at: string;
  synced_at: string;
  created_at: string;
}

export interface ValidationListResponse {
  items: BoardingValidation[];
  total: number;
  page: number;
  page_size: number;
}

export interface ValidationListParams {
  page?: number;
  page_size?: number;
  status?: ValidationStatus;
  passenger_id?: string;
  bus_id?: string;
  captured_from?: string;
  captured_to?: string;
}

export interface ValidationStats {
  by_status: Record<string, number>;
  total: number;
}
