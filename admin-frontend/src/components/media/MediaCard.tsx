import { motion } from "framer-motion";
import { FileText, Image as ImageIcon, Maximize2 } from "lucide-react";
import type { MediaAsset } from "../../types/media";
import {
  formatFileSize,
  formatMediaDate,
  getMediaDimensions,
  getMediaPreviewUrl,
} from "./mediaUtils";

interface MediaCardProps {
  asset: MediaAsset;
  index: number;
  onSelect: (asset: MediaAsset) => void;
}

export function MediaCard({ asset, index, onSelect }: MediaCardProps) {
  const previewUrl = getMediaPreviewUrl(asset);
  const dimensions = getMediaDimensions(asset);

  return (
    <motion.button
      className="media-card"
      type="button"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.32,
        delay: Math.min(index * 0.025, 0.2),
      }}
      onClick={() => onSelect(asset)}
    >
      <div className="media-card__preview">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt={asset.alt_text || asset.original_filename}
            loading="lazy"
          />
        ) : (
          <div className="media-card__document">
            <FileText size={38} />
            <span>PDF</span>
          </div>
        )}

        <div className="media-card__type">
          {asset.file_type === "image" ? (
            <ImageIcon size={14} />
          ) : (
            <FileText size={14} />
          )}

          {asset.file_type}
        </div>

        <div className="media-card__open">
          <Maximize2 size={16} />
        </div>
      </div>

      <div className="media-card__body">
        <strong title={asset.original_filename}>
          {asset.original_filename}
        </strong>

        <div className="media-card__metadata">
          <span>{formatFileSize(asset.file_size)}</span>

          {dimensions && (
            <>
              <i />
              <span>{dimensions}</span>
            </>
          )}

          <i />
          <span>{formatMediaDate(asset.created_at)}</span>
        </div>

        {asset.alt_text ? (
          <p title={asset.alt_text}>{asset.alt_text}</p>
        ) : (
          <p className="media-card__missing-alt">No alt text</p>
        )}
      </div>
    </motion.button>
  );
}
