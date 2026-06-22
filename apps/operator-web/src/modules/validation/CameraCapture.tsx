import { useEffect, useRef, useState } from "react";

import styles from "./CameraCapture.module.css";

interface Props {
  onCapture: (blob: Blob) => void;
  disabled: boolean;
  processing: boolean;
}

export function CameraCapture({ onCapture, disabled, processing }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [streamReady, setStreamReady] = useState(false);

  useEffect(() => {
    let stream: MediaStream | null = null;

    async function initCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
        });
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          setStreamReady(true);
        }
      } catch {
        setCameraError(
          "Não foi possível acessar a câmera. Verifique as permissões do dispositivo.",
        );
      }
    }

    void initCamera();

    return () => {
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  function handleCapture() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !streamReady) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob);
      },
      "image/jpeg",
      0.92,
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.cameraCard}>
        <video ref={videoRef} className={styles.video} autoPlay playsInline muted />

        {cameraError ? (
          <div className={styles.overlay}>
            <span className={styles.overlayIcon}>⚠</span>
            <span className={styles.overlayText}>{cameraError}</span>
          </div>
        ) : processing ? (
          <div className={styles.overlay}>
            <span className={styles.spinner} aria-hidden="true" />
            <span className={styles.overlayText}>Validando...</span>
          </div>
        ) : null}
      </div>

      <canvas ref={canvasRef} className={styles.hiddenCanvas} />

      <button
        type="button"
        className={styles.captureButton}
        onClick={handleCapture}
        disabled={disabled || !!cameraError || !streamReady}
      >
        {processing ? (
          "Validando..."
        ) : (
          <>
            <CameraIcon />
            Capturar e Validar
          </>
        )}
      </button>
    </div>
  );
}

function CameraIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
      <circle cx="12" cy="13" r="4" />
    </svg>
  );
}
