import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  Check,
  ExternalLink,
  Image as ImageIcon,
  LoaderCircle,
  MessageSquareQuote,
  Pencil,
  Plus,
  Search,
  Trash2,
  Upload,
  UserRound,
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
import { useToast } from "../context/toastContext";
import { listMedia, uploadMedia } from "../services/mediaApi";
import {
  createTestimonial,
  deleteTestimonial,
  listTestimonials,
  reorderTestimonials,
  updateTestimonial,
} from "../services/testimonialsApi";
import type { MediaAsset } from "../types/media";
import type {
  Testimonial,
  TestimonialStatusFilter,
  TestimonialWritePayload,
} from "../types/testimonial";
import { getMediaPreviewUrl } from "../components/media/mediaUtils";

interface TestimonialForm {
  person_name: string;
  testimonial_text: string;
  profile_media_asset_id: number | null;
  profile_image_url: string | null;
  linkedin_url: string;
  is_active: boolean;
}

const emptyForm: TestimonialForm = {
  person_name: "",
  testimonial_text: "",
  profile_media_asset_id: null,
  profile_image_url: null,
  linkedin_url: "",
  is_active: true,
};

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

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean).slice(0, 2);

  return parts.map((part) => part[0]?.toUpperCase()).join("") || "NR";
}

export default function TestimonialsPage() {
  const { showToast } = useToast();

  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<TestimonialStatusFilter>("all");

  const [isLoading, setIsLoading] = useState(true);
  const [isReordering, setIsReordering] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);

  const [editorTarget, setEditorTarget] = useState<Testimonial | "new" | null>(
    null,
  );
  const [form, setForm] = useState<TestimonialForm>(emptyForm);
  const [isSaving, setIsSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<Testimonial | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [isMediaOpen, setIsMediaOpen] = useState(false);
  const [mediaAssets, setMediaAssets] = useState<MediaAsset[]>([]);
  const [mediaSearch, setMediaSearch] = useState("");
  const [debouncedMediaSearch, setDebouncedMediaSearch] = useState("");
  const [isMediaLoading, setIsMediaLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 260);

    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedMediaSearch(mediaSearch.trim());
    }, 250);

    return () => window.clearTimeout(timer);
  }, [mediaSearch]);

  const loadTestimonials = useCallback(async () => {
    setIsLoading(true);

    try {
      const result = await listTestimonials({
        search: debouncedSearch || undefined,
        isActive:
          statusFilter === "all" ? undefined : statusFilter === "active",
      });

      setTestimonials(result.items);
      setTotal(result.total);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load testimonials",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, showToast, statusFilter]);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      if (!cancelled) {
        void loadTestimonials();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [loadTestimonials]);

  const loadMedia = useCallback(async () => {
    setIsMediaLoading(true);

    try {
      const result = await listMedia({
        search: debouncedMediaSearch || undefined,
        fileType: "image",
        limit: 100,
        offset: 0,
      });

      setMediaAssets(result.items);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load media",
        message: getErrorMessage(error),
      });
    } finally {
      setIsMediaLoading(false);
    }
  }, [debouncedMediaSearch, showToast]);

  useEffect(() => {
    if (!isMediaOpen) {
      return;
    }

    void loadMedia();
  }, [isMediaOpen, loadMedia]);

  useEffect(() => {
    if (!editorTarget && !isMediaOpen && !deleteTarget) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }

      if (isMediaOpen) {
        setIsMediaOpen(false);
      } else if (deleteTarget) {
        setDeleteTarget(null);
      } else {
        setEditorTarget(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [deleteTarget, editorTarget, isMediaOpen]);

  const counts = useMemo(() => {
    const active = testimonials.filter(
      (testimonial) => testimonial.is_active,
    ).length;

    return {
      active,
      inactive: testimonials.length - active,
      visible: testimonials.length,
    };
  }, [testimonials]);

  const hasActiveFilters = search.trim().length > 0 || statusFilter !== "all";

  const canReorder = !hasActiveFilters && !isLoading;

  function openCreate() {
    setForm(emptyForm);
    setEditorTarget("new");
  }

  function openEdit(testimonial: Testimonial) {
    setForm({
      person_name: testimonial.person_name,
      testimonial_text: testimonial.testimonial_text,
      profile_media_asset_id: testimonial.profile_media_asset_id,
      profile_image_url:
        testimonial.profile_thumbnail_url ?? testimonial.profile_image_url,
      linkedin_url: testimonial.linkedin_url ?? "",
      is_active: testimonial.is_active,
    });
    setEditorTarget(testimonial);
  }

  async function handleSave() {
    const personName = form.person_name.trim();
    const testimonialText = form.testimonial_text.trim();

    if (!personName || !testimonialText) {
      showToast({
        type: "error",
        title: "Required fields missing",
        message: "Add the person's name and recommendation text.",
      });
      return;
    }

    const payload: TestimonialWritePayload = {
      person_name: personName,
      testimonial_text: testimonialText,
      profile_media_asset_id: form.profile_media_asset_id,
      linkedin_url: form.linkedin_url.trim() || null,
      is_active: form.is_active,
    };

    setIsSaving(true);

    try {
      if (editorTarget === "new") {
        await createTestimonial(payload);

        showToast({
          type: "success",
          title: "Testimonial added",
          message: `${personName}'s recommendation was created.`,
        });
      } else if (editorTarget) {
        await updateTestimonial(editorTarget.id, payload);

        showToast({
          type: "success",
          title: "Testimonial updated",
          message: `${personName}'s recommendation was saved.`,
        });
      }

      setEditorTarget(null);
      await loadTestimonials();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not save testimonial",
        message: getErrorMessage(error),
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) {
      return;
    }

    setIsDeleting(true);

    try {
      await deleteTestimonial(deleteTarget.id);

      showToast({
        type: "success",
        title: "Testimonial deleted",
        message: `${deleteTarget.person_name}'s recommendation was removed.`,
      });

      setDeleteTarget(null);
      await loadTestimonials();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not delete testimonial",
        message: getErrorMessage(error),
      });
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleToggle(testimonial: Testimonial) {
    if (savingId !== null) {
      return;
    }

    setSavingId(testimonial.id);

    try {
      await updateTestimonial(testimonial.id, {
        person_name: testimonial.person_name,
        testimonial_text: testimonial.testimonial_text,
        profile_media_asset_id: testimonial.profile_media_asset_id,
        linkedin_url: testimonial.linkedin_url,
        is_active: !testimonial.is_active,
      });

      showToast({
        type: "success",
        title: testimonial.is_active
          ? "Testimonial hidden"
          : "Testimonial active",
        message: testimonial.is_active
          ? `${testimonial.person_name} is no longer public.`
          : `${testimonial.person_name} can now appear publicly.`,
      });

      await loadTestimonials();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not update testimonial",
        message: getErrorMessage(error),
      });
    } finally {
      setSavingId(null);
    }
  }

  async function moveTestimonial(index: number, direction: -1 | 1) {
    if (!canReorder || isReordering) {
      return;
    }

    const targetIndex = index + direction;

    if (targetIndex < 0 || targetIndex >= testimonials.length) {
      return;
    }

    const previous = testimonials;
    const next = [...testimonials];

    [next[index], next[targetIndex]] = [next[targetIndex], next[index]];

    const normalized = next.map((testimonial, testimonialIndex) => ({
      ...testimonial,
      display_order: testimonialIndex,
    }));

    setTestimonials(normalized);
    setIsReordering(true);

    try {
      await reorderTestimonials(
        normalized.map((testimonial) => ({
          id: testimonial.id,
          display_order: testimonial.display_order,
        })),
      );

      showToast({
        type: "success",
        title: "Order updated",
        message: "Testimonial display order was saved.",
      });
    } catch (error) {
      setTestimonials(previous);

      showToast({
        type: "error",
        title: "Could not reorder testimonials",
        message: getErrorMessage(error),
      });
    } finally {
      setIsReordering(false);
    }
  }

  async function handleMediaUpload(files: File[]) {
    if (!files.length || isUploading) {
      return;
    }

    const imageFiles = files.filter((file) => file.type.startsWith("image/"));

    if (imageFiles.length !== files.length) {
      showToast({
        type: "error",
        title: "Images only",
        message: "Testimonial profile photos must be image files.",
      });
    }

    if (imageFiles.length === 0) {
      return;
    }

    setIsUploading(true);

    try {
      const asset = await uploadMedia(imageFiles[0]);

      setForm((current) => ({
        ...current,
        profile_media_asset_id: asset.id,
        profile_image_url: getMediaPreviewUrl(asset),
      }));

      showToast({
        type: "success",
        title: "Photo uploaded",
        message: "The new Media Library image was selected.",
      });

      setIsMediaOpen(false);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not upload photo",
        message: getErrorMessage(error),
      });
    } finally {
      setIsUploading(false);
    }
  }

  function handleUploadInput(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    void handleMediaUpload(files);
  }

  return (
    <div className="admin-page testimonials-page">
      <header className="admin-page-header testimonials-page__header">
        <div>
          <span className="admin-eyebrow">Portfolio content</span>
          <h1>Testimonials</h1>
          <p>
            Manage the recommendations shown on your portfolio and control their
            public display order.
          </p>
        </div>

        <button
          className="admin-primary-action"
          type="button"
          onClick={openCreate}
        >
          <Plus size={19} />
          Add testimonial
        </button>
      </header>

      <section
        className="testimonials-summary"
        aria-label="Testimonial summary"
      >
        <div>
          <span>Total</span>
          <strong>{total}</strong>
          <small>All recommendations</small>
        </div>
        <div>
          <span>Active</span>
          <strong>{counts.active}</strong>
          <small>Visible in this view</small>
        </div>
        <div>
          <span>Inactive</span>
          <strong>{counts.inactive}</strong>
          <small>Visible in this view</small>
        </div>
        <div>
          <span>Public limit</span>
          <strong>3</strong>
          <small>Shown on portfolio</small>
        </div>
      </section>

      <section className="testimonials-toolbar">
        <label className="testimonials-search">
          <Search size={19} />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search testimonials..."
            aria-label="Search testimonials"
          />
        </label>

        <div className="testimonials-segmented" aria-label="Testimonial status">
          {(["all", "active", "inactive"] as TestimonialStatusFilter[]).map(
            (filter) => (
              <button
                key={filter}
                type="button"
                className={
                  statusFilter === filter
                    ? "testimonials-segmented__button testimonials-segmented__button--active"
                    : "testimonials-segmented__button"
                }
                onClick={() => setStatusFilter(filter)}
              >
                {filter === "all"
                  ? "All"
                  : filter === "active"
                    ? "Active"
                    : "Inactive"}
              </button>
            ),
          )}
        </div>
      </section>

      <div
        className={`testimonials-reorder-note${
          hasActiveFilters ? " testimonials-reorder-note--disabled" : ""
        }`}
      >
        {hasActiveFilters
          ? "Clear filters to reorder."
          : "Use the arrows to control the public testimonial order."}
      </div>

      <section className="testimonials-panel">
        {isLoading ? (
          <div className="testimonials-state">
            <LoaderCircle className="testimonials-spin" size={30} />
            <strong>Loading testimonials</strong>
            <span>Fetching your recommendations...</span>
          </div>
        ) : testimonials.length === 0 ? (
          <div className="testimonials-state">
            <div className="testimonials-state__icon">
              <MessageSquareQuote size={29} />
            </div>
            <strong>No testimonials found</strong>
            <span>
              {debouncedSearch || statusFilter !== "all"
                ? "Try changing your search or filters."
                : "Add your first recommendation to get started."}
            </span>
          </div>
        ) : (
          <div className="testimonials-list">
            <AnimatePresence initial={false}>
              {testimonials.map((testimonial, index) => {
                const profileUrl =
                  testimonial.profile_thumbnail_url ??
                  testimonial.profile_image_url;

                return (
                  <motion.article
                    layout
                    key={testimonial.id}
                    className="testimonial-row"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.98 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="testimonial-row__order">
                      <button
                        type="button"
                        aria-label={`Move ${testimonial.person_name} up`}
                        disabled={!canReorder || index === 0 || isReordering}
                        onClick={() => void moveTestimonial(index, -1)}
                      >
                        <ArrowUp size={17} />
                      </button>
                      <span>{index + 1}</span>
                      <button
                        type="button"
                        aria-label={`Move ${testimonial.person_name} down`}
                        disabled={
                          !canReorder ||
                          index === testimonials.length - 1 ||
                          isReordering
                        }
                        onClick={() => void moveTestimonial(index, 1)}
                      >
                        <ArrowDown size={17} />
                      </button>
                    </div>

                    <div className="testimonial-row__avatar">
                      {profileUrl ? (
                        <img src={profileUrl} alt="" />
                      ) : (
                        <span>{initials(testimonial.person_name)}</span>
                      )}
                    </div>

                    <div className="testimonial-row__content">
                      <div className="testimonial-row__title">
                        <h2>{testimonial.person_name}</h2>
                        <span
                          className={
                            testimonial.is_active
                              ? "testimonial-status testimonial-status--active"
                              : "testimonial-status testimonial-status--inactive"
                          }
                        >
                          {testimonial.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <p>“{testimonial.testimonial_text}”</p>
                    </div>

                    <div className="testimonial-row__actions">
                      {testimonial.linkedin_url ? (
                        <a
                          href={testimonial.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          aria-label={`Open ${testimonial.person_name} on LinkedIn`}
                          title="LinkedIn"
                        >
                          <ExternalLink size={18} />
                        </a>
                      ) : null}

                      <button
                        className={
                          testimonial.is_active
                            ? "testimonial-visibility testimonial-visibility--active"
                            : "testimonial-visibility"
                        }
                        type="button"
                        disabled={savingId !== null}
                        onClick={() => void handleToggle(testimonial)}
                        title={
                          testimonial.is_active
                            ? "Deactivate testimonial"
                            : "Activate testimonial"
                        }
                      >
                        {savingId === testimonial.id ? (
                          <LoaderCircle
                            className="testimonials-spin"
                            size={17}
                          />
                        ) : (
                          <Check size={17} />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => openEdit(testimonial)}
                        aria-label={`Edit ${testimonial.person_name}`}
                        title="Edit"
                      >
                        <Pencil size={18} />
                      </button>

                      <button
                        className="testimonial-row__delete"
                        type="button"
                        onClick={() => setDeleteTarget(testimonial)}
                        aria-label={`Delete ${testimonial.person_name}`}
                        title="Delete"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </motion.article>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </section>

      <AnimatePresence>
        {editorTarget ? (
          <motion.div
            className="testimonials-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="testimonials-modal-backdrop"
              type="button"
              aria-label="Close testimonial editor"
              onClick={() => setEditorTarget(null)}
            />

            <motion.div
              className="testimonial-editor"
              role="dialog"
              aria-modal="true"
              aria-labelledby="testimonial-editor-title"
              initial={{ opacity: 0, y: 18, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.985 }}
              transition={{ duration: 0.2 }}
            >
              <header className="testimonial-editor__header">
                <div>
                  <span className="admin-eyebrow">
                    {editorTarget === "new"
                      ? "New recommendation"
                      : "Edit recommendation"}
                  </span>
                  <h2 id="testimonial-editor-title">
                    {editorTarget === "new"
                      ? "Add testimonial"
                      : form.person_name || "Edit testimonial"}
                  </h2>
                  <p>
                    Add the recommendation exactly as you want it presented on
                    your portfolio.
                  </p>
                </div>

                <button
                  className="testimonial-editor__close"
                  type="button"
                  aria-label="Close"
                  onClick={() => setEditorTarget(null)}
                >
                  <X size={20} />
                </button>
              </header>

              <div className="testimonial-editor__body">
                <section className="testimonial-editor__photo">
                  <div className="testimonial-editor__photo-preview">
                    {form.profile_image_url ? (
                      <img src={form.profile_image_url} alt="" />
                    ) : (
                      <span>{initials(form.person_name)}</span>
                    )}
                  </div>

                  <div>
                    <strong>Profile photo</strong>
                    <p>
                      Optional. Select an existing Media Library image or upload
                      a new one.
                    </p>

                    <div className="testimonial-editor__photo-actions">
                      <button
                        type="button"
                        onClick={() => setIsMediaOpen(true)}
                      >
                        <ImageIcon size={17} />
                        Choose image
                      </button>

                      {form.profile_media_asset_id ? (
                        <button
                          type="button"
                          onClick={() =>
                            setForm((current) => ({
                              ...current,
                              profile_media_asset_id: null,
                              profile_image_url: null,
                            }))
                          }
                        >
                          <X size={17} />
                          Remove
                        </button>
                      ) : null}
                    </div>
                  </div>
                </section>

                <label className="testimonial-field">
                  <span>Name</span>
                  <input
                    value={form.person_name}
                    maxLength={200}
                    placeholder="Person's full name"
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        person_name: event.target.value,
                      }))
                    }
                  />
                </label>

                <label className="testimonial-field">
                  <span>Recommendation</span>
                  <textarea
                    value={form.testimonial_text}
                    rows={8}
                    placeholder="Paste the recommendation here..."
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        testimonial_text: event.target.value,
                      }))
                    }
                  />
                </label>

                <label className="testimonial-field">
                  <span>LinkedIn profile</span>
                  <input
                    type="url"
                    value={form.linkedin_url}
                    placeholder="https://www.linkedin.com/in/..."
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        linkedin_url: event.target.value,
                      }))
                    }
                  />
                  <small>Optional link to the person's LinkedIn profile.</small>
                </label>

                <label className="testimonial-editor__active">
                  <div>
                    <strong>Active testimonial</strong>
                    <span>
                      Active recommendations are eligible to appear publicly.
                    </span>
                  </div>

                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        is_active: event.target.checked,
                      }))
                    }
                  />
                  <span className="testimonial-editor__switch" />
                </label>
              </div>

              <footer className="testimonial-editor__footer">
                <button
                  className="testimonial-secondary-button"
                  type="button"
                  disabled={isSaving}
                  onClick={() => setEditorTarget(null)}
                >
                  Cancel
                </button>

                <button
                  className="admin-primary-action"
                  type="button"
                  disabled={isSaving}
                  onClick={() => void handleSave()}
                >
                  {isSaving ? (
                    <LoaderCircle className="testimonials-spin" size={18} />
                  ) : (
                    <Check size={18} />
                  )}
                  {isSaving ? "Saving..." : "Save testimonial"}
                </button>
              </footer>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {isMediaOpen ? (
          <motion.div
            className="testimonials-modal-layer testimonials-modal-layer--media"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="testimonials-modal-backdrop"
              type="button"
              aria-label="Close media picker"
              onClick={() => setIsMediaOpen(false)}
            />

            <motion.div
              className="testimonial-media-picker"
              role="dialog"
              aria-modal="true"
              aria-labelledby="testimonial-media-title"
              initial={{ opacity: 0, y: 18, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.985 }}
              transition={{ duration: 0.2 }}
            >
              <header className="testimonial-editor__header">
                <div>
                  <span className="admin-eyebrow">Media Library</span>
                  <h2 id="testimonial-media-title">Choose profile photo</h2>
                  <p>Select one image for this testimonial.</p>
                </div>

                <button
                  className="testimonial-editor__close"
                  type="button"
                  aria-label="Close"
                  onClick={() => setIsMediaOpen(false)}
                >
                  <X size={20} />
                </button>
              </header>

              <div className="testimonial-media-picker__toolbar">
                <label className="testimonials-search">
                  <Search size={18} />
                  <input
                    value={mediaSearch}
                    placeholder="Search images..."
                    onChange={(event) => setMediaSearch(event.target.value)}
                  />
                </label>

                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/avif"
                  hidden
                  onChange={handleUploadInput}
                />

                <button
                  className="testimonial-secondary-button"
                  type="button"
                  disabled={isUploading}
                  onClick={() => uploadInputRef.current?.click()}
                >
                  {isUploading ? (
                    <LoaderCircle className="testimonials-spin" size={17} />
                  ) : (
                    <Upload size={17} />
                  )}
                  {isUploading ? "Uploading..." : "Upload new"}
                </button>
              </div>

              <div className="testimonial-media-picker__content">
                {isMediaLoading ? (
                  <div className="testimonials-state">
                    <LoaderCircle className="testimonials-spin" size={28} />
                    <strong>Loading images</strong>
                    <span>Fetching your Media Library...</span>
                  </div>
                ) : mediaAssets.length === 0 ? (
                  <div className="testimonials-state">
                    <div className="testimonials-state__icon">
                      <ImageIcon size={28} />
                    </div>
                    <strong>No images found</strong>
                    <span>
                      {debouncedMediaSearch
                        ? "Try a different search."
                        : "Upload your first profile image."}
                    </span>
                  </div>
                ) : (
                  <div className="testimonial-media-picker__grid">
                    {mediaAssets.map((asset) => {
                      const preview = getMediaPreviewUrl(asset);
                      const selected = form.profile_media_asset_id === asset.id;

                      return (
                        <button
                          key={asset.id}
                          className={
                            selected
                              ? "testimonial-media-picker__asset testimonial-media-picker__asset--selected"
                              : "testimonial-media-picker__asset"
                          }
                          type="button"
                          onClick={() => {
                            setForm((current) => ({
                              ...current,
                              profile_media_asset_id: asset.id,
                              profile_image_url: preview,
                            }));
                            setIsMediaOpen(false);
                          }}
                        >
                          <div className="testimonial-media-picker__preview">
                            {preview ? (
                              <img
                                src={preview}
                                alt={asset.alt_text || asset.original_filename}
                              />
                            ) : (
                              <UserRound size={28} />
                            )}

                            {selected ? (
                              <span>
                                <Check size={15} />
                              </span>
                            ) : null}
                          </div>

                          <strong>{asset.original_filename}</strong>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {deleteTarget ? (
          <motion.div
            className="testimonials-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="testimonials-modal-backdrop"
              type="button"
              aria-label="Close delete confirmation"
              onClick={() => setDeleteTarget(null)}
            />

            <motion.div
              className="testimonial-delete-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="testimonial-delete-title"
              initial={{ opacity: 0, y: 14, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.985 }}
            >
              <div className="testimonial-delete-modal__icon">
                <Trash2 size={22} />
              </div>

              <span className="admin-eyebrow">Delete testimonial</span>
              <h2 id="testimonial-delete-title">
                Remove {deleteTarget.person_name}?
              </h2>
              <p>
                This removes the testimonial from your portfolio database. Its
                Media Library image will remain available.
              </p>

              <div className="testimonial-delete-modal__actions">
                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={() => setDeleteTarget(null)}
                >
                  Cancel
                </button>

                <button
                  className="testimonial-delete-modal__confirm"
                  type="button"
                  disabled={isDeleting}
                  onClick={() => void handleDelete()}
                >
                  {isDeleting ? (
                    <LoaderCircle className="testimonials-spin" size={17} />
                  ) : (
                    <Trash2 size={17} />
                  )}
                  {isDeleting ? "Deleting..." : "Delete testimonial"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
