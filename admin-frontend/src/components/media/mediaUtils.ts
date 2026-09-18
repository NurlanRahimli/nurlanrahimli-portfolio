import type { MediaAsset, MediaVariant } from "../../types/media";

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;

  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(kilobytes >= 100 ? 0 : 1)} KB`;
  }

  const megabytes = kilobytes / 1024;

  return `${megabytes.toFixed(megabytes >= 100 ? 0 : 1)} MB`;
}

export function formatMediaDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function findVariant(
  asset: MediaAsset,
  names: string[],
): MediaVariant | undefined {
  return names
    .map((name) =>
      asset.variants.find((variant) => variant.variant_name === name),
    )
    .find(Boolean);
}

export function getMediaPreviewUrl(asset: MediaAsset): string | null {
  if (asset.file_type !== "image") {
    return null;
  }

  const variant = findVariant(asset, ["small", "medium", "thumbnail", "large"]);

  return variant?.url ?? asset.url;
}

export function getMediaDimensions(asset: MediaAsset): string | null {
  if (!asset.width || !asset.height) {
    return null;
  }

  return `${asset.width} × ${asset.height}`;
}
