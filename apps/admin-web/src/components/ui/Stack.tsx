import type { CSSProperties, ReactNode } from "react";

interface StackProps {
  children: ReactNode;
  direction?: "row" | "column";
  gap?: number;
  align?: CSSProperties["alignItems"];
  justify?: CSSProperties["justifyContent"];
  wrap?: boolean;
  style?: CSSProperties;
  className?: string;
}

/** Tiny flexbox helper — replaces ad-hoc inline `style={{ display: "flex" }}`
 * scattered across pages with one consistent component. */
export function Stack({
  children,
  direction = "row",
  gap = 0,
  align,
  justify,
  wrap,
  style,
  className,
}: StackProps) {
  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: direction,
        gap,
        alignItems: align,
        justifyContent: justify,
        flexWrap: wrap ? "wrap" : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
