import { type FormEvent, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Check,
  Clipboard,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  LoaderCircle,
  Save,
  Trash2,
  X,
} from "lucide-react";
import type { MediaAsset } from "../../types/media";
import {
  formatFileSize,
  formatMediaDate,
  getMediaDimensions,
  getMediaPreviewUrl,
} from "./mediaUtils";

interface MediaDetailsModalProps {
  asset: MediaAsset | null;
  isSaving: boolean;
  onClose: () => void;
  onSave: (asset: MediaAsset, altText: string) => void;
  onDelete: (asset: MediaAsset) => void;
  onCopyUrl: (url: string) => void;
}

export function MediaDetailsModal({
  asset,
  isSaving,
  onClose,
  onSave,
  onDelete,
  onCopyUrl,
}: MediaDetailsModalProps) {
  const [altText, setAltText] = useState(asset?.alt_text ?? "");
  const [copiedVariantId, setCopiedVariantId] = useState<number | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!asset) {
      return;
    }

    onSave(asset, altText);
  }

  function copyVariant(variantId: number, url: string) {
    onCopyUrl(url);
    setCopiedVariantId(variantId);

    window.setTimeout(() => {
      setCopiedVariantId((current) => (current === variantId ? null : current));
    }, 1800);
  }

  const previewUrl = asset ? getMediaPreviewUrl(asset) : null;

  const dimensions = asset ? getMediaDimensions(asset) : null;

  const hasAltChanges =
    asset !== null && altText.trim() !== (asset.alt_text ?? "").trim();

  return (
    <AnimatePresence>
      {asset && (
        <motion.div
          className="admin-modal-layer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            className="admin-modal-backdrop"
            type="button"
            aria-label="Close media details"
            onClick={isSaving ? undefined : onClose}
          />

          <motion.section
            className="media-details-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="media-details-title"
            initial={{
              opacity: 0,
              scale: 0.98,
              y: 18,
            }}
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              scale: 0.98,
              y: 12,
            }}
            transition={{
              duration: 0.24,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            <button
              className="admin-modal-close"
              type="button"
              disabled={isSaving}
              aria-label="Close media details"
              onClick={onClose}
            >
              <X size={21} />
            </button>

            <div className="media-details-modal__preview">
              {asset.file_type === "image" && previewUrl ? (
                <img
                  src={previewUrl}
                  alt={asset.alt_text || asset.original_filename}
                />
              ) : asset.url ? (
                <iframe src={asset.url} title={asset.original_filename} />
              ) : (
                <div className="media-details-modal__document">
                  <FileText size={48} />
                  <strong>PDF document</strong>
                </div>
              )}
            </div>

            <div className="media-details-modal__content">
              <div className="media-details-modal__header">
                <div>
                  <span className="admin-eyebrow">
                    {asset.file_type === "image"
                      ? "Image asset"
                      : "Document asset"}
                  </span>

                  <h2 id="media-details-title">{asset.original_filename}</h2>
                </div>

                <div className="media-details-modal__type-icon">
                  {asset.file_type === "image" ? (
                    <ImageIcon size={22} />
                  ) : (
                    <FileText size={22} />
                  )}
                </div>
              </div>

              <div className="media-detail-metadata">
                <div>
                  <span>File size</span>
                  <strong>{formatFileSize(asset.file_size)}</strong>
                </div>

                <div>
                  <span>Dimensions</span>
                  <strong>{dimensions ?? "Not applicable"}</strong>
                </div>

                <div>
                  <span>Format</span>
                  <strong>{asset.mime_type}</strong>
                </div>

                <div>
                  <span>Uploaded</span>
                  <strong>{formatMediaDate(asset.created_at)}</strong>
                </div>
              </div>

              {asset.url && (
                <div className="media-public-url">
                  <div>
                    <span>Original public URL</span>
                    <strong title={asset.url}>{asset.url}</strong>
                  </div>

                  <div>
                    <button
                      type="button"
                      title="Copy URL"
                      aria-label="Copy original URL"
                      onClick={() => onCopyUrl(asset.url!)}
                    >
                      <Clipboard size={17} />
                    </button>

                    <a
                      href={asset.url}
                      target="_blank"
                      rel="noreferrer"
                      title="Open original"
                      aria-label="Open original"
                    >
                      <ExternalLink size={17} />
                    </a>
                  </div>
                </div>
              )}

              {asset.file_type === "image" && asset.variants.length > 0 && (
                <div className="media-variants">
                  <div className="media-variants__heading">
                    <div>
                      <strong>Optimized variants</strong>
                      <span>
                        Generated automatically for responsive delivery.
                      </span>
                    </div>

                    <span>{asset.variants.length} variants</span>
                  </div>

                  <div className="media-variants__list">
                    {asset.variants.map((variant) => (
                      <div className="media-variant-row" key={variant.id}>
                        <div>
                          <strong>{variant.variant_name}</strong>
                          <span>
                            {variant.width} × {variant.height}
                            {" · "}
                            {formatFileSize(variant.file_size)}
                          </span>
                        </div>

                        {variant.url && (
                          <div>
                            <button
                              type="button"
                              title="Copy variant URL"
                              aria-label={`Copy ${variant.variant_name} URL`}
                              onClick={() =>
                                copyVariant(variant.id, variant.url!)
                              }
                            >
                              {copiedVariantId === variant.id ? (
                                <Check size={16} />
                              ) : (
                                <Clipboard size={16} />
                              )}
                            </button>

                            <a
                              href={variant.url}
                              target="_blank"
                              rel="noreferrer"
                              title="Open variant"
                              aria-label={`Open ${variant.variant_name} variant`}
                            >
                              <ExternalLink size={16} />
                            </a>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <form className="media-alt-form" onSubmit={handleSubmit}>
                <label htmlFor="media-alt-text">
                  Alt text
                  <span>Used for accessibility and image descriptions.</span>
                </label>

                <textarea
                  id="media-alt-text"
                  value={altText}
                  maxLength={500}
                  rows={3}
                  placeholder="Describe this image..."
                  disabled={isSaving}
                  onChange={(event) => setAltText(event.target.value)}
                />

                <div className="media-alt-form__footer">
                  <span>{altText.length} / 500</span>

                  <button
                    className="admin-primary-action"
                    type="submit"
                    disabled={isSaving || !hasAltChanges}
                  >
                    {isSaving ? (
                      <>
                        <LoaderCircle
                          className="media-dropzone__spinner"
                          size={18}
                        />
                        Saving
                      </>
                    ) : (
                      <>
                        <Save size={18} />
                        Save changes
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="media-danger-zone">
                <div>
                  <strong>Delete asset</strong>
                  <span>
                    Permanently remove this file and its generated variants.
                  </span>
                </div>

                <button
                  className="admin-danger-button admin-danger-button--outline"
                  type="button"
                  disabled={isSaving}
                  onClick={() => onDelete(asset)}
                >
                  <Trash2 size={17} />
                  Delete
                </button>
              </div>
            </div>
          </motion.section>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
