export interface AdminUser {
  id: number
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
