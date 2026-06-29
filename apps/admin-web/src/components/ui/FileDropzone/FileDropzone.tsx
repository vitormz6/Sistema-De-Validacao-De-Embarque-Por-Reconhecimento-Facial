import { useRef, useState, type DragEvent } from "react";

import { UploadIcon } from "../icons";
import styles from "./FileDropzone.module.css";

interface FileDropzoneProps {
  onFile: (file: File) => void;
  accept?: string;
  hint?: string;
}

export function FileDropzone({ onFile, accept = "image/*", hint }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) {
      onFile(file);
    }
  };

  return (
    <div
      className={[styles.dropzone, isDragging ? styles.dragging : ""].join(" ")}
      onClick={() => inputRef.current?.click()}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
    >
      <UploadIcon className={styles.icon} />
      <p className={styles.text}>Clique ou arraste uma foto do rosto</p>
      {hint && <p className={styles.hint}>{hint}</p>}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className={styles.hiddenInput}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            onFile(file);
          }
          event.target.value = "";
        }}
      />
    </div>
  );
}
