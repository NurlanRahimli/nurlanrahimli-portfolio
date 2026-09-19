export interface ExperienceHighlight {
  id: number;
  text: string;
  display_order: number;
}

export interface Experience {
  id: number;
  job_title: string;
  company: string;
  location: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  is_active: boolean;
  display_order: number;
  highlights: ExperienceHighlight[];
  created_at: string;
  updated_at: string;
}

export interface ExperienceList {
  items: Experience[];
  total: number;
  limit: number;
  offset: number;
}

export interface ExperienceWritePayload {
  job_title: string;
  company: string;
  location: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  is_active: boolean;
  highlights: Array<{ text: string }>;
}

export type ExperienceStatusFilter = "all" | "active" | "inactive";
