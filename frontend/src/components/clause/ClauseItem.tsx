import React from "react";
import { Badge } from "../common/Badge";

interface ClauseItemProps {
  text: string;
  type: string;
  risk: "LOW" | "MEDIUM" | "HIGH";
}

export const ClauseItem: React.FC<ClauseItemProps> = ({
  text,
  type,
  risk,
}) => {
  return (
    <div style={{ padding: "8px 0", borderBottom: "1px solid #E5E7EB" }}>
      <div style={{ fontSize: "12px", color: "#6B7280" }}>{type}</div>
      <div style={{ fontSize: "14px", margin: "4px 0" }}>{text}</div>
      <Badge label={risk} type={risk} />
    </div>
  );
};
