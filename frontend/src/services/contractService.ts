import { apiRequest } from "./api";

export async function fetchContracts() {
  return apiRequest("/contracts");
}

export async function fetchContract(contractId: string) {
  return apiRequest(`/contracts/${contractId}`);
}

export async function fetchContractRisks(contractId: string) {
  return apiRequest(`/risks/contract/${contractId}`);
}

export async function submitReview(data: {
  clause_id: string;
  decision: "ACCEPT" | "OVERRIDE";
  comment: string;
}) {
  return apiRequest("/reviews/submit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
