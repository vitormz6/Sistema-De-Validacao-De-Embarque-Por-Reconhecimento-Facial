import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { validationApi } from "@/api/validationApi";
import type { BoardingValidationResponse } from "@/types";

import { CameraCapture } from "./CameraCapture";
import { ResultCard } from "./ResultCard";
import { SyncStatusBar } from "./SyncStatusBar";
import styles from "./ValidationPage.module.css";

type PageState = "idle" | "processing" | "result";

const RESULT_DISPLAY_MS = 4_000;

export function ValidationPage() {
  const [pageState, setPageState] = useState<PageState>("idle");
  const [result, setResult] = useState<BoardingValidationResponse | null>(null);

  const { mutate, isError } = useMutation({
    mutationFn: (blob: Blob) => validationApi.validateBoarding(blob),
    onSuccess: (data) => {
      setResult(data);
      setPageState("result");
      setTimeout(() => {
        setPageState("idle");
        setResult(null);
      }, RESULT_DISPLAY_MS);
    },
    onError: () => {
      setPageState("idle");
    },
  });

  function handleCapture(blob: Blob) {
    setPageState("processing");
    mutate(blob);
  }

  return (
    <div className={styles.page}>
      <SyncStatusBar />
      <main className={styles.main}>
        {pageState === "result" && result !== null ? (
          <ResultCard result={result} resetAfterMs={RESULT_DISPLAY_MS} />
        ) : (
          <>
            <p className={styles.subtitle}>
              Posicione o rosto na câmera e pressione o botão para validar o embarque
            </p>
            <CameraCapture
              onCapture={handleCapture}
              disabled={pageState === "processing"}
              processing={pageState === "processing"}
            />
            {isError && (
              <p className={styles.errorText}>
                Erro ao comunicar com o dispositivo. Tente novamente.
              </p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
