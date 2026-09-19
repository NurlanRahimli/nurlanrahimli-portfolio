export interface Skill {
  id: number;
  name: string;
  media_asset_id: number;
  image_url: string | null;
  thumbnail_url: string | null;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface SkillListResponse {
  items: Skill[];
  total: number;
  limit: number;
  offset: number;
}

export interface SkillPayload {
  name: string;
  media_asset_id: number;
  is_active: boolean;
}

export interface SkillReorderItem {
  id: number;
  display_order: number;
}
