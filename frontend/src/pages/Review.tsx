import React, { useState } from "react";
import { submitReview } from "../services/contractService";
import { Button } from "../components/common/Button";

export const Review: React.FC = () => {
  const [comment, setComment] = useState("");

  const handleSubmit = (decision: "ACCEPT" | "OVERRIDE") => {
    submitReview({
      clause_id: "example-clause-id",
      decision,
      comment,
    }).then(() => alert("Review submitted"));
  };

  return (
    <div>
      <h1 style={{ fontSize: "20px", fontWeight: 600 }}>Review AI Finding</h1>

      <textarea
        style={{ width: "100%", height: "100px", marginTop: "12px" }}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />

      <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
        <Button onClick={() => handleSubmit("ACCEPT")}>Accept</Button>
        <Button variant="secondary" onClick={() => handleSubmit("OVERRIDE")}>
          Override
        </Button>
      </div>
    </div>
  );
};
