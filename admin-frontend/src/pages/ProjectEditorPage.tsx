import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  CalendarDays,
  Check,
  ChevronRight,
  ExternalLink,
  FolderKanban,
  GripVertical,
  Image as ImageIcon,
  Images,
  Layers3,
  Link2,
  LoaderCircle,
  Plus,
  Save,
  Sparkles,
  Star,
  Tag,
  Trash2,
} from "lucide-react";
import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ProjectMediaPicker } from "../components/projects/ProjectMediaPicker";
import { useToast } from "../context/toastContext";
import { getProject, updateProject } from "../services/projectsApi";
import type { MediaAsset } from "../types/media";
import type { Project, ProjectWritePayload } from "../types/project";

function GithubIcon({ size = 18 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.426 2.865 8.184 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.866-.014-1.7-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.071 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.091-.647.349-1.088.635-1.338-2.221-.253-4.555-1.112-4.555-4.947 0-1.093.39-1.987 1.029-2.686-.103-.253-.446-1.272.098-2.65 0 0 .84-.269 2.75 1.026A9.564 9.564 0 0 1 12 6.847a9.59 9.59 0 0 1 2.504.337c1.909-1.295 2.747-1.026 2.747-1.026.546 1.378.203 2.397.1 2.65.64.699 1.028 1.593 1.028 2.686 0 3.844-2.337 4.691-4.566 4.94.359.31.678.921.678 1.856 0 1.34-.012 2.421-.012 2.75 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z" />
    </svg>
  );
}

interface EditorImage {
  key: string;
  mediaAssetId: number;
  label: string;
  mediaUrl: string | null;
  thumbnailUrl: string | null;
  altText: string | null;
}

interface EditorFeature {
  key: string;
  text: string;
}

interface EditorTechItem {
  key: string;
  name: string;
}

interface EditorTechGroup {
  key: string;
  label: string;
  items: EditorTechItem[];
}

interface EditorState {
  title: string;
  slug: string;
  projectType: string;
  projectMonth: string;
  shortDescription: string;
  longDescription: string;
  githubUrl: string;
  showGithubLink: boolean;
  demoUrl: string;
  isFeatured: boolean;
  isPublished: boolean;
  tags: string[];
  images: EditorImage[];
  coverMediaAssetId: number | null;
  features: EditorFeature[];
  techGroups: EditorTechGroup[];
}

let localKey = 0;

function nextKey(prefix: string): string {
  localKey += 1;
  return `${prefix}-${localKey}`;
}

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

function monthValue(date: string | null): string {
  if (!date) {
    return "";
  }

  return date.slice(0, 7);
}

function projectToEditor(project: Project): EditorState {
  return {
    title: project.title,
    slug: project.slug,
    projectType: project.project_type ?? "",
    projectMonth: monthValue(project.project_date),
    shortDescription: project.short_description ?? "",
    longDescription: project.long_description ?? "",
    githubUrl: project.github_url ?? "",
    showGithubLink: project.show_github_link,
    demoUrl: project.demo_url ?? "",
    isFeatured: project.is_featured,
    isPublished: project.is_published,
    tags: project.tags.map((tag) => tag.label),
    images: project.images.map((image) => ({
      key: nextKey("image"),
      mediaAssetId: image.media_asset_id,
      label: image.label ?? "",
      mediaUrl: image.media_url,
      thumbnailUrl: image.thumbnail_url,
      altText: image.alt_text,
    })),
    coverMediaAssetId: project.cover_media_asset_id,
    features: project.features.map((feature) => ({
      key: nextKey("feature"),
      text: feature.text,
    })),
    techGroups: project.tech_groups.map((group) => ({
      key: nextKey("group"),
      label: group.label,
      items: group.items.map((item) => ({
        key: nextKey("tech"),
        name: item.name,
      })),
    })),
  };
}

function createPayload(
  state: EditorState,
  publishOverride?: boolean,
): ProjectWritePayload {
  return {
    slug: state.slug.trim() || null,
    title: state.title.trim(),
    project_type: state.projectType.trim() || null,
    short_description: state.shortDescription.trim() || null,
    long_description: state.longDescription.trim() || null,
    project_date: state.projectMonth ? `${state.projectMonth}-01` : null,
    cover_media_asset_id: state.coverMediaAssetId,
    github_url: state.githubUrl.trim() || null,
    show_github_link: state.showGithubLink,
    demo_url: state.demoUrl.trim() || null,
    is_featured: state.isFeatured,
    is_published: publishOverride ?? state.isPublished,
    tags: state.tags
      .map((tag) => tag.trim())
      .filter(Boolean)
      .map((label) => ({ label })),
    images: state.images.map((image) => ({
      media_asset_id: image.mediaAssetId,
      label: image.label.trim() || null,
    })),
    features: state.features
      .map((feature) => feature.text.trim())
      .filter(Boolean)
      .map((text) => ({ text })),
    tech_groups: state.techGroups
      .map((group) => ({
        label: group.label.trim(),
        items: group.items
          .map((item) => item.name.trim())
          .filter(Boolean)
          .map((name) => ({ name })),
      }))
      .filter((group) => group.label || group.items.length > 0),
  };
}

function moveItem<T>(items: T[], index: number, direction: -1 | 1): T[] {
  const target = index + direction;

  if (target < 0 || target >= items.length) {
    return items;
  }

  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

function EditorSection({
  eyebrow,
  title,
  description,
  icon,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      className="project-editor-section"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
    >
      <header className="project-editor-section__header">
        <div className="project-editor-section__icon">{icon}</div>
        <div>
          <span>{eyebrow}</span>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </header>
      <div className="project-editor-section__body">{children}</div>
    </motion.section>
  );
}

export default function ProjectEditorPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const numericProjectId = Number(projectId);

  const [project, setProject] = useState<Project | null>(null);
  const [form, setForm] = useState<EditorState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [tagDraft, setTagDraft] = useState("");
  const [isMediaPickerOpen, setIsMediaPickerOpen] = useState(false);

  const loadProject = useCallback(async () => {
    if (!Number.isInteger(numericProjectId) || numericProjectId <= 0) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);

    try {
      const data = await getProject(numericProjectId);
      setProject(data);
      setForm(projectToEditor(data));
    } catch (error) {
      showToast({
        title: "Could not load project",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsLoading(false);
    }
  }, [numericProjectId, showToast]);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      if (!cancelled) {
        void loadProject();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [loadProject]);

  const completion = useMemo(() => {
    if (!form) {
      return 0;
    }

    const checks = [
      Boolean(form.title.trim()),
      Boolean(form.projectType.trim()),
      Boolean(form.projectMonth),
      Boolean(form.shortDescription.trim()),
      Boolean(form.longDescription.trim()),
      form.images.length > 0,
      Boolean(form.coverMediaAssetId),
      form.features.some((feature) => feature.text.trim()),
      form.techGroups.some(
        (group) =>
          group.label.trim() && group.items.some((item) => item.name.trim()),
      ),
    ];

    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [form]);

  const updateField = <K extends keyof EditorState>(
    field: K,
    value: EditorState[K],
  ) => {
    setForm((current) =>
      current
        ? {
            ...current,
            [field]: value,
          }
        : current,
    );
  };

  const save = async (publishOverride?: boolean) => {
    if (!form || !project || isSaving) {
      return;
    }

    if (!form.title.trim()) {
      showToast({
        title: "Title required",
        message: "Add a project title before saving.",
        type: "error",
      });
      return;
    }

    setIsSaving(true);

    try {
      const updated = await updateProject(
        project.id,
        createPayload(form, publishOverride),
      );

      setProject(updated);
      setForm(projectToEditor(updated));

      showToast({
        title: publishOverride
          ? "Project published"
          : updated.is_published
            ? "Project saved"
            : "Draft saved",
        message: publishOverride
          ? `${updated.title} is now live.`
          : "Your latest project changes have been saved.",
        type: "success",
      });
    } catch (error) {
      showToast({
        title: publishOverride ? "Could not publish" : "Could not save project",
        message: getErrorMessage(error),
        type: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const addTag = () => {
    if (!form) {
      return;
    }

    const tag = tagDraft.trim();

    if (!tag) {
      return;
    }

    if (
      form.tags.some(
        (existing) => existing.toLocaleLowerCase() === tag.toLocaleLowerCase(),
      )
    ) {
      showToast({
        title: "Tag already added",
        message: `"${tag}" is already part of this project.`,
        type: "info",
      });
      return;
    }

    updateField("tags", [...form.tags, tag]);
    setTagDraft("");
  };

  const addProjectImages = (assets: MediaAsset[]) => {
    if (!form || assets.length === 0) {
      return;
    }

    const existingIds = new Set(form.images.map((image) => image.mediaAssetId));

    const additions: EditorImage[] = assets
      .filter((asset) => !existingIds.has(asset.id))
      .map((asset) => ({
        key: nextKey("image"),
        mediaAssetId: asset.id,
        label: "",
        mediaUrl: asset.url,
        thumbnailUrl:
          asset.variants.find((variant) => variant.variant_name === "thumbnail")
            ?.url ??
          asset.variants.find((variant) => variant.variant_name === "small")
            ?.url ??
          asset.url,
        altText: asset.alt_text,
      }));

    if (additions.length === 0) {
      return;
    }

    const images = [...form.images, ...additions];

    setForm((current) =>
      current
        ? {
            ...current,
            images,
            coverMediaAssetId:
              current.coverMediaAssetId ?? images[0].mediaAssetId,
          }
        : current,
    );
  };

  const updateImageLabel = (key: string, label: string) => {
    if (!form) {
      return;
    }

    updateField(
      "images",
      form.images.map((image) =>
        image.key === key ? { ...image, label } : image,
      ),
    );
  };

  const setCoverImage = (mediaAssetId: number) => {
    updateField("coverMediaAssetId", mediaAssetId);
  };

  const removeProjectImage = (key: string) => {
    if (!form) {
      return;
    }

    const removed = form.images.find((image) => image.key === key);

    if (!removed) {
      return;
    }

    const images = form.images.filter((image) => image.key !== key);

    setForm((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        images,
        coverMediaAssetId:
          current.coverMediaAssetId === removed.mediaAssetId
            ? (images[0]?.mediaAssetId ?? null)
            : current.coverMediaAssetId,
      };
    });
  };

  const moveProjectImage = (index: number, direction: -1 | 1) => {
    if (!form) {
      return;
    }

    updateField("images", moveItem(form.images, index, direction));
  };

  const addFeature = () => {
    if (!form) {
      return;
    }

    updateField("features", [
      ...form.features,
      { key: nextKey("feature"), text: "" },
    ]);
  };

  const updateFeature = (key: string, text: string) => {
    if (!form) {
      return;
    }

    updateField(
      "features",
      form.features.map((feature) =>
        feature.key === key ? { ...feature, text } : feature,
      ),
    );
  };

  const removeFeature = (key: string) => {
    if (!form) {
      return;
    }

    updateField(
      "features",
      form.features.filter((feature) => feature.key !== key),
    );
  };

  const moveFeature = (index: number, direction: -1 | 1) => {
    if (!form) {
      return;
    }

    updateField("features", moveItem(form.features, index, direction));
  };

  const addTechGroup = () => {
    if (!form) {
      return;
    }

    updateField("techGroups", [
      ...form.techGroups,
      {
        key: nextKey("group"),
        label: "",
        items: [{ key: nextKey("tech"), name: "" }],
      },
    ]);
  };

  const updateTechGroupLabel = (groupKey: string, label: string) => {
    if (!form) {
      return;
    }

    updateField(
      "techGroups",
      form.techGroups.map((group) =>
        group.key === groupKey ? { ...group, label } : group,
      ),
    );
  };

  const removeTechGroup = (groupKey: string) => {
    if (!form) {
      return;
    }

    updateField(
      "techGroups",
      form.techGroups.filter((group) => group.key !== groupKey),
    );
  };

  const moveTechGroup = (index: number, direction: -1 | 1) => {
    if (!form) {
      return;
    }

    updateField("techGroups", moveItem(form.techGroups, index, direction));
  };

  const addTechItem = (groupKey: string) => {
    if (!form) {
      return;
    }

    updateField(
      "techGroups",
      form.techGroups.map((group) =>
        group.key === groupKey
          ? {
              ...group,
              items: [...group.items, { key: nextKey("tech"), name: "" }],
            }
          : group,
      ),
    );
  };

  const updateTechItem = (groupKey: string, itemKey: string, name: string) => {
    if (!form) {
      return;
    }

    updateField(
      "techGroups",
      form.techGroups.map((group) =>
        group.key === groupKey
          ? {
              ...group,
              items: group.items.map((item) =>
                item.key === itemKey ? { ...item, name } : item,
              ),
            }
          : group,
      ),
    );
  };

  const removeTechItem = (groupKey: string, itemKey: string) => {
    if (!form) {
      return;
    }

    updateField(
      "techGroups",
      form.techGroups.map((group) =>
        group.key === groupKey
          ? {
              ...group,
              items: group.items.filter((item) => item.key !== itemKey),
            }
          : group,
      ),
    );
  };

  const moveTechItem = (groupKey: string, index: number, direction: -1 | 1) => {
    if (!form) {
      return;
    }

    updateField(
      "techGroups",
      form.techGroups.map((group) =>
        group.key === groupKey
          ? {
              ...group,
              items: moveItem(group.items, index, direction),
            }
          : group,
      ),
    );
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void save();
  };

  if (isLoading) {
    return (
      <div className="admin-page project-editor-page">
        <div className="project-editor-loading">
          <LoaderCircle className="projects-spin" size={34} />
          <strong>Loading project</strong>
          <span>Preparing the editor…</span>
        </div>
      </div>
    );
  }

  if (!project || !form) {
    return (
      <div className="admin-page project-editor-page">
        <div className="project-editor-not-found">
          <FolderKanban size={32} />
          <span className="admin-eyebrow">Project editor</span>
          <h1>Project not found</h1>
          <p>
            This project could not be loaded. It may have been removed or the
            URL may be incorrect.
          </p>
          <button
            className="admin-primary-action"
            type="button"
            onClick={() => navigate("/projects")}
          >
            <ArrowLeft size={18} />
            Back to projects
          </button>
        </div>
      </div>
    );
  }

  return (
    <form className="admin-page project-editor-page" onSubmit={submit}>
      <div className="project-editor-topbar">
        <div>
          <Link className="project-editor-back" to="/projects">
            <ArrowLeft size={18} />
            Projects
          </Link>

          <div className="project-editor-heading">
            <div>
              <span className="admin-eyebrow">Project editor</span>
              <h1>{form.title || "Untitled project"}</h1>
              <p>
                Manage the content, technologies, links and publishing status
                for this portfolio project.
              </p>
            </div>

            <div className="project-editor-heading__badges">
              <span
                className={
                  project.is_published
                    ? "project-status project-status--published"
                    : "project-status project-status--draft"
                }
              >
                {project.is_published ? "Published" : "Draft"}
              </span>

              {form.isFeatured ? (
                <span className="project-featured">
                  <Sparkles size={13} />
                  Featured
                </span>
              ) : null}
            </div>
          </div>
        </div>

        <div className="project-editor-topbar__actions">
          <button
            className="project-editor-button project-editor-button--secondary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? (
              <LoaderCircle className="projects-spin" size={18} />
            ) : (
              <Save size={18} />
            )}
            Save
          </button>

          {!project.is_published ? (
            <button
              className="admin-primary-action"
              type="button"
              disabled={isSaving}
              onClick={() => void save(true)}
            >
              <Check size={18} />
              Publish
            </button>
          ) : null}
        </div>
      </div>

      <div className="project-editor-layout">
        <main className="project-editor-main">
          <EditorSection
            eyebrow="01 · Details"
            title="Project information"
            description="The core content visitors will see across project cards and the detail page."
            icon={<FolderKanban size={21} />}
          >
            <div className="project-editor-fields project-editor-fields--two">
              <label className="project-editor-field">
                <span>Project title *</span>
                <input
                  value={form.title}
                  maxLength={200}
                  placeholder="Bookaify"
                  onChange={(event) => updateField("title", event.target.value)}
                />
              </label>

              <label className="project-editor-field">
                <span>Slug</span>
                <input
                  value={form.slug}
                  maxLength={160}
                  placeholder="bookaify"
                  onChange={(event) =>
                    updateField(
                      "slug",
                      event.target.value
                        .toLowerCase()
                        .replace(/[^a-z0-9-]/g, "-")
                        .replace(/-+/g, "-")
                        .replace(/^-|-$/g, ""),
                    )
                  }
                />
                <small>Used in the public project URL.</small>
              </label>

              <label className="project-editor-field">
                <span>Project type *</span>
                <input
                  value={form.projectType}
                  maxLength={120}
                  placeholder="Full-Stack Web Application"
                  onChange={(event) =>
                    updateField("projectType", event.target.value)
                  }
                />
              </label>

              <label className="project-editor-field">
                <span>Project date *</span>
                <div className="project-editor-input-icon">
                  <CalendarDays size={18} />
                  <input
                    type="month"
                    value={form.projectMonth}
                    onChange={(event) =>
                      updateField("projectMonth", event.target.value)
                    }
                  />
                </div>
              </label>
            </div>

            <label className="project-editor-field">
              <span>Short description *</span>
              <textarea
                value={form.shortDescription}
                maxLength={500}
                rows={4}
                placeholder="A concise summary used on project cards and introductory sections."
                onChange={(event) =>
                  updateField("shortDescription", event.target.value)
                }
              />
              <small>{form.shortDescription.length}/500 characters</small>
            </label>

            <label className="project-editor-field">
              <span>Long description *</span>
              <textarea
                className="project-editor-textarea--large"
                value={form.longDescription}
                rows={9}
                placeholder="Explain the problem, your approach, architecture, implementation and outcome."
                onChange={(event) =>
                  updateField("longDescription", event.target.value)
                }
              />
            </label>
          </EditorSection>

          <EditorSection
            eyebrow="02 · Gallery"
            title="Project gallery"
            description="Choose existing Media Library images, set the cover image and control the order shown on the public project page."
            icon={<Images size={21} />}
          >
            <div className="project-gallery-toolbar">
              <div>
                <strong>
                  {form.images.length} image
                  {form.images.length === 1 ? "" : "s"}
                </strong>
                <span>
                  Removing an image here never deletes it from Media Library or
                  R2.
                </span>
              </div>

              <button
                className="project-editor-add-button"
                type="button"
                onClick={() => setIsMediaPickerOpen(true)}
              >
                <Plus size={18} />
                Add images
              </button>
            </div>

            {form.images.length > 0 ? (
              <div className="project-gallery-list">
                <AnimatePresence initial={false}>
                  {form.images.map((image, index) => {
                    const isCover =
                      form.coverMediaAssetId === image.mediaAssetId;
                    const preview = image.thumbnailUrl ?? image.mediaUrl;

                    return (
                      <motion.article
                        layout
                        key={image.key}
                        className={`project-gallery-item${
                          isCover ? " project-gallery-item--cover" : ""
                        }`}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                      >
                        <div className="project-gallery-item__preview">
                          {preview ? (
                            <img
                              src={preview}
                              alt={
                                image.altText || `Project image ${index + 1}`
                              }
                            />
                          ) : (
                            <ImageIcon size={28} />
                          )}

                          <span>{index + 1}</span>
                        </div>

                        <div className="project-gallery-item__content">
                          <div className="project-gallery-item__heading">
                            <div>
                              <strong>
                                {isCover
                                  ? "Cover image"
                                  : `Gallery image ${index + 1}`}
                              </strong>
                              <span>Media asset #{image.mediaAssetId}</span>
                            </div>

                            {isCover ? (
                              <span className="project-gallery-cover-badge">
                                <Star size={13} />
                                Cover
                              </span>
                            ) : (
                              <button
                                className="project-gallery-cover-action"
                                type="button"
                                onClick={() =>
                                  setCoverImage(image.mediaAssetId)
                                }
                              >
                                <Star size={14} />
                                Set as cover
                              </button>
                            )}
                          </div>

                          <label className="project-editor-field">
                            <span>Optional label</span>
                            <input
                              value={image.label}
                              maxLength={120}
                              placeholder="e.g. Dashboard overview"
                              onChange={(event) =>
                                updateImageLabel(image.key, event.target.value)
                              }
                            />
                          </label>
                        </div>

                        <div className="project-gallery-item__actions">
                          <button
                            type="button"
                            disabled={index === 0}
                            aria-label="Move image up"
                            onClick={() => moveProjectImage(index, -1)}
                          >
                            <ArrowUp size={16} />
                          </button>

                          <button
                            type="button"
                            disabled={index === form.images.length - 1}
                            aria-label="Move image down"
                            onClick={() => moveProjectImage(index, 1)}
                          >
                            <ArrowDown size={16} />
                          </button>

                          <button
                            className="project-editor-danger-icon"
                            type="button"
                            aria-label="Remove image from project"
                            onClick={() => removeProjectImage(image.key)}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </motion.article>
                    );
                  })}
                </AnimatePresence>
              </div>
            ) : (
              <button
                className="project-gallery-empty"
                type="button"
                onClick={() => setIsMediaPickerOpen(true)}
              >
                <span>
                  <Images size={28} />
                </span>
                <strong>Add your project gallery</strong>
                <p>
                  Select screenshots and project imagery from the existing Media
                  Library.
                </p>
                <em>
                  <Plus size={16} />
                  Choose images
                </em>
              </button>
            )}
          </EditorSection>

          <EditorSection
            eyebrow="03 · Links"
            title="Project links"
            description="Connect visitors to the source code and live product when those destinations are available."
            icon={<Link2 size={21} />}
          >
            <div className="project-editor-fields project-editor-fields--two">
              <label className="project-editor-field">
                <span>GitHub repository</span>
                <div className="project-editor-input-icon">
                  <GithubIcon size={18} />
                  <input
                    type="url"
                    value={form.githubUrl}
                    placeholder="https://github.com/..."
                    onChange={(event) =>
                      updateField("githubUrl", event.target.value)
                    }
                  />
                </div>
              </label>

              <label className="project-editor-field">
                <span>Live demo</span>
                <div className="project-editor-input-icon">
                  <ExternalLink size={18} />
                  <input
                    type="url"
                    value={form.demoUrl}
                    placeholder="https://..."
                    onChange={(event) =>
                      updateField("demoUrl", event.target.value)
                    }
                  />
                </div>
              </label>
            </div>

            <label className="project-editor-toggle">
              <input
                type="checkbox"
                checked={form.showGithubLink}
                onChange={(event) =>
                  updateField("showGithubLink", event.target.checked)
                }
              />
              <span className="project-editor-toggle__control" />
              <span>
                <strong>Show GitHub link publicly</strong>
                <small>
                  Keep the repository stored privately in admin without showing
                  it on the portfolio when this is disabled.
                </small>
              </span>
            </label>
          </EditorSection>

          <EditorSection
            eyebrow="04 · Tags"
            title="Project tags"
            description="Add concise labels that help describe and categorize the project."
            icon={<Tag size={21} />}
          >
            <div className="project-editor-add-row">
              <input
                value={tagDraft}
                maxLength={80}
                placeholder="e.g. SaaS"
                onChange={(event) => setTagDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addTag();
                  }
                }}
              />
              <button type="button" onClick={addTag}>
                <Plus size={18} />
                Add tag
              </button>
            </div>

            {form.tags.length > 0 ? (
              <div className="project-editor-tags">
                <AnimatePresence initial={false}>
                  {form.tags.map((tag) => (
                    <motion.span
                      key={tag}
                      layout
                      initial={{ opacity: 0, scale: 0.92 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.92 }}
                    >
                      {tag}
                      <button
                        type="button"
                        aria-label={`Remove ${tag}`}
                        onClick={() =>
                          updateField(
                            "tags",
                            form.tags.filter((item) => item !== tag),
                          )
                        }
                      >
                        ×
                      </button>
                    </motion.span>
                  ))}
                </AnimatePresence>
              </div>
            ) : (
              <div className="project-editor-inline-empty">
                No tags yet. Tags are optional.
              </div>
            )}
          </EditorSection>

          <EditorSection
            eyebrow="05 · Features"
            title="Key features"
            description="Build the ordered list of capabilities highlighted on the project detail page."
            icon={<Sparkles size={21} />}
          >
            <div className="project-editor-stack">
              <AnimatePresence initial={false}>
                {form.features.map((feature, index) => (
                  <motion.div
                    layout
                    key={feature.key}
                    className="project-editor-repeat-row"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                  >
                    <div className="project-editor-repeat-row__grip">
                      <GripVertical size={17} />
                      <span>{index + 1}</span>
                    </div>

                    <input
                      value={feature.text}
                      maxLength={500}
                      placeholder="Describe a key capability..."
                      onChange={(event) =>
                        updateFeature(feature.key, event.target.value)
                      }
                    />

                    <div className="project-editor-repeat-row__actions">
                      <button
                        type="button"
                        disabled={index === 0}
                        aria-label="Move feature up"
                        onClick={() => moveFeature(index, -1)}
                      >
                        <ArrowUp size={16} />
                      </button>
                      <button
                        type="button"
                        disabled={index === form.features.length - 1}
                        aria-label="Move feature down"
                        onClick={() => moveFeature(index, 1)}
                      >
                        <ArrowDown size={16} />
                      </button>
                      <button
                        className="project-editor-danger-icon"
                        type="button"
                        aria-label="Remove feature"
                        onClick={() => removeFeature(feature.key)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {form.features.length === 0 ? (
                <div className="project-editor-inline-empty">
                  No features added yet. Published projects require at least
                  one.
                </div>
              ) : null}

              <button
                className="project-editor-add-button"
                type="button"
                onClick={addFeature}
              >
                <Plus size={18} />
                Add feature
              </button>
            </div>
          </EditorSection>

          <EditorSection
            eyebrow="06 · Technology"
            title="Tech stack"
            description="Create any technology groups you need, then order the technologies inside each group."
            icon={<Layers3 size={21} />}
          >
            <div className="project-editor-tech-groups">
              <AnimatePresence initial={false}>
                {form.techGroups.map((group, groupIndex) => (
                  <motion.div
                    layout
                    key={group.key}
                    className="project-editor-tech-group"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <div className="project-editor-tech-group__header">
                      <div className="project-editor-tech-group__title">
                        <GripVertical size={18} />
                        <span>Group {groupIndex + 1}</span>
                      </div>

                      <div className="project-editor-repeat-row__actions">
                        <button
                          type="button"
                          disabled={groupIndex === 0}
                          aria-label="Move group up"
                          onClick={() => moveTechGroup(groupIndex, -1)}
                        >
                          <ArrowUp size={16} />
                        </button>
                        <button
                          type="button"
                          disabled={groupIndex === form.techGroups.length - 1}
                          aria-label="Move group down"
                          onClick={() => moveTechGroup(groupIndex, 1)}
                        >
                          <ArrowDown size={16} />
                        </button>
                        <button
                          className="project-editor-danger-icon"
                          type="button"
                          aria-label="Remove technology group"
                          onClick={() => removeTechGroup(group.key)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    <label className="project-editor-field">
                      <span>Group name</span>
                      <input
                        value={group.label}
                        maxLength={100}
                        placeholder="Frontend"
                        onChange={(event) =>
                          updateTechGroupLabel(group.key, event.target.value)
                        }
                      />
                    </label>

                    <div className="project-editor-tech-items">
                      {group.items.map((item, itemIndex) => (
                        <div
                          className="project-editor-repeat-row project-editor-repeat-row--compact"
                          key={item.key}
                        >
                          <div className="project-editor-repeat-row__grip">
                            <GripVertical size={16} />
                            <span>{itemIndex + 1}</span>
                          </div>

                          <input
                            value={item.name}
                            maxLength={100}
                            placeholder="React"
                            onChange={(event) =>
                              updateTechItem(
                                group.key,
                                item.key,
                                event.target.value,
                              )
                            }
                          />

                          <div className="project-editor-repeat-row__actions">
                            <button
                              type="button"
                              disabled={itemIndex === 0}
                              aria-label="Move technology up"
                              onClick={() =>
                                moveTechItem(group.key, itemIndex, -1)
                              }
                            >
                              <ArrowUp size={15} />
                            </button>
                            <button
                              type="button"
                              disabled={itemIndex === group.items.length - 1}
                              aria-label="Move technology down"
                              onClick={() =>
                                moveTechItem(group.key, itemIndex, 1)
                              }
                            >
                              <ArrowDown size={15} />
                            </button>
                            <button
                              className="project-editor-danger-icon"
                              type="button"
                              aria-label="Remove technology"
                              onClick={() =>
                                removeTechItem(group.key, item.key)
                              }
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </div>
                      ))}

                      <button
                        className="project-editor-add-button project-editor-add-button--small"
                        type="button"
                        onClick={() => addTechItem(group.key)}
                      >
                        <Plus size={17} />
                        Add technology
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {form.techGroups.length === 0 ? (
                <div className="project-editor-inline-empty">
                  No technology groups yet. Published projects require at least
                  one group with at least one technology.
                </div>
              ) : null}

              <button
                className="project-editor-add-button"
                type="button"
                onClick={addTechGroup}
              >
                <Plus size={18} />
                Add tech group
              </button>
            </div>
          </EditorSection>
        </main>

        <aside className="project-editor-sidebar">
          <div className="project-editor-sidecard project-editor-sidecard--sticky">
            <span className="admin-eyebrow">Publishing</span>
            <h2>Project status</h2>

            <div className="project-editor-progress">
              <div>
                <span>Content readiness</span>
                <strong>{completion}%</strong>
              </div>
              <div className="project-editor-progress__track">
                <span style={{ width: `${completion}%` }} />
              </div>
              <small>
                Gallery readiness will update after we connect the Media Library
                picker.
              </small>
            </div>

            <div className="project-editor-sidecard__divider" />

            <label className="project-editor-toggle">
              <input
                type="checkbox"
                checked={form.isFeatured}
                onChange={(event) =>
                  updateField("isFeatured", event.target.checked)
                }
              />
              <span className="project-editor-toggle__control" />
              <span>
                <strong>
                  <Star size={15} />
                  Featured project
                </strong>
                <small>Highlight this project in featured experiences.</small>
              </span>
            </label>

            <div className="project-editor-sidecard__divider" />

            <div className="project-editor-publish-state">
              <span
                className={
                  project.is_published
                    ? "project-status project-status--published"
                    : "project-status project-status--draft"
                }
              >
                {project.is_published ? "Published" : "Draft"}
              </span>
              <p>
                {project.is_published
                  ? "This project is currently available through the public API."
                  : "This project is private and only visible in the admin portal."}
              </p>
            </div>

            {project.is_published ? (
              <button
                className="project-editor-button project-editor-button--secondary project-editor-button--full"
                type="button"
                disabled={isSaving}
                onClick={() => void save(false)}
              >
                Save as draft
              </button>
            ) : (
              <button
                className="admin-primary-action project-editor-button--full"
                type="button"
                disabled={isSaving}
                onClick={() => void save(true)}
              >
                {isSaving ? (
                  <LoaderCircle className="projects-spin" size={18} />
                ) : (
                  <Check size={18} />
                )}
                Publish project
              </button>
            )}

            <div className="project-editor-sidecard__divider" />

            <div className="project-editor-next">
              <span>Gallery</span>
              <button type="button" onClick={() => setIsMediaPickerOpen(true)}>
                {form.images.length > 0
                  ? `${form.images.length} image${
                      form.images.length === 1 ? "" : "s"
                    } selected`
                  : "Add project images"}
                <ChevronRight size={17} />
              </button>
            </div>
          </div>
        </aside>
      </div>

      <ProjectMediaPicker
        isOpen={isMediaPickerOpen}
        selectedIds={form.images.map((image) => image.mediaAssetId)}
        onClose={() => setIsMediaPickerOpen(false)}
        onConfirm={addProjectImages}
      />
    </form>
  );
}
