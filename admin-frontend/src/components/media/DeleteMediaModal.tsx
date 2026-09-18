import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, LoaderCircle, Trash2, X } from "lucide-react";
import type { MediaAsset } from "../../types/media";

interface DeleteMediaModalProps {
  asset: MediaAsset | null;
  isDeleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DeleteMediaModal({
  asset,
  isDeleting,
  onCancel,
  onConfirm,
}: DeleteMediaModalProps) {
  return (
    <AnimatePresence>
      {asset && (
        <motion.div
          className="admin-modal-layer admin-modal-layer--confirm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            className="admin-modal-backdrop"
            type="button"
            aria-label="Close delete confirmation"
            onClick={isDeleting ? undefined : onCancel}
          />

          <motion.div
            className="delete-media-modal"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-media-title"
            initial={{
              opacity: 0,
              scale: 0.96,
              y: 14,
            }}
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
              scale: 0.97,
              y: 10,
            }}
            transition={{
              duration: 0.22,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            <button
              className="admin-modal-close"
              type="button"
              disabled={isDeleting}
              aria-label="Close"
              onClick={onCancel}
            >
              <X size={20} />
            </button>

            <div className="delete-media-modal__icon">
              <AlertTriangle size={27} />
            </div>

            <span className="admin-eyebrow">Permanent action</span>

            <h2 id="delete-media-title">Delete this asset?</h2>

            <p>
              <strong>{asset.original_filename}</strong> and all generated
              variants will be permanently removed from storage.
            </p>

            <div className="delete-media-modal__actions">
              <button
                className="admin-secondary-button"
                type="button"
                disabled={isDeleting}
                onClick={onCancel}
              >
                Cancel
              </button>

              <button
                className="admin-danger-button"
                type="button"
                disabled={isDeleting}
                onClick={onConfirm}
              >
                {isDeleting ? (
                  <>
                    <LoaderCircle
                      className="media-dropzone__spinner"
                      size={18}
                    />
                    Deleting
                  </>
                ) : (
                  <>
                    <Trash2 size={18} />
                    Delete asset
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
