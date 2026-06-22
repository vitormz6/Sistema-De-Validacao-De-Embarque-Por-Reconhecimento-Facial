import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Descriptions } from "@/components/ui/Descriptions";
import { Skeleton } from "@/components/ui/Skeleton";
import { Stack } from "@/components/ui/Stack";
import { Tabs } from "@/components/ui/Tabs";
import { Tag } from "@/components/ui/Tag";
import { ArrowLeftIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { BiometricEnrollmentPanel } from "@/modules/biometrics/BiometricEnrollmentPanel";
import { TicketsPanel } from "@/modules/tickets/TicketsPanel";

import { PassengerFormModal } from "./PassengerFormModal";
import { passengersApi } from "./passengersApi";
import type { PassengerFormValues } from "./passengerSchema";
import type { PassengerStatus } from "./types";
import styles from "./PassengerDetailPage.module.css";

const STATUS_VARIANTS: Record<PassengerStatus, "success" | "danger" | "default"> = {
  ACTIVE: "success",
  BLOCKED: "danger",
  INACTIVE: "default",
};

const STATUS_LABELS: Record<PassengerStatus, string> = {
  ACTIVE: "Ativo",
  BLOCKED: "Bloqueado",
  INACTIVE: "Inativo",
};

export function PassengerDetailPage() {
  const { passengerId } = useParams<{ passengerId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [isEditOpen, setIsEditOpen] = useState(false);

  const passengerQuery = useQuery({
    queryKey: ["passenger", passengerId],
    queryFn: () => passengersApi.getById(passengerId!),
    enabled: Boolean(passengerId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["passenger", passengerId] });

  const updateMutation = useMutation({
    mutationFn: (values: PassengerFormValues) => passengersApi.update(passengerId!, values),
    onSuccess: () => {
      toast.success("Dados atualizados.");
      setIsEditOpen(false);
      invalidate();
    },
  });

  const blockMutation = useMutation({
    mutationFn: () => passengersApi.block(passengerId!),
    onSuccess: () => {
      toast.success("Passageiro bloqueado.");
      invalidate();
    },
  });

  const activateMutation = useMutation({
    mutationFn: () => passengersApi.activate(passengerId!),
    onSuccess: () => {
      toast.success("Passageiro ativado.");
      invalidate();
    },
  });

  if (passengerQuery.isLoading) {
    return (
      <div>
        <div className={styles.backRow}>
          <Skeleton rows={1} height={18} />
        </div>
        <Skeleton rows={4} height={20} />
      </div>
    );
  }

  if (passengerQuery.isError) {
    return <Alert type="error" message={extractErrorMessage(passengerQuery.error)} />;
  }

  const passenger = passengerQuery.data;
  if (!passenger) return null;

  return (
    <div>
      <button
        type="button"
        className={styles.backButton}
        onClick={() => navigate("/passengers")}
      >
        <ArrowLeftIcon />
        Voltar para Passageiros
      </button>

      <Card className={styles.profileCard}>
        <Stack justify="space-between" align="flex-start">
          <div className={styles.profileInfo}>
            <div className={styles.profileAvatar}>
              {passenger.full_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className={styles.profileName}>{passenger.full_name}</h2>
              <Tag variant={STATUS_VARIANTS[passenger.status]}>
                {STATUS_LABELS[passenger.status]}
              </Tag>
            </div>
          </div>

          <Stack gap={8}>
            <Button onClick={() => setIsEditOpen(true)}>Editar</Button>
            {passenger.status === "BLOCKED" ? (
              <Button
                onClick={() => activateMutation.mutate()}
                loading={activateMutation.isPending}
              >
                Ativar
              </Button>
            ) : (
              <Button
                variant="danger"
                onClick={() => blockMutation.mutate()}
                loading={blockMutation.isPending}
              >
                Bloquear
              </Button>
            )}
          </Stack>
        </Stack>

        <div className={styles.profileDetails}>
          <Descriptions
            items={[
              { label: "Documento", value: passenger.document_number },
              { label: "Data de nascimento", value: passenger.birth_date ?? "—" },
              { label: "Status", value: STATUS_LABELS[passenger.status] },
            ]}
          />
        </div>
      </Card>

      <div className={styles.tabsSection}>
        <Tabs
          items={[
            {
              key: "biometrics",
              label: "Biometria",
              children: <BiometricEnrollmentPanel passengerId={passenger.id} />,
            },
            {
              key: "tickets",
              label: "Passagens",
              children: <TicketsPanel passengerId={passenger.id} />,
            },
          ]}
        />
      </div>

      <PassengerFormModal
        open={isEditOpen}
        passenger={passenger}
        onSubmit={async (values) => {
          await updateMutation.mutateAsync(values);
        }}
        onCancel={() => setIsEditOpen(false)}
      />
    </div>
  );
}
