import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchContractRisks } from "../services/contractService";
import { RiskExplanationPanel } from "../components/risk/RiskExplanationPanel";

export const ContractDetail: React.FC = () => {
  const { id } = useParams();
  const [risks, setRisks] = useState<any[]>([]);

  useEffect(() => {
    if (!id) return;
    fetchContractRisks(id)
      .then((res) => setRisks(res.risks))
      .catch(console.error);
  }, [id]);

  return (
    <div>
      <h1 style={{ fontSize: "20px", fontWeight: 600 }}>
        Contract Risk Details
      </h1>

      <div style={{ marginTop: "16px", display: "grid", gap: "16px" }}>
        {risks.map((risk, index) => (
          <RiskExplanationPanel
            key={index}
            riskLevel={risk.risk_level}
            explanation={risk.explanation}
            confidence={risk.confidence}
            standardClause={risk.compared_standard_clause}
          />
        ))}
      </div>
    </div>
  );
};
