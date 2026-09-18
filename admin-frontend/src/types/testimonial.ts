export interface Testimonial {
  id: number;
  person_name: string;
  testimonial_text: string;
  profile_media_asset_id: number | null;
  profile_image_url: string | null;
  profile_thumbnail_url: string | null;
  linkedin_url: string | null;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface TestimonialList {
  items: Testimonial[];
  total: number;
  limit: number;
  offset: number;
}

export interface TestimonialWritePayload {
  person_name: string;
  testimonial_text: string;
  profile_media_asset_id: number | null;
  linkedin_url: string | null;
  is_active: boolean;
}

export type TestimonialStatusFilter = "all" | "active" | "inactive";
