export interface Contract {
  id: string;
  file_name: string;
  status: string;
  overall_risk: "LOW" | "MEDIUM" | "HIGH";
}
