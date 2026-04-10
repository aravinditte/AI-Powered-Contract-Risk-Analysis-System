import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { ContractDetail } from "./pages/ContractDetail";
import { Review } from "./pages/Review";
import { Reports } from "./pages/Reports";

export const App: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/contracts/:id" element={<ContractDetail />} />
      <Route path="/review" element={<Review />} />
      <Route path="/reports" element={<Reports />} />
    </Routes>
  </BrowserRouter>
);
