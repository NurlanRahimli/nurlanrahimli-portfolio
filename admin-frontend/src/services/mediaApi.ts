import { api } from "../lib/api";
import type { MediaAsset, MediaAssetList, MediaFileType } from "../types/media";

export interface ListMediaParams {
  search?: string;
  fileType?: MediaFileType;
  limit?: number;
  offset?: number;
}

export async function listMedia({
  search,
  fileType,
  limit = 100,
  offset = 0,
}: ListMediaParams = {}): Promise<MediaAssetList> {
  const response = await api.get<MediaAssetList>("/media", {
    params: {
      search: search || undefined,
      file_type: fileType,
      limit,
      offset,
    },
  });

  return response.data;
}

export async function getMedia(assetId: number): Promise<MediaAsset> {
  const response = await api.get<MediaAsset>(`/media/${assetId}`);

  return response.data;
}

export async function uploadMedia(
  file: File,
  altText?: string,
): Promise<MediaAsset> {
  const formData = new FormData();

  formData.append("file", file);

  if (altText?.trim()) {
    formData.append("alt_text", altText.trim());
  }

  const response = await api.post<MediaAsset>("/media", formData);

  return response.data;
}

export async function updateMediaAltText(
  assetId: number,
  altText: string | null,
): Promise<MediaAsset> {
  const response = await api.patch<MediaAsset>(`/media/${assetId}`, {
    alt_text: altText,
  });

  return response.data;
}

export async function deleteMedia(assetId: number): Promise<void> {
  await api.delete(`/media/${assetId}`);
}
