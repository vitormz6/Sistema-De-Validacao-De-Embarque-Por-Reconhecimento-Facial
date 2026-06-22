/** Mirrors edge-api's app/modules/validation/schema.py and app/modules/health/schema.py */

export type ValidationStatus =
  | "AUTHORIZED"
  | "DENIED_NO_ACTIVE_TICKET"
  | "DENIED_LOW_CONFIDENCE"
  | "DENIED_FACE_NOT_FOUND"
  | "DENIED_SPOOF_SUSPECTED"
  | "DENIED_PASSENGER_BLOCKED";

export interface BoardingValidationResponse {
  id: string;
  status: ValidationStatus;
  passenger_id: string | null;
  passenger_name: string | null;
  ticket_id: string | null;
  confidence_score: number | null;
  similarity_distance: number | null;
  reason_code: string | null;
  is_offline: boolean;
  captured_at: string;
}

export interface SyncStatusResponse {
  is_offline: boolean;
  last_connectivity_check_at: string | null;
  pending_validations: number;
  last_validation_captured_at: string | null;
}
