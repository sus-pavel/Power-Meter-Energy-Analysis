import { apiClient } from "./client";
import type { CurrentUser, LoginResponse } from "../types/auth";

export async function loginRequest(username: string, password: string): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/auth/login", { username, password });
  return response.data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>("/auth/me");
  return response.data;
}

export async function logoutRequest(): Promise<void> {
  await apiClient.post("/auth/logout");
}
