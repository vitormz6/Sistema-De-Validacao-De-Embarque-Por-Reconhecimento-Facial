import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useState } from "react";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Descriptions } from "@/components/ui/Descriptions";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { Segmented } from "@/components/ui/Segmented";
import { Stack } from "@/components/ui/Stack";
import { Tag } from "@/components/ui/Tag";
import { useToast } from "@/components/ui/toast/ToastContext";

import { biometricsApi } from "./biometricsApi";
import { WebcamCapture } from "./WebcamCapture";
import styles from "./BiometricEnrollmentPanel.module.css";

interface BiometricEnrollmentPanelProps {
  passengerId: string;
}

type CaptureMode = "upload" | "webcam";

export function BiometricEnrollmentPanel({ passengerId }: BiometricEnrollmentPanelProps) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [mode, setMode] = useState<CaptureMode>("upload");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const historyQuery = useQuery({
    queryKey: ["biometrics", passengerId],
    queryFn: () => biometricsApi.listHistory(passengerId),
  });

  const enrollMutation = useMutation({
    mutationFn: (file: File) => biometricsApi.enroll(passengerId, file),
    onSuccess: (enrollment) => {
      toast.success(
        `Biometria cadastrada (qualidade: ${(enrollment.quality_score * 100).toFixed(0)}%).`,
      );
      setPendingFile(null);
      setPreviewUrl(null);
      queryClient.invalidateQueries({ queryKey: ["biometrics", passengerId] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: () => biometricsApi.revoke(passengerId),
    onSuccess: () => {
      toast.success("Biometria revogada.");
      queryClient.invalidateQueries({ queryKey: ["biometrics", passengerId] });
    },
  });

  const selectFile = (file: File) => {
    setPendingFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const activeEnrollment = historyQuery.data?.find((item) => item.active);

  return (
    <Stack direction="column" gap={16}>
      <Card title="Biometria atual">
        {historyQuery.isLoading && <Alert type="info" message="Carregando..." />}
        {activeEnrollment ? (
          <Descriptions
            items={[
              { label: "Qualidade", value: `${(activeEnrollment.quality_score * 100).toFixed(0)}%` },
              {
                label: "Modelo",
                value: `${activeEnrollment.model_name} (${activeEnrollment.model_version})`,
              },
              {
                label: "Cadastrada em",
                value: dayjs(activeEnrollment.created_at).format("DD/MM/YYYY HH:mm"),
              },
              { label: "Status", value: <Tag variant="success">Ativa</Tag> },
            ]}
          />
        ) : (
          !historyQuery.isLoading && <Alert type="warning" message="Sem biometria cadastrada." />
        )}

        {activeEnrollment && (
          <Button
            variant="danger"
            className={styles.revokeButton}
            onClick={() => revokeMutation.mutate()}
            loading={revokeMutation.isPending}
          >
            Revogar biometria
          </Button>
        )}
      </Card>

      <Card title="Novo cadastro biométrico">
        <Segmented
          options={[
            { label: "Upload", value: "upload" },
            { label: "Câmera", value: "webcam" },
          ]}
          value={mode}
          onChange={(value) => setMode(value as CaptureMode)}
        />

        <div className={styles.captureArea}>
          {mode === "upload" ? (
            <FileDropzone onFile={selectFile} />
          ) : (
            <WebcamCapture onCapture={selectFile} />
          )}
        </div>

        {previewUrl && (
          <Stack direction="column" gap={12} align="center" className={styles.preview}>
            <img src={previewUrl} alt="Pré-visualização" className={styles.previewImage} />
            <Button
              variant="primary"
              onClick={() => pendingFile && enrollMutation.mutate(pendingFile)}
              loading={enrollMutation.isPending}
            >
              Confirmar cadastro
            </Button>
          </Stack>
        )}

        {enrollMutation.isError && (
          <Alert
            type="error"
            message={extractErrorMessage(enrollMutation.error)}
            className={styles.errorAlert}
          />
        )}
      </Card>
    </Stack>
  );
}
