export type UserRole = "admin" | "chief_engineer" | "analyst" | "guest";

export interface CurrentUser {
  id: number;
  username: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
