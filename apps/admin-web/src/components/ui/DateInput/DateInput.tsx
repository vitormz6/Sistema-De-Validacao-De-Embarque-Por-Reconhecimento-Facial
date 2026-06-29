import dayjs from "dayjs";
import { forwardRef } from "react";

import { Input } from "../Input";

interface DateInputProps {
  value: string | null;
  onChange: (value: string | null) => void;
  error?: boolean;
}

/** Native date input — `value`/`onChange` work in plain "YYYY-MM-DD"
 * strings, matching what the backend's `date` fields (e.g. birth_date)
 * expect, no timezone conversion involved. */
export const DateInput = forwardRef<HTMLInputElement, DateInputProps>(function DateInput(
  { value, onChange, error },
  ref,
) {
  return (
    <Input
      ref={ref}
      type="date"
      error={error}
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value || null)}
    />
  );
});

interface DateTimeInputProps {
  value: string | null;
  onChange: (isoValue: string) => void;
  error?: boolean;
}

const LOCAL_FORMAT = "YYYY-MM-DDTHH:mm";

/** Native datetime-local input — `value`/`onChange` work in full ISO 8601
 * (with timezone), matching the backend's `datetime` fields. The native
 * input itself has no timezone concept, so the conversion treats
 * whatever the user typed as local wall-clock time, same behavior the
 * previous date-picker library had. */
export const DateTimeInput = forwardRef<HTMLInputElement, DateTimeInputProps>(
  function DateTimeInput({ value, onChange, error }, ref) {
    const localValue = value && dayjs(value).isValid() ? dayjs(value).format(LOCAL_FORMAT) : "";

    return (
      <Input
        ref={ref}
        type="datetime-local"
        error={error}
        value={localValue}
        onChange={(event) => {
          const raw = event.target.value;
          onChange(raw ? dayjs(raw, LOCAL_FORMAT).toISOString() : "");
        }}
      />
    );
  },
);
