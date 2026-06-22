import { useEffect, useState } from "react";

import type { BoardingValidationResponse, ValidationStatus } from "@/types";

import styles from "./ResultCard.module.css";

interface Props {
  result: BoardingValidationResponse;
  resetAfterMs: number;
}

const STATUS_LABELS: Record<ValidationStatus, string> = {
  AUTHORIZED: "Embarque Autorizado",
  DENIED_NO_ACTIVE_TICKET: "Sem Passagem Ativa",
  DENIED_LOW_CONFIDENCE: "Reconhecimento Insuficiente",
  DENIED_FACE_NOT_FOUND: "Rosto Não Detectado",
  DENIED_SPOOF_SUSPECTED: "Fraude Suspeita",
  DENIED_PASSENGER_BLOCKED: "Passageiro Bloqueado",
};

function formatConfidence(result: BoardingValidationResponse): string | null {
  if (result.similarity_distance !== null) {
    const pct = Math.round((1 - result.similarity_distance) * 100);
    return `${pct}% de confiança`;
  }
  if (result.confidence_score !== null) {
    return `${Math.round(result.confidence_score * 100)}% de qualidade`;
  }
  return null;
}

export function ResultCard({ result, resetAfterMs }: Props) {
  const [countdown, setCountdown] = useState(Math.round(resetAfterMs / 1000));

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const isAuthorized = result.status === "AUTHORIZED";
  const label = STATUS_LABELS[result.status];
  const confidence = isAuthorized ? formatConfidence(result) : null;

  return (
    <div className={`${styles.card} ${isAuthorized ? styles.cardAuthorized : styles.cardDenied}`}>
      <span
        className={`${styles.icon} ${isAuthorized ? styles.iconAuthorized : styles.iconDenied}`}
        aria-hidden="true"
      >
        {isAuthorized ? "✓" : "✗"}
      </span>

      <h2
        className={`${styles.statusText} ${isAuthorized ? styles.statusAuthorized : styles.statusDenied}`}
      >
        {label}
      </h2>

      {isAuthorized && result.passenger_name !== null && (
        <p className={styles.passengerName}>{result.passenger_name}</p>
      )}

      {confidence !== null && <p className={styles.detail}>{confidence}</p>}

      {result.is_offline && <p className={styles.offlineTag}>● Modo offline</p>}

      <p className={styles.resetTimer}>Voltando em {countdown}s...</p>
    </div>
  );
}
