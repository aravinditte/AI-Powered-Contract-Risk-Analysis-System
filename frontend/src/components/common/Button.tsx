import React from "react";
import { COLORS } from "../../assets/colors";

type ButtonVariant = "primary" | "secondary";

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = "primary",
  disabled = false,
}) => {
  const baseStyle: React.CSSProperties = {
    padding: "8px 16px",
    fontSize: "14px",
    fontWeight: 500,
    borderRadius: "4px",
    cursor: disabled ? "not-allowed" : "pointer",
    border: "1px solid transparent",
  };

  const variantStyle: React.CSSProperties =
    variant === "primary"
      ? {
          backgroundColor: COLORS.primary,
          color: "#FFFFFF",
        }
      : {
          backgroundColor: "transparent",
          color: COLORS.primary,
          border: `1px solid ${COLORS.primary}`,
        };

  return (
    <button
      style={{ ...baseStyle, ...variantStyle }}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
