import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useState } from "react";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { DateInput } from "@/components/ui/DateInput";
import { Descriptions } from "@/components/ui/Descriptions";
import { Drawer } from "@/components/ui/Drawer";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Stack } from "@/components/ui/Stack";
import { Table, type TableColumn } from "@/components/ui/Table";
import { Tag } from "@/components/ui/Tag";

import { validationsApi } from "./validationsApi";
import type { BoardingValidation, ValidationStatus } from "./types";
import styles from "./ValidationsListPage.module.css";

const PAGE_SIZE = 20;

const STATUS_OPTIONS: { value: ValidationStatus; label: string }[] = [
  { value: "AUTHORIZED", label: "Autorizado" },
  { value: "DENIED_NO_ACTIVE_TICKET", label: "Sem passagem ativa" },
  { value: "DENIED_LOW_CONFIDENCE", label: "Baixa confiança" },
  { value: "DENIED_FACE_NOT_FOUND", label: "Rosto não encontrado" },
  { value: "DENIED_SPOOF_SUSPECTED", label: "Suspeita de fraude" },
  { value: "DENIED_PASSENGER_BLOCKED", label: "Passageiro bloqueado" },
];

const STATUS_DISPLAY: Record<ValidationStatus, string> = {
  AUTHORIZED: "Autorizado",
  DENIED_NO_ACTIVE_TICKET: "Sem passagem",
  DENIED_LOW_CONFIDENCE: "Baixa confiança",
  DENIED_FACE_NOT_FOUND: "Rosto não encontrado",
  DENIED_SPOOF_SUSPECTED: "Suspeita de fraude",
  DENIED_PASSENGER_BLOCKED: "Passageiro bloqueado",
};

function statusVariant(status: ValidationStatus): "success" | "danger" {
  return status === "AUTHORIZED" ? "success" : "danger";
}

export function ValidationsListPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<ValidationStatus | undefined>();
  const [busIdFilter, setBusIdFilter] = useState<string>();
  const [dateFrom, setDateFrom] = useState<string | null>(null);
  const [dateTo, setDateTo] = useState<string | null>(null);
  const [selected, setSelected] = useState<BoardingValidation | null>(null);

  const validationsQuery = useQuery({
    queryKey: ["validations", { page, statusFilter, busIdFilter, dateFrom, dateTo }],
    queryFn: () =>
      validationsApi.list({
        page,
        page_size: PAGE_SIZE,
        status: statusFilter,
        bus_id: busIdFilter,
        captured_from: dateFrom ? dayjs(dateFrom).startOf("day").toISOString() : undefined,
        captured_to: dateTo ? dayjs(dateTo).endOf("day").toISOString() : undefined,
      }),
  });

  const columns: TableColumn<BoardingValidation>[] = [
    {
      key: "captured_at",
      title: "Capturado em",
      render: (v) => dayjs(v.captured_at).format("DD/MM/YYYY HH:mm"),
    },
    { key: "bus_id", title: "Ônibus", render: (v) => v.bus_id },
    {
      key: "status",
      title: "Status",
      render: (v) => (
        <Tag variant={statusVariant(v.status)}>{STATUS_DISPLAY[v.status]}</Tag>
      ),
    },
    {
      key: "confidence_score",
      title: "Confiança",
      render: (v) =>
        v.confidence_score != null ? `${(v.confidence_score * 100).toFixed(0)}%` : "—",
    },
    {
      key: "is_offline",
      title: "Captura",
      render: (v) => (v.is_offline ? <Tag>Offline</Tag> : <Tag variant="info">Online</Tag>),
    },
  ];

  return (
    <div>
      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.heading}>Validações</h2>
          <p className={styles.subheading}>Histórico de tentativas de embarque</p>
        </div>
      </div>

      <div className={styles.filtersCard}>
        <Stack gap={12} wrap>
          <div className={styles.statusSelect}>
            <Select
              placeholder="Todos os status"
              options={STATUS_OPTIONS}
              onChange={(event) => {
                setPage(1);
                setStatusFilter((event.target.value as ValidationStatus) || undefined);
              }}
            />
          </div>
          <Input
            placeholder="ID do ônibus"
            wrapperClassName={styles.busInput}
            onChange={(event) => {
              setPage(1);
              setBusIdFilter(event.target.value || undefined);
            }}
          />
          <Stack gap={8} align="center">
            <span className={styles.dateLabel}>De</span>
            <DateInput
              value={dateFrom}
              onChange={(value) => {
                setPage(1);
                setDateFrom(value);
              }}
            />
            <span className={styles.dateLabel}>Até</span>
            <DateInput
              value={dateTo}
              onChange={(value) => {
                setPage(1);
                setDateTo(value);
              }}
            />
          </Stack>
        </Stack>
      </div>

      {validationsQuery.isError && (
        <Alert
          type="error"
          message={extractErrorMessage(validationsQuery.error)}
          className={styles.alert}
        />
      )}

      <Table
        rowKey={(validation) => validation.id}
        columns={columns}
        data={validationsQuery.data?.items ?? []}
        loading={validationsQuery.isLoading}
        onRowClick={setSelected}
        pagination={{
          page,
          pageSize: PAGE_SIZE,
          total: validationsQuery.data?.total ?? 0,
          onChange: setPage,
        }}
      />

      <Drawer
        title="Detalhes da validação"
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
      >
        {selected && (
          <Descriptions
            items={[
              {
                label: "Status",
                value: (
                  <Tag variant={statusVariant(selected.status)}>
                    {STATUS_DISPLAY[selected.status]}
                  </Tag>
                ),
              },
              { label: "Motivo", value: selected.reason_code ?? "—" },
              { label: "Ônibus", value: selected.bus_id },
              { label: "Linha", value: selected.route_id ?? "—" },
              { label: "Passageiro", value: selected.passenger_id ?? "Não identificado" },
              { label: "Passagem", value: selected.ticket_id ?? "—" },
              {
                label: "Confiança",
                value:
                  selected.confidence_score != null
                    ? `${(selected.confidence_score * 100).toFixed(1)}%`
                    : "—",
              },
              { label: "Distância", value: selected.similarity_distance ?? "—" },
              {
                label: "Capturado em",
                value: dayjs(selected.captured_at).format("DD/MM/YYYY HH:mm:ss"),
              },
              {
                label: "Sincronizado em",
                value: dayjs(selected.synced_at).format("DD/MM/YYYY HH:mm:ss"),
              },
              { label: "Capturado offline", value: selected.is_offline ? "Sim" : "Não" },
            ]}
          />
        )}
      </Drawer>
    </div>
  );
}
