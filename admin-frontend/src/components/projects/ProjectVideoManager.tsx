import MuxPlayer from "@mux/mux-player-react";
import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Film,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import {
  type ChangeEvent,
  type DragEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useToast } from "../../context/toastContext";
import {
  cancelProjectVideoReplacement,
  createProjectVideoUpload,
  deleteProjectVideo,
  getProject,
  retryProjectVideoCleanup,
  uploadProjectVideoToMux,
} from "../../services/projectsApi";
import type { Project } from "../../types/project";

interface ProjectVideoManagerProps {
  project: Project;
  onProjectChange: (project: Project) => void;
}

type ConfirmAction = "delete" | "cancel-replacement" | null;

const ACCEPTED_VIDEO_TYPES = [
  "video/mp4",
  "video/quicktime",
  "video/webm",
  "video/x-m4v",
];

const PROCESSING_STATUSES = new Set([
  "uploading",
  "waiting",
  "processing",
  "preparing",
]);

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = (
      error.response?.data as
        | {
            detail?: string | Array<{ msg?: string }>;
          }
        | undefined
    )?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
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

function formatDuration(seconds: number | null): string {
  if (seconds === null || !Number.isFinite(seconds)) {
    return "—";
  }

  const total = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(total / 60);
  const remainingSeconds = total % 60;

  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

function formatStatus(status: string | null): string {
  if (!status) {
    return "Unknown";
  }

  return status
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isProcessing(status: string | null): boolean {
  return Boolean(status && PROCESSING_STATUSES.has(status.toLowerCase()));
}

function validateVideoFile(file: File): string | null {
  const extension = file.name.split(".").pop()?.toLowerCase();
  const supportedExtension = ["mp4", "mov", "m4v", "webm"].includes(
    extension ?? "",
  );

  if (
    file.type &&
    !ACCEPTED_VIDEO_TYPES.includes(file.type) &&
    !supportedExtension
  ) {
    return "Choose an MP4, MOV, M4V or WebM video.";
  }

  if (!file.type && !supportedExtension) {
    return "Choose an MP4, MOV, M4V or WebM video.";
  }

  if (file.size <= 0) {
    return "The selected video is empty.";
  }

  return null;
}

export function ProjectVideoManager({
  project,
  onProjectChange,
}: ProjectVideoManagerProps) {
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRetryingCleanup, setIsRetryingCleanup] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  const video = project.video;
  const hasActiveVideo = Boolean(video);
  const hasPendingReplacement = Boolean(video?.pending_mux_upload_id);
  const activeReady =
    video?.status === "ready" && Boolean(video.mux_playback_id);
  const activeProcessing = Boolean(video && isProcessing(video.status));
  const pendingProcessing = Boolean(
    hasPendingReplacement && isProcessing(video?.pending_status ?? null),
  );
  const pendingFailed =
    hasPendingReplacement &&
    Boolean(
      video?.pending_status === "errored" ||
      video?.pending_status === "error" ||
      video?.pending_error_message,
    );

  const refreshProject = useCallback(async () => {
    try {
      const refreshed = await getProject(project.id);
      onProjectChange(refreshed);
    } catch {
      // Polling is best-effort. Explicit actions surface their own errors.
    }
  }, [onProjectChange, project.id]);

  useEffect(() => {
    const shouldPoll = isUploading || activeProcessing || pendingProcessing;

    if (!shouldPoll) {
      return;
    }

    const interval = window.setInterval(() => {
      void refreshProject();
    }, 3500);

    return () => {
      window.clearInterval(interval);
    };
  }, [activeProcessing, isUploading, pendingProcessing, refreshProject]);

  const beginUpload = async (file: File) => {
    const validationError = validateVideoFile(file);

    if (validationError) {
      showToast({
        title: "Video not accepted",
        message: validationError,
        type: "error",
      });
      return;
    }

    if (video?.cleanup_pending) {
      showToast({
        title: "Cleanup required first",
        message:
          "Retry the previous video cleanup before starting another replacement.",
        type: "error",
      });
      return;
    }

    if (hasPendingReplacement) {
      showToast({
        title: "Replacement already in progress",
        message:
          "Cancel or finish the current replacement before uploading another video.",
        type: "error",
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const upload = await createProjectVideoUpload(project.id, file.name);

      await uploadProjectVideoToMux(upload.upload_url, file, (progress) => {
        setUploadProgress(progress);
      });

      await refreshProject();

      showToast({
        title: hasActiveVideo ? "Replacement uploaded" : "Video uploaded",
        message: hasActiveVideo
          ? "Mux is processing the replacement. Your current video stays live until the new one is ready."
          : "Upload complete. Mux is now processing your video.",
        type: "success",
      });
    } catch (error) {
      await refreshProject();

      showToast({
        title: "Video upload failed",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      void beginUpload(file);
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      void beginUpload(file);
    }
  };

  const retryCleanup = async () => {
    setIsRetryingCleanup(true);

    try {
      await retryProjectVideoCleanup(project.id);
      await refreshProject();

      showToast({
        title: "Cleanup complete",
        message: "The previous Mux video resources were removed successfully.",
        type: "success",
      });
    } catch (error) {
      await refreshProject();

      showToast({
        title: "Cleanup still needs attention",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsRetryingCleanup(false);
    }
  };

  const confirmDestructiveAction = async () => {
    if (!confirmAction) {
      return;
    }

    setIsConfirming(true);

    try {
      if (confirmAction === "delete") {
        await deleteProjectVideo(project.id);

        showToast({
          title: "Video removed",
          message: "The project video and its Mux resources were removed.",
          type: "success",
        });
      } else {
        await cancelProjectVideoReplacement(project.id);

        showToast({
          title: "Replacement cancelled",
          message:
            "The pending replacement was removed. Your current video was left untouched.",
          type: "success",
        });
      }

      setConfirmAction(null);
      await refreshProject();
    } catch (error) {
      showToast({
        title:
          confirmAction === "delete"
            ? "Could not remove video"
            : "Could not cancel replacement",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsConfirming(false);
    }
  };

  const openFilePicker = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        className="project-video-file-input"
        type="file"
        accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.m4v,.webm"
        onChange={handleFileChange}
      />

      {!video ? (
        <div
          className={`project-video-dropzone${
            isDragging ? " project-video-dropzone--dragging" : ""
          }`}
          onDragEnter={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();

            if (event.currentTarget === event.target) {
              setIsDragging(false);
            }
          }}
          onDrop={handleDrop}
        >
          <div className="project-video-dropzone__icon">
            {isUploading ? (
              <LoaderCircle className="projects-spin" size={30} />
            ) : (
              <Upload size={30} />
            )}
          </div>

          <div className="project-video-dropzone__copy">
            <span className="project-video-kicker">Mux direct upload</span>
            <h3>{isUploading ? "Uploading video…" : "Add a project video"}</h3>
            <p>
              Upload directly to Mux without routing the video through the API
              server. MP4, MOV, M4V and WebM are supported.
            </p>
          </div>

          {isUploading && uploadProgress !== null ? (
            <div className="project-video-progress">
              <div className="project-video-progress__meta">
                <span>Uploading to Mux</span>
                <strong>{uploadProgress}%</strong>
              </div>
              <div className="project-video-progress__track">
                <motion.span
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
            <button
              className="project-video-primary"
              type="button"
              onClick={openFilePicker}
            >
              <Upload size={18} />
              Choose video
            </button>
          )}

          {!isUploading ? <small>or drag and drop a video here</small> : null}
        </div>
      ) : (
        <div className="project-video-manager">
          {video.cleanup_pending ? (
            <motion.div
              className="project-video-alert project-video-alert--warning"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="project-video-alert__icon">
                <AlertTriangle size={21} />
              </div>

              <div className="project-video-alert__copy">
                <strong>Previous video cleanup needs attention</strong>
                <p>
                  Your current video is safe and remains active. The old Mux
                  resource still needs to be removed.
                </p>
                {video.cleanup_error_message ? (
                  <code>{video.cleanup_error_message}</code>
                ) : null}
              </div>

              <button
                type="button"
                disabled={isRetryingCleanup}
                onClick={() => void retryCleanup()}
              >
                {isRetryingCleanup ? (
                  <LoaderCircle className="projects-spin" size={17} />
                ) : (
                  <RefreshCw size={17} />
                )}
                Retry cleanup
              </button>
            </motion.div>
          ) : null}

          <div className="project-video-active">
            <div className="project-video-preview">
              {activeReady && video.mux_playback_id ? (
                <MuxPlayer
                  key={video.mux_playback_id}
                  playbackId={video.mux_playback_id}
                  streamType="on-demand"
                  preload="metadata"
                  playsInline
                  metadata={{
                    video_id: String(project.id),
                    video_title:
                      video.original_filename ||
                      project.title ||
                      "Project video",
                    player_name: "Portfolio Admin Project Editor",
                  }}
                  className="project-video-mux-player"
                />
              ) : (
                <div className="project-video-preview__processing">
                  {activeProcessing ? (
                    <LoaderCircle className="projects-spin" size={34} />
                  ) : (
                    <Film size={34} />
                  )}
                  <strong>
                    {activeProcessing
                      ? "Mux is processing your video"
                      : "Video preview unavailable"}
                  </strong>
                  <span>{formatStatus(video.status)}</span>
                </div>
              )}

              <span
                className={`project-video-status project-video-status--${video.status.toLowerCase()}`}
              >
                {activeReady ? <CheckCircle2 size={14} /> : null}
                {activeProcessing ? (
                  <LoaderCircle className="projects-spin" size={14} />
                ) : null}
                {formatStatus(video.status)}
              </span>
            </div>

            <div className="project-video-details">
              <div className="project-video-details__heading">
                <div>
                  <span className="project-video-kicker">Active video</span>
                  <h3>{video.original_filename || "Project video"}</h3>
                </div>

                {activeReady ? (
                  <span className="project-video-ready-badge">
                    <CheckCircle2 size={15} />
                    Live
                  </span>
                ) : null}
              </div>

              <div className="project-video-meta">
                <div>
                  <span>Duration</span>
                  <strong>{formatDuration(video.duration_seconds)}</strong>
                </div>
                <div>
                  <span>Aspect ratio</span>
                  <strong>{video.aspect_ratio || "—"}</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong>{formatStatus(video.status)}</strong>
                </div>
              </div>

              {video.error_message ? (
                <div className="project-video-error">
                  <AlertTriangle size={18} />
                  <span>{video.error_message}</span>
                </div>
              ) : null}

              {isUploading && uploadProgress !== null ? (
                <div className="project-video-progress">
                  <div className="project-video-progress__meta">
                    <span>Uploading replacement</span>
                    <strong>{uploadProgress}%</strong>
                  </div>
                  <div className="project-video-progress__track">
                    <motion.span
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              ) : null}

              <div className="project-video-actions">
                <button
                  className="project-video-primary"
                  type="button"
                  disabled={
                    isUploading ||
                    !activeReady ||
                    hasPendingReplacement ||
                    video.cleanup_pending
                  }
                  onClick={openFilePicker}
                >
                  {isUploading ? (
                    <LoaderCircle className="projects-spin" size={18} />
                  ) : (
                    <RotateCcw size={18} />
                  )}
                  Replace video
                </button>

                <button
                  className="project-video-danger"
                  type="button"
                  disabled={isUploading}
                  onClick={() => setConfirmAction("delete")}
                >
                  <Trash2 size={18} />
                  Remove video
                </button>
              </div>

              {activeReady ? (
                <p className="project-video-safety-note">
                  Replacements are processed separately. This video stays live
                  until Mux confirms the new video is ready.
                </p>
              ) : null}
            </div>
          </div>

          <AnimatePresence>
            {hasPendingReplacement ? (
              <motion.div
                className={`project-video-replacement${
                  pendingFailed ? " project-video-replacement--error" : ""
                }`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <div className="project-video-replacement__icon">
                  {pendingFailed ? (
                    <AlertTriangle size={22} />
                  ) : (
                    <LoaderCircle className="projects-spin" size={22} />
                  )}
                </div>

                <div className="project-video-replacement__copy">
                  <span className="project-video-kicker">
                    Pending replacement
                  </span>
                  <strong>
                    {video.pending_original_filename || "Replacement video"}
                  </strong>
                  <p>
                    {pendingFailed
                      ? "Mux could not finish this replacement. The active video above has not been changed."
                      : "Mux is preparing the replacement. The active video above remains live until processing succeeds."}
                  </p>

                  <div className="project-video-replacement__meta">
                    <span>
                      Status:{" "}
                      <strong>{formatStatus(video.pending_status)}</strong>
                    </span>
                    {video.pending_duration_seconds !== null ? (
                      <span>
                        Duration:{" "}
                        <strong>
                          {formatDuration(video.pending_duration_seconds)}
                        </strong>
                      </span>
                    ) : null}
                    {video.pending_aspect_ratio ? (
                      <span>
                        Ratio: <strong>{video.pending_aspect_ratio}</strong>
                      </span>
                    ) : null}
                  </div>

                  {video.pending_error_message ? (
                    <code>{video.pending_error_message}</code>
                  ) : null}
                </div>

                <button
                  type="button"
                  disabled={isConfirming || isUploading}
                  onClick={() => setConfirmAction("cancel-replacement")}
                >
                  <X size={17} />
                  Cancel replacement
                </button>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      )}

      <AnimatePresence>
        {confirmAction ? (
          <motion.div
            className="project-video-modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={(event) => {
              if (event.currentTarget === event.target && !isConfirming) {
                setConfirmAction(null);
              }
            }}
          >
            <motion.div
              className="project-video-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="project-video-modal-title"
              initial={{ opacity: 0, y: 16, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ duration: 0.18 }}
            >
              <div className="project-video-modal__icon">
                <AlertTriangle size={24} />
              </div>

              <div className="project-video-modal__copy">
                <span className="project-video-kicker">
                  {confirmAction === "delete"
                    ? "Remove project video"
                    : "Cancel replacement"}
                </span>
                <h3 id="project-video-modal-title">
                  {confirmAction === "delete"
                    ? "Remove this video?"
                    : "Cancel this replacement?"}
                </h3>
                <p>
                  {confirmAction === "delete"
                    ? "This removes the active video, any pending replacement and associated Mux resources. The project itself will remain."
                    : "The pending replacement and its Mux resources will be removed. Your current active video will remain untouched."}
                </p>
              </div>

              <div className="project-video-modal__actions">
                <button
                  type="button"
                  disabled={isConfirming}
                  onClick={() => setConfirmAction(null)}
                >
                  Keep it
                </button>

                <button
                  className="project-video-modal__danger"
                  type="button"
                  disabled={isConfirming}
                  onClick={() => void confirmDestructiveAction()}
                >
                  {isConfirming ? (
                    <LoaderCircle className="projects-spin" size={17} />
                  ) : (
                    <Trash2 size={17} />
                  )}
                  {confirmAction === "delete"
                    ? "Remove video"
                    : "Cancel replacement"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
