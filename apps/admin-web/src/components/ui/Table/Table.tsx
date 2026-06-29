import type { ReactNode } from "react";

import { ChevronLeftIcon, ChevronRightIcon } from "../icons";
import { Skeleton } from "../Skeleton";
import styles from "./Table.module.css";

export interface TableColumn<T> {
  key: string;
  title: ReactNode;
  render: (record: T) => ReactNode;
  width?: string;
}

interface TablePagination {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  rowKey: (record: T) => string;
  loading?: boolean;
  onRowClick?: (record: T) => void;
  emptyText?: string;
  pagination?: TablePagination;
}

export function Table<T>({
  columns,
  data,
  rowKey,
  loading,
  onRowClick,
  emptyText = "Nenhum registro encontrado.",
  pagination,
}: TableProps<T>) {
  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1;

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} style={{ width: column.width }}>
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 5 }, (_, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column.key}>
                    <Skeleton height={16} />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={styles.empty}>
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((record) => (
              <tr
                key={rowKey(record)}
                onClick={onRowClick ? () => onRowClick(record) : undefined}
                className={onRowClick ? styles.clickableRow : undefined}
              >
                {columns.map((column) => (
                  <td key={column.key}>{column.render(record)}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {pagination && (
        <div className={styles.pagination}>
          <span className={styles.pageInfo}>
            Página {pagination.page} de {totalPages} · {pagination.total} registros
          </span>
          <div className={styles.pageControls}>
            <button
              type="button"
              className={styles.pageButton}
              disabled={pagination.page <= 1}
              onClick={() => pagination.onChange(pagination.page - 1)}
              aria-label="Página anterior"
            >
              <ChevronLeftIcon />
            </button>
            <button
              type="button"
              className={styles.pageButton}
              disabled={pagination.page >= totalPages}
              onClick={() => pagination.onChange(pagination.page + 1)}
              aria-label="Próxima página"
            >
              <ChevronRightIcon />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
