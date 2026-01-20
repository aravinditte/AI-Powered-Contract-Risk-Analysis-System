import React from "react";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";

interface ContractListItemProps {
  fileName: string;
  status: string;
  risk: "LOW" | "MEDIUM" | "HIGH";
}

export const ContractListItem: React.FC<ContractListItemProps> = ({
  fileName,
  status,
  risk,
}) => {
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontWeight: 600 }}>{fileName}</div>
          <div style={{ fontSize: "12px", color: "#4B5563" }}>
            Status: {status}
          </div>
        </div>
        <Badge label={risk} type={risk} />
      </div>
    </Card>
  );
};
