export interface Education {
  id: number;
  title: string;
  location: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  certification_media_asset_id: number | null;
  certification_filename: string | null;
  certification_url: string | null;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface EducationList {
  items: Education[];
  total: number;
  limit: number;
  offset: number;
}

export interface EducationWritePayload {
  title: string;
  location: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  certification_media_asset_id: number | null;
  is_active: boolean;
}

export type EducationStatusFilter = "all" | "active" | "inactive";
