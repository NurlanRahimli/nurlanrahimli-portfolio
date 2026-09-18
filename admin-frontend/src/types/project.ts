export interface ProjectTag {
  id: number;
  label: string;
  display_order: number;
}

export interface ProjectImage {
  id: number;
  media_asset_id: number;
  label: string | null;
  display_order: number;
  media_url: string | null;
  thumbnail_url: string | null;
  alt_text: string | null;
}

export interface ProjectFeature {
  id: number;
  text: string;
  display_order: number;
}

export interface ProjectTechItem {
  id: number;
  name: string;
  display_order: number;
}

export interface ProjectTechGroup {
  id: number;
  label: string;
  display_order: number;
  items: ProjectTechItem[];
}

export interface ProjectVideo {
  id: number;
  mux_upload_id: string | null;
  mux_asset_id: string | null;
  mux_playback_id: string | null;
  status: string;
  duration_seconds: number | null;
  aspect_ratio: string | null;
  original_filename: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListItem {
  id: number;
  slug: string;
  title: string;
  project_type: string | null;
  short_description: string | null;
  project_date: string | null;
  cover_media_asset_id: number | null;
  cover_url: string | null;
  cover_thumbnail_url: string | null;
  github_url: string | null;
  show_github_link: boolean;
  demo_url: string | null;
  is_featured: boolean;
  is_published: boolean;
  display_order: number;
  tags: ProjectTag[];
  technologies: string[];
  created_at: string;
  updated_at: string;
}

export interface ProjectList {
  items: ProjectListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface Project {
  id: number;
  slug: string;
  title: string;
  project_type: string | null;
  short_description: string | null;
  long_description: string | null;
  project_date: string | null;
  cover_media_asset_id: number | null;
  cover_url: string | null;
  cover_thumbnail_url: string | null;
  github_url: string | null;
  show_github_link: boolean;
  demo_url: string | null;
  is_featured: boolean;
  is_published: boolean;
  display_order: number;
  tags: ProjectTag[];
  images: ProjectImage[];
  features: ProjectFeature[];
  tech_groups: ProjectTechGroup[];
  video: ProjectVideo | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectWritePayload {
  slug?: string | null;
  title: string;
  project_type?: string | null;
  short_description?: string | null;
  long_description?: string | null;
  project_date?: string | null;
  cover_media_asset_id?: number | null;
  github_url?: string | null;
  show_github_link?: boolean;
  demo_url?: string | null;
  is_featured?: boolean;
  is_published?: boolean;
  tags?: Array<{ label: string }>;
  images?: Array<{
    media_asset_id: number;
    label?: string | null;
  }>;
  features?: Array<{ text: string }>;
  tech_groups?: Array<{
    label: string;
    items: Array<{ name: string }>;
  }>;
}

export interface ProjectVideoUploadResponse {
  project_id: number;
  upload_id: string;
  upload_url: string;
  status: string;
}

export type ProjectStatusFilter = "all" | "published" | "draft";
