import React, { useEffect, useState } from "react";
import { fetchContracts } from "../services/contractService";
import { ContractListItem } from "../components/contract/ContractListItem";

export const Dashboard: React.FC = () => {
  const [contracts, setContracts] = useState<any[]>([]);

  useEffect(() => {
    fetchContracts()
      .then(setContracts)
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: "20px", fontWeight: 600 }}>Contracts</h1>

      <div style={{ marginTop: "16px", display: "grid", gap: "12px" }}>
        {contracts.map((c) => (
          <ContractListItem
            key={c.id}
            fileName={c.file_name}
            status={c.status}
            risk={c.overall_risk}
          />
        ))}
      </div>
    </div>
  );
};
