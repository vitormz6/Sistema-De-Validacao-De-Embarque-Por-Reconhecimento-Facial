import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useState } from "react";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Stack } from "@/components/ui/Stack";
import { Table, type TableColumn } from "@/components/ui/Table";
import { Tag } from "@/components/ui/Tag";

import { TicketFormModal } from "./TicketFormModal";
import { ticketsApi } from "./ticketsApi";
import type { TicketFormValues } from "./ticketSchema";
import type { Ticket, TicketStatus } from "./types";
import styles from "./TicketsPanel.module.css";

interface TicketsPanelProps {
  passengerId: string;
}

const STATUS_VARIANTS: Record<TicketStatus, "success" | "default" | "danger"> = {
  ACTIVE: "success",
  EXPIRED: "default",
  BLOCKED: "danger",
  CANCELLED: "default",
};

export function TicketsPanel({ passengerId }: TicketsPanelProps) {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const ticketsQuery = useQuery({
    queryKey: ["tickets", passengerId],
    queryFn: () => ticketsApi.list({ passenger_id: passengerId, page: 1, page_size: 100 }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["tickets", passengerId] });

  const createMutation = useMutation({
    mutationFn: (values: TicketFormValues) =>
      ticketsApi.create({ passenger_id: passengerId, ...values }),
    onSuccess: () => {
      setIsCreateOpen(false);
      invalidate();
    },
  });

  const blockMutation = useMutation({
    mutationFn: ticketsApi.block,
    onSuccess: invalidate,
  });

  const activateMutation = useMutation({
    mutationFn: ticketsApi.activate,
    onSuccess: invalidate,
  });

  const columns: TableColumn<Ticket>[] = [
    { key: "ticket_type", title: "Tipo", render: (ticket) => ticket.ticket_type },
    {
      key: "status",
      title: "Status",
      render: (ticket) => <Tag variant={STATUS_VARIANTS[ticket.status]}>{ticket.status}</Tag>,
    },
    {
      key: "valid_from",
      title: "Válida de",
      render: (ticket) => dayjs(ticket.valid_from).format("DD/MM/YYYY HH:mm"),
    },
    {
      key: "valid_until",
      title: "Válida até",
      render: (ticket) => dayjs(ticket.valid_until).format("DD/MM/YYYY HH:mm"),
    },
    {
      key: "actions",
      title: "Ações",
      render: (ticket) =>
        ticket.status === "BLOCKED" ? (
          <Button size="sm" onClick={() => activateMutation.mutate(ticket.id)}>
            Ativar
          </Button>
        ) : (
          <Button size="sm" variant="danger" onClick={() => blockMutation.mutate(ticket.id)}>
            Bloquear
          </Button>
        ),
    },
  ];

  return (
    <div>
      <Stack justify="flex-end" className={styles.headerRow}>
        <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
          Nova passagem
        </Button>
      </Stack>

      {ticketsQuery.isError && (
        <Alert
          type="error"
          message={extractErrorMessage(ticketsQuery.error)}
          className={styles.alert}
        />
      )}

      <Table
        rowKey={(ticket) => ticket.id}
        columns={columns}
        data={ticketsQuery.data?.items ?? []}
        loading={ticketsQuery.isLoading}
        emptyText="Nenhuma passagem cadastrada."
      />

      <TicketFormModal
        open={isCreateOpen}
        onSubmit={async (values) => {
          await createMutation.mutateAsync(values);
        }}
        onCancel={() => setIsCreateOpen(false)}
      />
    </div>
  );
}
