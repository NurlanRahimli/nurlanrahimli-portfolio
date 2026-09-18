import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  Check,
  Image as ImageIcon,
  LoaderCircle,
  Plus,
  Search,
  Upload,
  X,
} from "lucide-react";
import {
  type ChangeEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useToast } from "../../context/toastContext";
import { listMedia, uploadMedia } from "../../services/mediaApi";
import type { MediaAsset } from "../../types/media";
import { getMediaPreviewUrl } from "../media/mediaUtils";

interface ProjectMediaPickerProps {
  isOpen: boolean;
  selectedIds: number[];
  onClose: () => void;
  onConfirm: (assets: MediaAsset[]) => void;
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

export function ProjectMediaPicker({
  isOpen,
  selectedIds,
  onClose,
  onConfirm,
}: ProjectMediaPickerProps) {
  const { showToast } = useToast();

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);

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
        fileType: "image",
        limit: 100,
        offset: 0,
      });

      setAssets(result.items);
    } catch (error) {
      showToast({
        title: "Could not load media",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, showToast]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    let cancelled = false;

    queueMicrotask(() => {
      if (!cancelled) {
        setSelected(selectedIds);
        void loadAssets();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [isOpen, loadAssets, selectedIds]);

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

  const selectedAssets = useMemo(
    () =>
      selected
        .map((id) => assets.find((asset) => asset.id === id))
        .filter((asset): asset is MediaAsset => Boolean(asset)),
    [assets, selected],
  );

  const newAssets = useMemo(
    () => selectedAssets.filter((asset) => !selectedIds.includes(asset.id)),
    [selectedAssets, selectedIds],
  );

  const handleUpload = async (files: File[]) => {
    if (!files.length || isUploading) {
      return;
    }

    const imageFiles = files.filter((file) => file.type.startsWith("image/"));

    if (imageFiles.length !== files.length) {
      showToast({
        title: "Images only",
        message: "Project galleries only support image files.",
        type: "error",
      });
    }

    if (imageFiles.length === 0) {
      return;
    }

    setIsUploading(true);

    const uploadedAssets: MediaAsset[] = [];

    try {
      for (const file of imageFiles) {
        const uploaded = await uploadMedia(file);
        uploadedAssets.push(uploaded);
      }

      setSearch("");
      setDebouncedSearch("");

      const result = await listMedia({
        fileType: "image",
        limit: 100,
        offset: 0,
      });

      setAssets(result.items);

      setSelected((current) => {
        const next = [...current];

        for (const asset of uploadedAssets) {
          if (!next.includes(asset.id)) {
            next.push(asset.id);
          }
        }

        return next;
      });

      showToast({
        title:
          uploadedAssets.length === 1 ? "Image uploaded" : "Images uploaded",
        message:
          uploadedAssets.length === 1
            ? `${uploadedAssets[0].original_filename} was uploaded and selected.`
            : `${uploadedAssets.length} images were uploaded and selected.`,
        type: "success",
      });
    } catch (error) {
      if (uploadedAssets.length > 0) {
        setSearch("");
        setDebouncedSearch("");

        const result = await listMedia({
          fileType: "image",
          limit: 100,
          offset: 0,
        });

        setAssets(result.items);

        setSelected((current) => {
          const next = [...current];

          for (const asset of uploadedAssets) {
            if (!next.includes(asset.id)) {
              next.push(asset.id);
            }
          }

          return next;
        });
      }

      showToast({
        title: "Upload failed",
        message:
          uploadedAssets.length > 0
            ? `${uploadedAssets.length} image${
                uploadedAssets.length === 1 ? "" : "s"
              } uploaded before the error. ${getErrorMessage(error)}`
            : getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadInput = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    void handleUpload(files);
  };

  const toggleAsset = (assetId: number) => {
    if (selectedIds.includes(assetId)) {
      return;
    }

    setSelected((current) =>
      current.includes(assetId)
        ? current.filter((id) => id !== assetId)
        : [...current, assetId],
    );
  };

  const confirm = () => {
    if (newAssets.length === 0) {
      return;
    }

    onConfirm(newAssets);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen ? (
        <motion.div
          className="project-media-picker"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            className="project-media-picker__backdrop"
            type="button"
            aria-label="Close media picker"
            onClick={onClose}
          />

          <motion.div
            className="project-media-picker__dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="project-media-picker-title"
            initial={{ opacity: 0, y: 18, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.985 }}
            transition={{ duration: 0.2 }}
          >
            <header className="project-media-picker__header">
              <div>
                <span className="admin-eyebrow">Media Library</span>
                <h2 id="project-media-picker-title">Add project images</h2>
                <p>
                  Select existing images for this project. Media Library assets
                  remain independent and are never deleted from here.
                </p>
              </div>

              <button
                className="project-media-picker__close"
                type="button"
                aria-label="Close"
                onClick={onClose}
              >
                <X size={20} />
              </button>
            </header>

            <div className="project-media-picker__toolbar">
              <label className="project-media-picker__search">
                <Search size={18} />
                <input
                  value={search}
                  placeholder="Search images..."
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>

              <div className="project-media-picker__toolbar-actions">
                <span>
                  {newAssets.length} new image
                  {newAssets.length === 1 ? "" : "s"} selected
                </span>

                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/avif"
                  multiple
                  hidden
                  onChange={handleUploadInput}
                />

                <button
                  className="project-media-picker__upload"
                  type="button"
                  disabled={isUploading}
                  onClick={() => uploadInputRef.current?.click()}
                >
                  {isUploading ? (
                    <>
                      <LoaderCircle className="projects-spin" size={17} />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload size={17} />
                      Upload New
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="project-media-picker__content">
              {isLoading ? (
                <div className="project-media-picker__state">
                  <LoaderCircle className="projects-spin" size={30} />
                  <strong>Loading images</strong>
                  <span>Fetching your Media Library…</span>
                </div>
              ) : assets.length === 0 ? (
                <div className="project-media-picker__state">
                  <ImageIcon size={32} />
                  <strong>No images found</strong>
                  <span>
                    {debouncedSearch
                      ? "Try a different search."
                      : "Upload images in Media Library first."}
                  </span>
                </div>
              ) : (
                <div className="project-media-picker__grid">
                  {assets.map((asset) => {
                    const preview = getMediaPreviewUrl(asset);
                    const alreadyAdded = selectedIds.includes(asset.id);
                    const isSelected = selected.includes(asset.id);

                    return (
                      <button
                        key={asset.id}
                        className={`project-media-picker__asset${
                          isSelected
                            ? " project-media-picker__asset--selected"
                            : ""
                        }`}
                        type="button"
                        disabled={alreadyAdded}
                        onClick={() => toggleAsset(asset.id)}
                      >
                        <div className="project-media-picker__asset-preview">
                          {preview ? (
                            <img
                              src={preview}
                              alt={asset.alt_text || asset.original_filename}
                            />
                          ) : (
                            <ImageIcon size={28} />
                          )}

                          <span className="project-media-picker__check">
                            {isSelected ? <Check size={15} /> : null}
                          </span>
                        </div>

                        <div className="project-media-picker__asset-copy">
                          <strong>{asset.original_filename}</strong>
                          <span>
                            {alreadyAdded
                              ? "Already in project"
                              : asset.width && asset.height
                                ? `${asset.width} × ${asset.height}`
                                : "Image"}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <footer className="project-media-picker__footer">
              <button
                className="project-editor-button project-editor-button--secondary"
                type="button"
                onClick={onClose}
              >
                Cancel
              </button>

              <button
                className="admin-primary-action"
                type="button"
                disabled={newAssets.length === 0}
                onClick={confirm}
              >
                <Plus size={18} />
                Add selected
              </button>
            </footer>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
