export type MediaFileType = "image" | "document";

export interface MediaVariant {
  id: number;
  variant_name: string;
  storage_key: string;
  mime_type: string;
  file_size: number;
  width: number;
  height: number;
  created_at: string;
  url: string | null;
}

export interface MediaAsset {
  id: number;
  filename: string;
  original_filename: string;
  storage_key: string;
  mime_type: string;
  file_type: MediaFileType;
  file_size: number;
  width: number | null;
  height: number | null;
  alt_text: string | null;
  created_at: string;
  updated_at: string;
  variants: MediaVariant[];
  url: string | null;
}

export interface MediaAssetList {
  items: MediaAsset[];
  total: number;
  limit: number;
  offset: number;
}

export type MediaFilter = "all" | MediaFileType;
