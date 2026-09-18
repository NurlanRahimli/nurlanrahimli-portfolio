import { useCallback, useEffect, useRef, useState } from "react";
import { AxiosError } from "axios";
import { motion } from "framer-motion";
import {
  FileText,
  Image,
  Library,
  RefreshCw,
  Search,
  Upload,
  X,
} from "lucide-react";
import { DeleteMediaModal } from "../components/media/DeleteMediaModal";
import { MediaCard } from "../components/media/MediaCard";
import { MediaDetailsModal } from "../components/media/MediaDetailsModal";
import { MediaUploadDropzone } from "../components/media/MediaUploadDropzone";
import { useToast } from "../context/toastContext";
import {
  deleteMedia,
  getMedia,
  listMedia,
  updateMediaAltText,
  uploadMedia,
} from "../services/mediaApi";
import type { MediaAsset, MediaFilter } from "../types/media";

const filters: Array<{
  value: MediaFilter;
  label: string;
}> = [
  { value: "all", label: "All media" },
  { value: "image", label: "Images" },
  { value: "document", label: "Documents" },
];

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as
      | {
          detail?: string | Array<{ msg?: string }>;
        }
      | undefined;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail)) {
      const message = data.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join(", ");

      if (message) {
        return message;
      }
    }
  }

  return "Something went wrong. Please try again.";
}

export function MediaLibraryPage() {
  const { showToast } = useToast();

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<MediaFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<MediaAsset | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<MediaAsset | null>(null);

  const requestIdRef = useRef(0);

  const loadMedia = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    setIsLoading(true);

    try {
      const data = await listMedia({
        search: search || undefined,
        fileType: filter === "all" ? undefined : filter,
        limit: 100,
      });

      if (requestId !== requestIdRef.current) {
        return;
      }

      setAssets(data.items);
      setTotal(data.total);
    } catch (error) {
      if (requestId !== requestIdRef.current) {
        return;
      }

      setAssets([]);
      setTotal(0);

      showToast({
        title: "Unable to load media",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      if (requestId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  }, [filter, search, showToast]);

  useEffect(() => {
    let isCancelled = false;

    queueMicrotask(() => {
      if (!isCancelled) {
        void loadMedia();
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [loadMedia]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setSearch(searchInput.trim());
    }, 300);

    return () => window.clearTimeout(timeout);
  }, [searchInput]);

  async function handleUpload(files: File[]) {
    if (!files.length || isUploading) {
      return;
    }

    setIsUploading(true);

    let uploaded = 0;

    try {
      for (const file of files) {
        await uploadMedia(file);
        uploaded += 1;
      }

      showToast({
        title: uploaded === 1 ? "Media uploaded" : "Media files uploaded",
        message:
          uploaded === 1
            ? `${files[0].name} is ready to use.`
            : `${uploaded} files are ready to use.`,
        type: "success",
      });

      await loadMedia();
    } catch (error) {
      showToast({
        title: "Upload failed",
        message:
          uploaded > 0
            ? `${uploaded} file${
                uploaded === 1 ? "" : "s"
              } uploaded before the error. ${getErrorMessage(error)}`
            : getErrorMessage(error),
        type: "error",
      });

      await loadMedia();
    } finally {
      setIsUploading(false);
    }
  }

  async function handleSelect(asset: MediaAsset) {
    try {
      const latestAsset = await getMedia(asset.id);
      setSelectedAsset(latestAsset);
    } catch (error) {
      showToast({
        title: "Unable to open asset",
        message: getErrorMessage(error),
        type: "error",
      });
    }
  }

  async function handleSaveAltText(asset: MediaAsset, altText: string) {
    setIsSaving(true);

    try {
      const updated = await updateMediaAltText(
        asset.id,
        altText.trim() || null,
      );

      setSelectedAsset(updated);

      setAssets((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );

      showToast({
        title: "Changes saved",
        message: "Alt text has been updated.",
        type: "success",
      });
    } catch (error) {
      showToast({
        title: "Unable to save changes",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCopyUrl(url: string) {
    try {
      await navigator.clipboard.writeText(url);

      showToast({
        title: "URL copied",
        message: "The public media URL is on your clipboard.",
        type: "info",
      });
    } catch {
      showToast({
        title: "Unable to copy URL",
        message: "Your browser did not allow clipboard access.",
        type: "error",
      });
    }
  }

  async function handleDelete() {
    if (!deleteTarget || isDeleting) {
      return;
    }

    const target = deleteTarget;

    setIsDeleting(true);

    try {
      await deleteMedia(target.id);

      setDeleteTarget(null);
      setSelectedAsset(null);

      setAssets((current) => current.filter((asset) => asset.id !== target.id));

      setTotal((current) => Math.max(0, current - 1));

      showToast({
        title: "Asset deleted",
        message: `${target.original_filename} was permanently removed.`,
        type: "success",
      });

      await loadMedia();
    } catch (error) {
      showToast({
        title: "Unable to delete asset",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsDeleting(false);
    }
  }

  const imageCount = assets.filter(
    (asset) => asset.file_type === "image",
  ).length;

  const documentCount = assets.filter(
    (asset) => asset.file_type === "document",
  ).length;

  return (
    <motion.div
      className="admin-page media-library-page"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="admin-page-header media-page-header">
        <div>
          <span className="admin-eyebrow">Content Assets</span>

          <h1>Media Library</h1>

          <p>
            Upload and organize the images and documents used across your
            portfolio.
          </p>
        </div>

        <div className="media-page-header__summary">
          <span>
            <Library size={17} />
            {total} {total === 1 ? "asset" : "assets"}
          </span>

          <span>
            <Image size={17} />
            {imageCount} images
          </span>

          <span>
            <FileText size={17} />
            {documentCount} documents
          </span>
        </div>
      </header>

      <MediaUploadDropzone
        isUploading={isUploading}
        onFilesSelected={(files) => {
          void handleUpload(files);
        }}
      />

      <section className="media-toolbar">
        <div className="media-search">
          <Search size={19} />

          <input
            type="search"
            value={searchInput}
            placeholder="Search media..."
            aria-label="Search media"
            onChange={(event) => setSearchInput(event.target.value)}
          />

          {searchInput && (
            <button
              type="button"
              aria-label="Clear search"
              onClick={() => setSearchInput("")}
            >
              <X size={17} />
            </button>
          )}
        </div>

        <div className="media-filters" aria-label="Filter media">
          {filters.map((item) => (
            <button
              key={item.value}
              className={
                filter === item.value
                  ? "media-filter media-filter--active"
                  : "media-filter"
              }
              type="button"
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <button
          className="media-refresh"
          type="button"
          disabled={isLoading}
          onClick={() => {
            void loadMedia();
          }}
          aria-label="Refresh media"
          title="Refresh media"
        >
          <RefreshCw
            className={isLoading ? "media-refresh__spinning" : undefined}
            size={19}
          />
        </button>
      </section>

      <div className="media-results-heading">
        <div>
          <strong>
            {filter === "all"
              ? "All media"
              : filter === "image"
                ? "Images"
                : "Documents"}
          </strong>

          <span>
            {isLoading
              ? "Loading..."
              : `${total} ${total === 1 ? "result" : "results"}`}
          </span>
        </div>
      </div>

      {isLoading && assets.length === 0 ? (
        <div
          className="media-grid media-grid--loading"
          aria-label="Loading media"
        >
          {Array.from({ length: 8 }).map((_, index) => (
            <div className="media-card media-card--skeleton" key={index}>
              <div className="media-card__preview" />
              <div className="media-card__body">
                <span />
                <span />
                <span />
              </div>
            </div>
          ))}
        </div>
      ) : assets.length > 0 ? (
        <section className="media-grid" aria-label="Media assets">
          {assets.map((asset, index) => (
            <MediaCard
              key={asset.id}
              asset={asset}
              index={index}
              onSelect={(item) => {
                void handleSelect(item);
              }}
            />
          ))}
        </section>
      ) : (
        <section className="media-empty-state">
          <div className="media-empty-state__icon">
            {search || filter !== "all" ? (
              <Search size={30} />
            ) : (
              <Upload size={30} />
            )}
          </div>

          <h2>
            {search || filter !== "all"
              ? "No media found"
              : "Your media library is empty"}
          </h2>

          <p>
            {search || filter !== "all"
              ? "Try another search or change the active filter."
              : "Upload your first image or PDF using the dropzone above."}
          </p>
        </section>
      )}

      <MediaDetailsModal
        key={selectedAsset?.id ?? "closed"}
        asset={selectedAsset}
        isSaving={isSaving}
        onClose={() => setSelectedAsset(null)}
        onSave={(asset, altText) => {
          void handleSaveAltText(asset, altText);
        }}
        onDelete={(asset) => {
          setDeleteTarget(asset);
        }}
        onCopyUrl={(url) => {
          void handleCopyUrl(url);
        }}
      />

      <DeleteMediaModal
        asset={deleteTarget}
        isDeleting={isDeleting}
        onCancel={() => {
          if (!isDeleting) {
            setDeleteTarget(null);
          }
        }}
        onConfirm={() => {
          void handleDelete();
        }}
      />
    </motion.div>
  );
}
