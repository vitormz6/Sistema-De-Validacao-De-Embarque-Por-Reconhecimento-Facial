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
    return `${pct}% de similaridade`;
  }
  if (result.confidence_score !== null) {
    return `${Math.round(result.confidence_score * 100)}% de confiança`;
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
      <div className={styles.iconWrapper}>
        {isAuthorized ? (
          <svg
            className={styles.icon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <path d="M22 4L12 14.01l-3-3" />
          </svg>
        ) : (
          <svg
            className={styles.icon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M15 9l-6 6" />
            <path d="M9 9l6 6" />
          </svg>
        )}
      </div>

      <h2 className={styles.statusText}>{label}</h2>

      {isAuthorized && result.passenger_name !== null && (
        <p className={styles.passengerName}>{result.passenger_name}</p>
      )}

      {confidence !== null && <p className={styles.detail}>{confidence}</p>}

      {result.is_offline && (
        <span className={styles.offlineBadge}>
          <span className={styles.offlineDot} />
          Modo offline
        </span>
      )}

      <div className={styles.footer}>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ animationDuration: `${resetAfterMs}ms` }}
          />
        </div>
        <p className={styles.resetTimer}>Voltando em {countdown}s</p>
      </div>
    </div>
  );
}
