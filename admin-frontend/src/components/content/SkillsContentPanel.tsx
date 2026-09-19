import { AxiosError } from "axios";
import { motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  Check,
  Code2,
  GripVertical,
  Image as ImageIcon,
  LoaderCircle,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useToast } from "../../context/toastContext";
import {
  createSkill,
  deleteSkill,
  getSkills,
  reorderSkills,
  updateSkill,
} from "../../services/skillsApi";
import type { MediaAsset } from "../../types/media";
import type { Skill, SkillPayload } from "../../types/skill";
import { getMediaPreviewUrl } from "../media/mediaUtils";
import { ContentMediaPicker } from "./ContentMediaPicker";

type StatusFilter = "all" | "active" | "inactive";

interface SkillFormState {
  name: string;
  media_asset_id: number | null;
  image_url: string | null;
  is_active: boolean;
}

const EMPTY_FORM: SkillFormState = {
  name: "",
  media_asset_id: null,
  image_url: null,
  is_active: true,
};

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const message = detail
        .map((item) =>
          typeof item?.msg === "string"
            ? item.msg.replace(/^Value error,\s*/i, "")
            : "",
        )
        .filter(Boolean)
        .join(" ");

      if (message) {
        return message;
      }
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

function toForm(skill: Skill): SkillFormState {
  return {
    name: skill.name,
    media_asset_id: skill.media_asset_id,
    image_url: skill.thumbnail_url ?? skill.image_url,
    is_active: skill.is_active,
  };
}

function getSkillImage(skill: Skill): string | null {
  return skill.thumbnail_url ?? skill.image_url;
}

export function SkillsContentPanel() {
  const { showToast } = useToast();

  const [skills, setSkills] = useState<Skill[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [form, setForm] = useState<SkillFormState>(EMPTY_FORM);
  const [isSaving, setIsSaving] = useState(false);

  const [mediaPickerOpen, setMediaPickerOpen] = useState(false);

  const [skillToDelete, setSkillToDelete] = useState<Skill | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [reorderingId, setReorderingId] = useState<number | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 250);

    return () => window.clearTimeout(timer);
  }, [search]);

  const reorderEnabled = debouncedSearch.length === 0 && statusFilter === "all";

  const loadSkills = useCallback(async () => {
    setIsLoading(true);

    try {
      const response = await getSkills({
        search: debouncedSearch || undefined,
        is_active:
          statusFilter === "all" ? undefined : statusFilter === "active",
        limit: 100,
        offset: 0,
      });

      setSkills(response.items);
      setTotal(response.total);
    } catch (error) {
      showToast({
        type: "error",
        title: "Couldn't load skills",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, showToast, statusFilter]);

  useEffect(() => {
    void loadSkills();
  }, [loadSkills]);

  useEffect(() => {
    if (!editorOpen && !skillToDelete && !mediaPickerOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || mediaPickerOpen) {
        return;
      }

      if (skillToDelete && !isDeleting) {
        setSkillToDelete(null);
        return;
      }

      if (editorOpen && !isSaving) {
        setEditorOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editorOpen, isDeleting, isSaving, mediaPickerOpen, skillToDelete]);

  const activeCount = useMemo(
    () => skills.filter((skill) => skill.is_active).length,
    [skills],
  );

  const openCreate = () => {
    setEditingSkill(null);
    setForm({ ...EMPTY_FORM });
    setEditorOpen(true);
  };

  const openEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setForm(toForm(skill));
    setEditorOpen(true);
  };

  const closeEditor = () => {
    if (isSaving || mediaPickerOpen) {
      return;
    }

    setEditorOpen(false);
  };

  const handleMediaSelect = (asset: MediaAsset) => {
    setForm((current) => ({
      ...current,
      media_asset_id: asset.id,
      image_url: getMediaPreviewUrl(asset),
    }));
  };

  const handleSave = async () => {
    const name = form.name.trim();

    if (!name) {
      showToast({
        type: "error",
        title: "Technology name required",
        message: "Give this skill a technology or tool name before saving.",
      });
      return;
    }

    if (form.media_asset_id === null) {
      showToast({
        type: "error",
        title: "Logo required",
        message: "Choose a logo from your Media Library before saving.",
      });
      return;
    }

    const payload: SkillPayload = {
      name,
      media_asset_id: form.media_asset_id,
      is_active: form.is_active,
    };

    setIsSaving(true);

    try {
      if (editingSkill) {
        await updateSkill(editingSkill.id, payload);
        showToast({
          type: "success",
          title: "Skill updated",
          message: `${name} was saved successfully.`,
        });
      } else {
        await createSkill(payload);
        showToast({
          type: "success",
          title: "Skill created",
          message: `${name} was added to your technology stack.`,
        });
      }

      setEditorOpen(false);
      await loadSkills();
    } catch (error) {
      showToast({
        type: "error",
        title: editingSkill ? "Couldn't update skill" : "Couldn't create skill",
        message: getErrorMessage(error),
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleActive = async (skill: Skill) => {
    try {
      await updateSkill(skill.id, {
        name: skill.name,
        media_asset_id: skill.media_asset_id,
        is_active: !skill.is_active,
      });

      showToast({
        type: "success",
        title: skill.is_active ? "Skill hidden" : "Skill published",
        message: skill.is_active
          ? `${skill.name} is no longer public.`
          : `${skill.name} is now visible publicly.`,
      });

      await loadSkills();
    } catch (error) {
      showToast({
        type: "error",
        title: "Couldn't update skill",
        message: getErrorMessage(error),
      });
    }
  };

  const handleDelete = async () => {
    if (!skillToDelete) {
      return;
    }

    setIsDeleting(true);

    try {
      await deleteSkill(skillToDelete.id);

      showToast({
        type: "success",
        title: "Skill deleted",
        message: `${skillToDelete.name} was removed.`,
      });

      setSkillToDelete(null);
      await loadSkills();
    } catch (error) {
      showToast({
        type: "error",
        title: "Couldn't delete skill",
        message: getErrorMessage(error),
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const moveSkill = async (skill: Skill, direction: -1 | 1) => {
    if (!reorderEnabled || reorderingId !== null) {
      return;
    }

    const currentIndex = skills.findIndex((item) => item.id === skill.id);
    const targetIndex = currentIndex + direction;

    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= skills.length) {
      return;
    }

    const next = [...skills];
    const [moved] = next.splice(currentIndex, 1);
    next.splice(targetIndex, 0, moved);

    const previous = skills;

    setSkills(next);
    setReorderingId(skill.id);

    try {
      await reorderSkills(
        next.map((item, index) => ({
          id: item.id,
          display_order: index,
        })),
      );

      showToast({
        type: "success",
        title: "Order updated",
        message: `${skill.name} was moved ${direction < 0 ? "up" : "down"}.`,
      });

      await loadSkills();
    } catch (error) {
      setSkills(previous);

      showToast({
        type: "error",
        title: "Couldn't reorder skills",
        message: getErrorMessage(error),
      });
    } finally {
      setReorderingId(null);
    }
  };

  return (
    <>
      <motion.div
        className="skills-content"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <section className="skills-overview">
          <div className="skills-overview__copy">
            <span className="skills-overview__eyebrow">
              <Code2 size={16} />
              Technology stack
            </span>

            <h2>Skills & technologies</h2>

            <p>
              Build the technology stack shown on your portfolio. Pair every
              skill with its real logo, control visibility, and arrange the
              order visitors see.
            </p>
          </div>

          <div className="skills-overview__actions">
            <div className="skills-overview__stat">
              <strong>{total}</strong>
              <span>{total === 1 ? "Skill" : "Skills"}</span>
            </div>

            <div className="skills-overview__stat">
              <strong>{activeCount}</strong>
              <span>Visible here</span>
            </div>

            <button
              type="button"
              className="admin-primary-action"
              onClick={openCreate}
            >
              <Plus size={18} />
              Add skill
            </button>
          </div>
        </section>

        <section className="skills-manager">
          <header className="skills-manager__toolbar">
            <div className="skills-search">
              <Search size={18} />

              <input
                type="search"
                value={search}
                placeholder="Search technologies..."
                aria-label="Search skills"
                onChange={(event) => setSearch(event.target.value)}
              />

              {search ? (
                <button
                  type="button"
                  aria-label="Clear search"
                  onClick={() => setSearch("")}
                >
                  <X size={16} />
                </button>
              ) : null}
            </div>

            <div className="skills-status-filter" aria-label="Filter skills">
              {(
                [
                  ["all", "All"],
                  ["active", "Active"],
                  ["inactive", "Inactive"],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={
                    statusFilter === value
                      ? "skills-status-filter__button skills-status-filter__button--active"
                      : "skills-status-filter__button"
                  }
                  onClick={() => setStatusFilter(value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </header>

          {!reorderEnabled ? (
            <div className="skills-reorder-note">
              <GripVertical size={17} />
              Clear search and filters to change the public display order.
            </div>
          ) : null}

          {isLoading ? (
            <div className="skills-state">
              <LoaderCircle className="website-content-spin" size={30} />
              <strong>Loading skills</strong>
              <span>Fetching your current technology stack...</span>
            </div>
          ) : skills.length === 0 ? (
            <div className="skills-state skills-state--empty">
              <div className="skills-state__icon">
                <Code2 size={25} />
              </div>

              <strong>
                {debouncedSearch || statusFilter !== "all"
                  ? "No matching skills"
                  : "No skills yet"}
              </strong>

              <span>
                {debouncedSearch || statusFilter !== "all"
                  ? "Try another search or clear your filters."
                  : "Add your first technology to start building your stack."}
              </span>

              {!debouncedSearch && statusFilter === "all" ? (
                <button
                  type="button"
                  className="about-secondary-button"
                  onClick={openCreate}
                >
                  <Plus size={17} />
                  Add first skill
                </button>
              ) : null}
            </div>
          ) : (
            <div className="skills-grid">
              {skills.map((skill, index) => {
                const image = getSkillImage(skill);
                const moving = reorderingId === skill.id;

                return (
                  <motion.article
                    layout
                    key={skill.id}
                    className={`skill-admin-card${
                      !skill.is_active ? " skill-admin-card--inactive" : ""
                    }`}
                  >
                    <div className="skill-admin-card__top">
                      <div className="skill-admin-card__order">
                        <GripVertical size={17} />

                        <div>
                          <button
                            type="button"
                            aria-label={`Move ${skill.name} up`}
                            disabled={
                              !reorderEnabled ||
                              index === 0 ||
                              reorderingId !== null
                            }
                            onClick={() => void moveSkill(skill, -1)}
                          >
                            <ArrowUp size={14} />
                          </button>

                          <button
                            type="button"
                            aria-label={`Move ${skill.name} down`}
                            disabled={
                              !reorderEnabled ||
                              index === skills.length - 1 ||
                              reorderingId !== null
                            }
                            onClick={() => void moveSkill(skill, 1)}
                          >
                            <ArrowDown size={14} />
                          </button>
                        </div>
                      </div>

                      <span
                        className={`skill-status${
                          skill.is_active ? " skill-status--active" : ""
                        }`}
                      >
                        <span />
                        {skill.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>

                    <div className="skill-admin-card__visual">
                      {image ? (
                        <img src={image} alt="" loading="lazy" />
                      ) : (
                        <ImageIcon size={34} />
                      )}
                    </div>

                    <div className="skill-admin-card__body">
                      <h3>{skill.name}</h3>
                      <span>Position {index + 1}</span>
                    </div>

                    <div className="skill-admin-card__actions">
                      <label
                        className="skill-active-toggle"
                        title={
                          skill.is_active
                            ? "Hide from public website"
                            : "Show on public website"
                        }
                      >
                        <input
                          type="checkbox"
                          checked={skill.is_active}
                          onChange={() => void handleToggleActive(skill)}
                        />
                        <span />
                      </label>

                      <button
                        type="button"
                        className="skill-card-action"
                        aria-label={`Edit ${skill.name}`}
                        onClick={() => openEdit(skill)}
                      >
                        <Pencil size={17} />
                      </button>

                      <button
                        type="button"
                        className="skill-card-action skill-card-action--danger"
                        aria-label={`Delete ${skill.name}`}
                        onClick={() => setSkillToDelete(skill)}
                      >
                        <Trash2 size={17} />
                      </button>

                      {moving ? (
                        <LoaderCircle
                          className="website-content-spin skill-card-loader"
                          size={17}
                        />
                      ) : null}
                    </div>
                  </motion.article>
                );
              })}
            </div>
          )}
        </section>
      </motion.div>

      {editorOpen ? (
        <div
          className="skill-modal"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeEditor();
            }
          }}
        >
          <motion.section
            className="skill-modal__dialog skill-editor"
            role="dialog"
            aria-modal="true"
            aria-labelledby="skill-editor-title"
            initial={{ opacity: 0, scale: 0.97, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.18 }}
          >
            <header className="skill-modal__header">
              <div>
                <span className="skill-modal__eyebrow">
                  {editingSkill ? "Edit skill" : "New skill"}
                </span>

                <h2 id="skill-editor-title">
                  {editingSkill ? editingSkill.name : "Add a technology"}
                </h2>

                <p>
                  Add the technology name and select its official logo from your
                  Media Library.
                </p>
              </div>

              <button
                type="button"
                className="skill-modal__close"
                aria-label="Close skill editor"
                disabled={isSaving}
                onClick={closeEditor}
              >
                <X size={20} />
              </button>
            </header>

            <div className="skill-editor__body">
              <div className="skill-editor__logo-column">
                <span className="skill-editor__section-label">
                  Technology logo
                </span>

                <button
                  type="button"
                  className="skill-logo-selector"
                  onClick={() => setMediaPickerOpen(true)}
                >
                  <div className="skill-logo-selector__preview">
                    {form.image_url ? (
                      <img src={form.image_url} alt="" />
                    ) : (
                      <ImageIcon size={38} />
                    )}
                  </div>

                  <div className="skill-logo-selector__copy">
                    <strong>
                      {form.media_asset_id ? "Change logo" : "Choose logo"}
                    </strong>
                    <span>Select or upload an image from Media Library.</span>
                  </div>

                  <span className="skill-logo-selector__action">Browse</span>
                </button>
              </div>

              <div className="skill-editor__fields">
                <label className="about-field">
                  <span>Technology name</span>
                  <input
                    value={form.name}
                    maxLength={120}
                    placeholder="Python"
                    autoFocus
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        name: event.target.value,
                      }))
                    }
                  />
                  <small>
                    Use the recognizable public name of the technology or tool.
                  </small>
                </label>

                <label className="skill-editor__visibility">
                  <div>
                    <strong>Publicly visible</strong>
                    <span>Show this technology on the public portfolio.</span>
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

                  <span className="skill-visibility-switch">
                    <span />
                  </span>
                </label>
              </div>
            </div>

            <footer className="skill-modal__footer">
              <button
                type="button"
                className="about-secondary-button"
                disabled={isSaving}
                onClick={closeEditor}
              >
                Cancel
              </button>

              <button
                type="button"
                className="admin-primary-action"
                disabled={isSaving}
                onClick={() => void handleSave()}
              >
                {isSaving ? (
                  <LoaderCircle className="website-content-spin" size={18} />
                ) : (
                  <Check size={18} />
                )}

                {isSaving
                  ? "Saving..."
                  : editingSkill
                    ? "Save changes"
                    : "Add skill"}
              </button>
            </footer>
          </motion.section>
        </div>
      ) : null}

      {skillToDelete ? (
        <div
          className="skill-modal"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !isDeleting) {
              setSkillToDelete(null);
            }
          }}
        >
          <motion.section
            className="skill-modal__dialog skill-delete-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="skill-delete-title"
            initial={{ opacity: 0, scale: 0.97, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.18 }}
          >
            <div className="skill-delete-dialog__icon">
              <Trash2 size={23} />
            </div>

            <span className="skill-modal__eyebrow">Delete skill</span>

            <h2 id="skill-delete-title">Remove {skillToDelete.name}?</h2>

            <p>
              This removes the skill from your portfolio content. The logo
              itself will stay safely stored in Media Library.
            </p>

            <div className="skill-delete-dialog__actions">
              <button
                type="button"
                className="about-secondary-button"
                disabled={isDeleting}
                onClick={() => setSkillToDelete(null)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="skill-danger-action"
                disabled={isDeleting}
                onClick={() => void handleDelete()}
              >
                {isDeleting ? (
                  <LoaderCircle className="website-content-spin" size={17} />
                ) : (
                  <Trash2 size={17} />
                )}

                {isDeleting ? "Deleting..." : "Delete skill"}
              </button>
            </div>
          </motion.section>
        </div>
      ) : null}

      <ContentMediaPicker
        isOpen={mediaPickerOpen}
        mode="skill"
        selectedId={form.media_asset_id}
        onClose={() => setMediaPickerOpen(false)}
        onSelect={handleMediaSelect}
      />
    </>
  );
}
