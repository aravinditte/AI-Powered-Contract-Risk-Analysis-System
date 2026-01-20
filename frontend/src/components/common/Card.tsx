import React from "react";
import { COLORS } from "../../assets/colors";

interface CardProps {
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children }) => {
  return (
    <div
      style={{
        backgroundColor: COLORS.card,
        padding: "16px",
        borderRadius: "6px",
        border: "1px solid #E5E7EB",
      }}
    >
      {children}
    </div>
  );
};
