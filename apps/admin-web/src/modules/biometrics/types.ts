/** Mirrors central-api's app/modules/biometrics/schema.py. */

export interface BiometricEnrollment {
  id: string;
  passenger_id: string;
  model_name: string;
  model_version: string;
  detector_name: string;
  detector_version: string;
  quality_score: number;
  active: boolean;
  created_at: string;
  revoked_at: string | null;
}

export type BiometricCompareDecision =
  | "AUTHORIZED"
  | "DENIED_LOW_CONFIDENCE"
  | "DENIED_FACE_NOT_FOUND"
  | "DENIED_SPOOF_SUSPECTED";

export interface BiometricCompareResult {
  decision: BiometricCompareDecision;
  matched_passenger_id: string | null;
  distance: number | null;
  similarity: number | null;
  threshold: number;
}
