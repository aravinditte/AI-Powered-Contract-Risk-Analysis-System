import { apiRequest } from "./api";

export async function login(username: string, password: string) {
  const res = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  localStorage.setItem("access_token", res.access_token);
  return res;
}

export function logout() {
  localStorage.removeItem("access_token");
}
