import React from "react";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";

interface RiskExplanationProps {
  riskLevel: "LOW" | "MEDIUM" | "HIGH";
  explanation: string;
  confidence: number;
  standardClause?: string;
}

export const RiskExplanationPanel: React.FC<RiskExplanationProps> = ({
  riskLevel,
  explanation,
  confidence,
  standardClause,
}) => {
  return (
    <Card>
      <div style={{ marginBottom: "8px" }}>
        <Badge label={riskLevel} type={riskLevel} />
      </div>

      <div style={{ fontSize: "14px", marginBottom: "8px" }}>
        {explanation}
      </div>

      {standardClause && (
        <div style={{ fontSize: "12px", color: "#4B5563" }}>
          <strong>Standard Clause:</strong>
          <div>{standardClause}</div>
        </div>
      )}

      <div style={{ fontSize: "12px", marginTop: "8px" }}>
        Confidence: {(confidence * 100).toFixed(1)}%
      </div>
    </Card>
  );
};
