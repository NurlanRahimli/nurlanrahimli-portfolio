import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  Check,
  FileText,
  Image as ImageIcon,
  LoaderCircle,
  Search,
  Upload,
  X,
} from "lucide-react";
import {
  type ChangeEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { useToast } from "../../context/toastContext";
import { listMedia, uploadMedia } from "../../services/mediaApi";
import type { MediaAsset, MediaFileType } from "../../types/media";
import { formatFileSize, getMediaPreviewUrl } from "../media/mediaUtils";

type ContentMediaPickerMode = "profile" | "resume" | "skill";

interface ContentMediaPickerProps {
  isOpen: boolean;
  mode: ContentMediaPickerMode;
  selectedId: number | null;
  onClose: () => void;
  onSelect: (asset: MediaAsset) => void;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as
      { detail?: string | Array<{ msg?: string }> } | undefined;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail)) {
      const messages = data.detail
        .map((item) => item.msg)
        .filter((message): message is string => Boolean(message));

      if (messages.length > 0) {
        return messages.join(" ");
      }
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

function isValidUpload(file: File, mode: ContentMediaPickerMode): boolean {
  if (mode === "profile" || mode === "skill") {
    return file.type.startsWith("image/");
  }

  return (
    file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
  );
}

export function ContentMediaPicker({
  isOpen,
  mode,
  selectedId,
  onClose,
  onSelect,
}: ContentMediaPickerProps) {
  const { showToast } = useToast();

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [pendingId, setPendingId] = useState<number | null>(selectedId);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const uploadInputRef = useRef<HTMLInputElement>(null);

  const isProfile = mode === "profile";
  const isSkill = mode === "skill";
  const isImageMode = isProfile || isSkill;
  const fileType: MediaFileType = isImageMode ? "image" : "document";

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 250);

    return () => window.clearTimeout(timer);
  }, [search]);

  const loadAssets = useCallback(async () => {
    setIsLoading(true);

    try {
      const result = await listMedia({
        search: debouncedSearch || undefined,
        fileType,
        limit: 100,
        offset: 0,
      });

      const filteredAssets = isImageMode
        ? result.items
        : result.items.filter(
            (asset) =>
              asset.mime_type === "application/pdf" ||
              asset.original_filename.toLowerCase().endsWith(".pdf"),
          );

      setAssets(filteredAssets);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load media",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, fileType, isImageMode, showToast]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    let cancelled = false;

    queueMicrotask(() => {
      if (!cancelled) {
        setPendingId(selectedId);
        void loadAssets();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [isOpen, loadAssets, selectedId]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  async function handleUpload(file: File) {
    if (isUploading) {
      return;
    }

    if (!isValidUpload(file, mode)) {
      showToast({
        type: "error",
        title: isImageMode ? "Images only" : "PDF required",
        message: isSkill
          ? "Skill logos must be image files."
          : isProfile
            ? "Profile photos must be image files."
            : "Your résumé must be uploaded as a PDF document.",
      });
      return;
    }

    setIsUploading(true);

    try {
      const uploaded = await uploadMedia(file);

      if (
        (!isImageMode && uploaded.file_type !== "document") ||
        (isImageMode && uploaded.file_type !== "image")
      ) {
        throw new Error("The uploaded asset has an unexpected file type.");
      }

      if (
        !isImageMode &&
        uploaded.mime_type !== "application/pdf" &&
        !uploaded.original_filename.toLowerCase().endsWith(".pdf")
      ) {
        throw new Error("The uploaded résumé is not a PDF.");
      }

      setSearch("");
      setDebouncedSearch("");
      setAssets((current) => [
        uploaded,
        ...current.filter((asset) => asset.id !== uploaded.id),
      ]);
      setPendingId(uploaded.id);

      showToast({
        type: "success",
        title: isSkill
          ? "Logo uploaded"
          : isProfile
            ? "Photo uploaded"
            : "Résumé uploaded",
        message: `${uploaded.original_filename} was uploaded to Media Library and selected.`,
      });
    } catch (error) {
      showToast({
        type: "error",
        title: isSkill
          ? "Could not upload logo"
          : isProfile
            ? "Could not upload photo"
            : "Could not upload résumé",
        message: getErrorMessage(error),
      });
    } finally {
      setIsUploading(false);
    }
  }

  function handleUploadInput(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (file) {
      void handleUpload(file);
    }
  }

  function confirmSelection() {
    const asset = assets.find((item) => item.id === pendingId);

    if (!asset) {
      return;
    }

    onSelect(asset);
    onClose();
  }

  const title = isSkill
    ? "Choose skill logo"
    : isProfile
      ? "Choose profile image"
      : "Choose résumé";

  const description = isSkill
    ? "Select an existing technology logo or upload a new image to your Media Library."
    : isProfile
      ? "Select an existing portrait or upload a new image to your Media Library."
      : "Select an existing PDF or upload a new résumé to your Media Library.";

  return (
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          className="content-media-picker"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            className="content-media-picker__backdrop"
            type="button"
            aria-label="Close media picker"
            onClick={onClose}
          />

          <motion.div
            className="content-media-picker__dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="content-media-picker-title"
            initial={{ opacity: 0, y: 18, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.985 }}
            transition={{ duration: 0.2 }}
          >
            <header className="content-media-picker__header">
              <div>
                <span className="admin-eyebrow">Media Library</span>
                <h2 id="content-media-picker-title">{title}</h2>
                <p>{description}</p>
              </div>

              <button
                className="content-media-picker__close"
                type="button"
                aria-label="Close"
                onClick={onClose}
              >
                <X size={20} />
              </button>
            </header>

            <div className="content-media-picker__toolbar">
              <label className="content-media-picker__search">
                <Search size={18} />
                <input
                  type="search"
                  value={search}
                  placeholder={
                    isImageMode ? "Search images..." : "Search PDFs..."
                  }
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>

              <input
                ref={uploadInputRef}
                type="file"
                accept={
                  isImageMode
                    ? "image/jpeg,image/png,image/webp,image/avif"
                    : "application/pdf,.pdf"
                }
                hidden
                onChange={handleUploadInput}
              />

              <button
                className="content-media-picker__upload"
                type="button"
                disabled={isUploading}
                onClick={() => uploadInputRef.current?.click()}
              >
                {isUploading ? (
                  <>
                    <LoaderCircle className="about-spin" size={17} />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload size={17} />
                    Upload new
                  </>
                )}
              </button>
            </div>

            <div className="content-media-picker__content">
              {isLoading ? (
                <div className="content-media-picker__state">
                  <LoaderCircle className="about-spin" size={30} />
                  <strong>
                    Loading {isImageMode ? "images" : "documents"}
                  </strong>
                  <span>Fetching your Media Library…</span>
                </div>
              ) : assets.length === 0 ? (
                <div className="content-media-picker__state">
                  {isImageMode ? (
                    <ImageIcon size={34} />
                  ) : (
                    <FileText size={34} />
                  )}

                  <strong>No {isImageMode ? "images" : "PDFs"} found</strong>

                  <span>
                    {debouncedSearch
                      ? "Try a different search."
                      : isSkill
                        ? "Upload a technology logo to get started."
                        : isProfile
                          ? "Upload a profile image to get started."
                          : "Upload your résumé PDF to get started."}
                  </span>
                </div>
              ) : (
                <div
                  className={
                    isImageMode
                      ? "content-media-picker__grid"
                      : "content-media-picker__documents"
                  }
                >
                  {assets.map((asset) => {
                    const preview = getMediaPreviewUrl(asset);
                    const selected = pendingId === asset.id;

                    return (
                      <button
                        key={asset.id}
                        type="button"
                        className={`content-media-picker__asset${
                          selected
                            ? " content-media-picker__asset--selected"
                            : ""
                        }${
                          !isImageMode
                            ? " content-media-picker__asset--document"
                            : ""
                        }`}
                        onClick={() => setPendingId(asset.id)}
                      >
                        {isImageMode ? (
                          <div className="content-media-picker__asset-preview">
                            {preview ? (
                              <img
                                src={preview}
                                alt={asset.alt_text || asset.original_filename}
                              />
                            ) : (
                              <ImageIcon size={30} />
                            )}

                            <span className="content-media-picker__check">
                              {selected ? <Check size={15} /> : null}
                            </span>
                          </div>
                        ) : (
                          <div className="content-media-picker__document-icon">
                            <FileText size={26} />

                            <span className="content-media-picker__check">
                              {selected ? <Check size={15} /> : null}
                            </span>
                          </div>
                        )}

                        <div className="content-media-picker__asset-copy">
                          <strong>{asset.original_filename}</strong>

                          <span>
                            {isProfile && asset.width && asset.height
                              ? `${asset.width} × ${asset.height}`
                              : isProfile
                                ? formatFileSize(asset.file_size)
                                : `PDF · ${formatFileSize(asset.file_size)}`}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <footer className="content-media-picker__footer">
              <button
                className="about-secondary-button"
                type="button"
                onClick={onClose}
              >
                Cancel
              </button>

              <button
                className="admin-primary-action"
                type="button"
                disabled={pendingId === null}
                onClick={confirmSelection}
              >
                <Check size={18} />
                Use selected
              </button>
            </footer>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
