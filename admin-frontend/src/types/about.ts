export type AvailabilityMode = "remote" | "onsite" | "hybrid";

export interface AboutSoftwareField {
  id: number;
  name: string;
  display_order: number;
}

export interface AboutSocialLink {
  id: number;
  platform: string;
  url: string;
  display_order: number;
}

export interface AboutContent {
  id: number;
  full_name: string;
  profile_media_asset_id: number | null;
  profile_image_url: string | null;
  profile_thumbnail_url: string | null;
  resume_media_asset_id: number | null;
  resume_url: string | null;
  resume_filename: string | null;
  about_html: string;
  experience_years: number;
  location: string;
  is_available: boolean;
  availability_modes: AvailabilityMode[];
  software_fields: AboutSoftwareField[];
  social_links: AboutSocialLink[];
  created_at: string;
  updated_at: string;
}

export interface AboutContentPayload {
  full_name: string;
  profile_media_asset_id: number | null;
  resume_media_asset_id: number | null;
  about_html: string;
  experience_years: number;
  location: string;
  is_available: boolean;
  availability_modes: AvailabilityMode[];
  software_fields: Array<{
    name: string;
  }>;
  social_links: Array<{
    platform: string;
    url: string;
  }>;
}
