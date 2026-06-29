/**
 * Minimal hand-drawn icon set (Feather-style: 1.75 stroke, 20x20 viewport)
 * — kept in-repo instead of pulling an icon package, since the app only
 * needs a couple dozen of them.
 */
import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Svg({ children, ...props }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export function DashboardIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </Svg>
  );
}

export function UsersIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="9" cy="8" r="3.25" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <path d="M16 9.5c1.5-.3 2.5-1.5 2.5-3a2.9 2.9 0 0 0-2-2.8" />
      <path d="M19 20c0-2.5-1.3-4.6-3.2-5.6" />
    </Svg>
  );
}

export function ListIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M8 6h13" />
      <path d="M8 12h13" />
      <path d="M8 18h13" />
      <path d="M3 6h.01" />
      <path d="M3 12h.01" />
      <path d="M3 18h.01" />
    </Svg>
  );
}

export function LogoutIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </Svg>
  );
}

export function SunIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="4.25" />
      <path d="M12 2.5v2.25M12 19.25v2.25M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2.5 12h2.25M19.25 12h2.25M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6" />
    </Svg>
  );
}

export function MoonIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z" />
    </Svg>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </Svg>
  );
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M6 9l6 6 6-6" />
    </Svg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M5 13l4 4L19 7" />
    </Svg>
  );
}

export function AlertTriangleIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M10.3 3.86L1.82 18a1.5 1.5 0 0 0 1.3 2.25h17.76a1.5 1.5 0 0 0 1.3-2.25L13.7 3.86a1.5 1.5 0 0 0-2.6 0z" />
      <path d="M12 9v4" />
      <path d="M12 16.5h.01" />
    </Svg>
  );
}

export function AlertCircleIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" />
      <path d="M12 16.5h.01" />
    </Svg>
  );
}

export function CameraIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7h1.7l1-1.6A1.5 1.5 0 0 1 9.5 4.6h5a1.5 1.5 0 0 1 1.3.8l1 1.6h1.7A1.5 1.5 0 0 1 20 8.5v9A1.5 1.5 0 0 1 18.5 19h-13A1.5 1.5 0 0 1 4 17.5z" />
      <circle cx="12" cy="13" r="3.2" />
    </Svg>
  );
}

export function UploadIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M12 16V4" />
      <path d="M7 9l5-5 5 5" />
      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
    </Svg>
  );
}

export function EyeIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="2.75" />
    </Svg>
  );
}

export function EyeOffIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M3 3l18 18" />
      <path d="M10.6 5.2A10.8 10.8 0 0 1 12 5c6.4 0 10 7 10 7a14.6 14.6 0 0 1-3 3.9M6.2 6.6C4 8.3 2 11 2 11s2.4 5 7.5 6.6c1 .3 2 .4 2.9.4" />
    </Svg>
  );
}

export function SearchIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </Svg>
  );
}

export function ChevronLeftIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M15 6l-6 6 6 6" />
    </Svg>
  );
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M9 6l6 6-6 6" />
    </Svg>
  );
}

export function PlaneIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M17.8 19.2L16 11l3.5-3.5C21 6 21 4 19 2c-2-2-4-2-5.5-.5L10 5 1.8 6.2c-.5.1-.7.7-.3 1l2.5 2.5-1 4.5 3-1.5 2 2-1.5 3 4.5-1 2.5 2.5c.3.4.9.2 1-.3z" />
    </Svg>
  );
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="M22 4L12 14.01l-3-3" />
    </Svg>
  );
}

export function XCircleIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M15 9l-6 6" />
      <path d="M9 9l6 6" />
    </Svg>
  );
}

export function ActivityIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </Svg>
  );
}

export function WifiOffIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <line x1="2" y1="2" x2="22" y2="22" />
      <path d="M8.5 16.5a5 5 0 0 1 7 0" />
      <path d="M5 12.5a10 10 0 0 1 5.17-2.6" />
      <path d="M19.07 12.5a10 10 0 0 0-5.6-2.74" />
      <path d="M10.7 19.7L12 21l1.3-1.3" />
      <path d="M2 8.82a15 15 0 0 1 4.17-2.65" />
      <path d="M22 8.82a15 15 0 0 0-8.22-3.79" />
    </Svg>
  );
}

export function ArrowLeftIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M19 12H5" />
      <path d="M12 19l-7-7 7-7" />
    </Svg>
  );
}

export function FilterIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </Svg>
  );
}
