import React from "react";
import { COLORS } from "../../assets/colors";

interface BadgeProps {
  label: string;
  type: "LOW" | "MEDIUM" | "HIGH";
}

export const Badge: React.FC<BadgeProps> = ({ label, type }) => {
  const colorMap = {
    LOW: COLORS.riskLow,
    MEDIUM: COLORS.riskMedium,
    HIGH: COLORS.riskHigh,
  };

  return (
    <span
      style={{
        padding: "4px 8px",
        fontSize: "12px",
        fontWeight: 600,
        borderRadius: "4px",
        color: colorMap[type],
        border: `1px solid ${colorMap[type]}`,
      }}
    >
      {label}
    </span>
  );
};
