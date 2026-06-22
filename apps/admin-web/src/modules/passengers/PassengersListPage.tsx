import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { extractErrorMessage } from "@/app/httpClient";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SearchIcon } from "@/components/ui/icons";
import { Select } from "@/components/ui/Select";
import { Stack } from "@/components/ui/Stack";
import { Table, type TableColumn } from "@/components/ui/Table";
import { Tag } from "@/components/ui/Tag";
import { useToast } from "@/components/ui/toast/ToastContext";

import { PassengerFormModal } from "./PassengerFormModal";
import { passengersApi } from "./passengersApi";
import type { PassengerFormValues } from "./passengerSchema";
import type { Passenger, PassengerStatus } from "./types";
import styles from "./PassengersListPage.module.css";

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

const STATUS_OPTIONS = [
  { value: "ACTIVE", label: "Ativo" },
  { value: "BLOCKED", label: "Bloqueado" },
  { value: "INACTIVE", label: "Inativo" },
];

const PAGE_SIZE = 20;

export function PassengersListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState<string>();
  const [statusFilter, setStatusFilter] = useState<PassengerStatus | undefined>();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const passengersQuery = useQuery({
    queryKey: ["passengers", { page, search, statusFilter }],
    queryFn: () =>
      passengersApi.list({ page, page_size: PAGE_SIZE, search, status: statusFilter }),
  });

  const createMutation = useMutation({
    mutationFn: passengersApi.create,
    onSuccess: () => {
      toast.success("Passageiro cadastrado.");
      setIsCreateOpen(false);
      queryClient.invalidateQueries({ queryKey: ["passengers"] });
    },
  });

  const handleCreate = async (values: PassengerFormValues) => {
    await createMutation.mutateAsync({
      full_name: values.full_name,
      document_number: values.document_number,
      birth_date: values.birth_date,
    });
  };

  const columns: TableColumn<Passenger>[] = [
    { key: "full_name", title: "Nome", render: (p) => p.full_name },
    { key: "document_number", title: "Documento", render: (p) => p.document_number },
    {
      key: "status",
      title: "Status",
      render: (p) => (
        <Tag variant={STATUS_VARIANTS[p.status]}>{STATUS_LABELS[p.status]}</Tag>
      ),
    },
  ];

  return (
    <div>
      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.heading}>Passageiros</h2>
          <p className={styles.subheading}>Gerencie cadastros e permissões de embarque</p>
        </div>
        <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
          Novo passageiro
        </Button>
      </div>

      <Stack gap={12} className={styles.filters}>
        <Input
          placeholder="Buscar por nome ou documento"
          suffix={<SearchIcon />}
          wrapperClassName={styles.searchInput}
          onChange={(event) => {
            setPage(1);
            setSearch(event.target.value || undefined);
          }}
        />
        <div className={styles.statusSelect}>
          <Select
            placeholder="Todos os status"
            options={STATUS_OPTIONS}
            onChange={(event) => {
              setPage(1);
              setStatusFilter((event.target.value as PassengerStatus) || undefined);
            }}
          />
        </div>
      </Stack>

      {passengersQuery.isError && (
        <Alert
          type="error"
          message={extractErrorMessage(passengersQuery.error)}
          className={styles.alert}
        />
      )}

      <Table
        rowKey={(passenger) => passenger.id}
        columns={columns}
        data={passengersQuery.data?.items ?? []}
        loading={passengersQuery.isLoading}
        onRowClick={(passenger) => navigate(`/passengers/${passenger.id}`)}
        pagination={{
          page,
          pageSize: PAGE_SIZE,
          total: passengersQuery.data?.total ?? 0,
          onChange: setPage,
        }}
      />

      <PassengerFormModal
        open={isCreateOpen}
        onSubmit={handleCreate}
        onCancel={() => setIsCreateOpen(false)}
      />
    </div>
  );
}
