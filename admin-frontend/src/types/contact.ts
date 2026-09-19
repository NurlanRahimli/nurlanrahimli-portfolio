export interface ContactContent {
  id: number;
  projects_built: number;
  email: string;
  phone_number: string;
  created_at: string;
  updated_at: string;
}

export interface ContactContentPayload {
  projects_built: number;
  email: string;
  phone_number: string;
}
