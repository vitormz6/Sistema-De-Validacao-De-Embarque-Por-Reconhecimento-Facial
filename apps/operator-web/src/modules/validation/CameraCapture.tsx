import * as faceapi from "@vladmandic/face-api";
import { useCallback, useEffect, useRef, useState } from "react";

import styles from "./CameraCapture.module.css";

interface Props {
  /** Called with the captured JPEG blob when a face is detected. */
  onCapture: (blob: Blob) => void;
  /** When false the rAF detection loop is paused (processing / result states). */
  autoDetect: boolean;
  processing: boolean;
}

const MODEL_URL = "/models";
const SCORE_THRESHOLD = 0.6;
/** Minimum time between captures — prevents re-firing on the same person. */
const CAPTURE_COOLDOWN_MS = 4_000;

export function CameraCapture({ onCapture, autoDetect, processing }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const rafIdRef = useRef<number | null>(null);
  const cooldownRef = useRef(false);

  const [modelReady, setModelReady] = useState(false);
  const [streamReady, setStreamReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [faceDetected, setFaceDetected] = useState(false);

  /* ─── Load TinyFaceDetector model once on mount ─────────────────── */
  useEffect(() => {
    faceapi.nets.tinyFaceDetector
      .loadFromUri(MODEL_URL)
      .then(() => setModelReady(true))
      .catch(() => setCameraError("Falha ao carregar modelo de detecção."));
  }, []);

  /* ─── Start camera stream on mount ──────────────────────────────── */
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
        setCameraError("Não foi possível acessar a câmera. Verifique as permissões.");
      }
    }

    void initCamera();
    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  /* ─── Capture current video frame as JPEG blob ───────────────────── */
  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = captureCanvasRef.current;
    if (!video || !canvas) return;

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
  }, [onCapture]);

  /* ─── Detection / drawing helpers ───────────────────────────────── */
  function drawDetections(
    canvas: HTMLCanvasElement,
    video: HTMLVideoElement,
    detections: faceapi.FaceDetection[],
  ) {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    /* Sync canvas size with video display size */
    canvas.width = video.offsetWidth;
    canvas.height = video.offsetHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (detections.length === 0) return;

    const scaleX = canvas.width / video.videoWidth;
    const scaleY = canvas.height / video.videoHeight;

    detections.forEach((det) => {
      const { x, y, width, height } = det.box;
      const sx = x * scaleX;
      const sy = y * scaleY;
      const sw = width * scaleX;
      const sh = height * scaleY;

      /* Glow effect */
      ctx.shadowColor = "rgba(99, 102, 241, 0.8)";
      ctx.shadowBlur = 12;
      ctx.strokeStyle = "#6366f1";
      ctx.lineWidth = 2.5;

      /* Corner brackets — top-left */
      const corner = Math.min(sw, sh) * 0.22;
      ctx.beginPath();
      ctx.moveTo(sx, sy + corner);
      ctx.lineTo(sx, sy);
      ctx.lineTo(sx + corner, sy);
      ctx.stroke();

      /* top-right */
      ctx.beginPath();
      ctx.moveTo(sx + sw - corner, sy);
      ctx.lineTo(sx + sw, sy);
      ctx.lineTo(sx + sw, sy + corner);
      ctx.stroke();

      /* bottom-left */
      ctx.beginPath();
      ctx.moveTo(sx, sy + sh - corner);
      ctx.lineTo(sx, sy + sh);
      ctx.lineTo(sx + corner, sy + sh);
      ctx.stroke();

      /* bottom-right */
      ctx.beginPath();
      ctx.moveTo(sx + sw - corner, sy + sh);
      ctx.lineTo(sx + sw, sy + sh);
      ctx.lineTo(sx + sw, sy + sh - corner);
      ctx.stroke();

      ctx.shadowBlur = 0;
    });
  }

  /* ─── rAF detection loop ─────────────────────────────────────────── */
  useEffect(() => {
    if (!modelReady || !streamReady || !autoDetect) {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      /* Clear canvas when paused */
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        ctx?.clearRect(0, 0, canvas.width, canvas.height);
      }
      return;
    }

    let cancelled = false;

    async function detect() {
      if (cancelled) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (video && canvas && video.readyState >= 2) {
        const detections = await faceapi.detectAllFaces(
          video,
          new faceapi.TinyFaceDetectorOptions({ scoreThreshold: SCORE_THRESHOLD }),
        );

        if (!cancelled) {
          const hasFace = detections.length > 0;
          setFaceDetected(hasFace);
          drawDetections(canvas, video, detections);

          if (hasFace && !cooldownRef.current) {
            cooldownRef.current = true;
            captureFrame();
            setTimeout(() => {
              cooldownRef.current = false;
            }, CAPTURE_COOLDOWN_MS);
          }
        }
      }

      if (!cancelled) {
        rafIdRef.current = requestAnimationFrame(detect);
      }
    }

    rafIdRef.current = requestAnimationFrame(detect);

    return () => {
      cancelled = true;
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [modelReady, streamReady, autoDetect, captureFrame]);

  /* ─── Derived status label ───────────────────────────────────────── */
  function getStatusLabel(): string {
    if (cameraError) return cameraError;
    if (!streamReady || !modelReady) return "Iniciando câmera...";
    if (processing) return "Validando...";
    if (faceDetected) return "Rosto detectado — validando...";
    return "Aguardando passageiro...";
  }

  const isActive = autoDetect && faceDetected && !processing;

  return (
    <div className={styles.container}>
      <div className={`${styles.cameraWrapper} ${isActive ? styles.cameraActive : ""}`}>
        <video ref={videoRef} className={styles.video} autoPlay playsInline muted />

        {/* Detection overlay canvas */}
        <canvas ref={canvasRef} className={styles.detectionCanvas} />

        {/* Scanning animation corners (visible when idle and no face) */}
        {autoDetect && !faceDetected && !processing && streamReady && modelReady && (
          <div className={styles.scanOverlay}>
            <div className={styles.scanCornerTL} />
            <div className={styles.scanCornerTR} />
            <div className={styles.scanCornerBL} />
            <div className={styles.scanCornerBR} />
            <div className={styles.scanLine} />
          </div>
        )}

        {/* Processing spinner overlay */}
        {processing && (
          <div className={styles.processingOverlay}>
            <span className={styles.spinner} aria-hidden="true" />
          </div>
        )}

        {/* Camera / model error overlay */}
        {cameraError && (
          <div className={styles.errorOverlay}>
            <span className={styles.errorIcon}>⚠</span>
            <span className={styles.errorText}>{cameraError}</span>
          </div>
        )}
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={captureCanvasRef} className={styles.hiddenCanvas} />

      <p className={`${styles.statusLabel} ${processing ? styles.statusProcessing : ""}`}>
        {getStatusLabel()}
      </p>
    </div>
  );
}
