import { useEffect, useRef, useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { CameraIcon } from "@/components/ui/icons";

import styles from "./WebcamCapture.module.css";

interface WebcamCaptureProps {
  onCapture: (file: File) => void;
}

/**
 * Snaps a single still frame from the browser's camera (RF02's "ou
 * captura" requirement) — no continuous streaming/recording, just enough
 * to grab one JPEG and hand it off exactly like a file upload would.
 */
export function WebcamCapture({ onCapture }: WebcamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let activeStream: MediaStream | null = null;

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "user" } })
      .then((mediaStream) => {
        activeStream = mediaStream;
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      })
      .catch(() => setError("Não foi possível acessar a câmera."));

    return () => {
      activeStream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (blob) {
        onCapture(new File([blob], "captura.jpg", { type: "image/jpeg" }));
      }
    }, "image/jpeg");
  };

  if (error) {
    return <Alert type="error" message={error} />;
  }

  return (
    <div className={styles.wrapper}>
      <video ref={videoRef} autoPlay playsInline muted className={styles.video} />
      <Button icon={<CameraIcon />} onClick={handleCapture} disabled={!stream}>
        Capturar
      </Button>
    </div>
  );
}
