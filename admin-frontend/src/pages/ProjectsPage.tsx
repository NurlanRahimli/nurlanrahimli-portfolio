import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  ExternalLink,
  FolderKanban,
  ImageOff,
  LoaderCircle,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AxiosError } from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createProject,
  deleteProject,
  listProjects,
  reorderProjects,
} from "../services/projectsApi";
import type {
  ProjectListItem,
  ProjectStatusFilter,
} from "../types/project";
import { useToast } from "../context/toastContext";

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

function formatProjectDate(value: string | null) {
  if (!value) {
    return "Date not set";
  }

  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    year: "numeric",
  }).format(date);
}

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<ProjectStatusFilter>("all");
  const [featuredOnly, setFeaturedOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  const [deleteTarget, setDeleteTarget] =
    useState<ProjectListItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 260);

    return () => window.clearTimeout(timer);
  }, [search]);

  const loadProjects = useCallback(async () => {
    setIsLoading(true);

    try {
      const result = await listProjects({
        search: debouncedSearch || undefined,
        isPublished:
          statusFilter === "all"
            ? undefined
            : statusFilter === "published",
        isFeatured: featuredOnly ? true : undefined,
      });

      setProjects(result.items);
      setTotal(result.total);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load projects",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, featuredOnly, showToast, statusFilter]);

  useEffect(() => {
    let isCancelled = false;

    queueMicrotask(() => {
      if (!isCancelled) {
        void loadProjects();
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [loadProjects]);

  const counts = useMemo(() => {
    const published = projects.filter((project) => project.is_published).length;
    const featured = projects.filter((project) => project.is_featured).length;

    return {
      visible: projects.length,
      published,
      draft: projects.length - published,
      featured,
    };
  }, [projects]);

  async function handleCreate() {
    setIsCreating(true);

    try {
      const project = await createProject({
        title: "Untitled Project",
      });

      showToast({
        type: "success",
        title: "Draft created",
        message: "Your new project is ready to edit.",
      });

      navigate(`/projects/${project.id}`);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not create project",
        message: getErrorMessage(error),
      });
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) {
      return;
    }

    setIsDeleting(true);

    try {
      await deleteProject(deleteTarget.id);

      setDeleteTarget(null);

      showToast({
        type: "success",
        title: "Project deleted",
        message: `${deleteTarget.title} was removed.`,
      });

      await loadProjects();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not delete project",
        message: getErrorMessage(error),
      });
    } finally {
      setIsDeleting(false);
    }
  }

  async function moveProject(index: number, direction: -1 | 1) {
    const targetIndex = index + direction;

    if (
      targetIndex < 0 ||
      targetIndex >= projects.length ||
      isReordering
    ) {
      return;
    }

    const next = [...projects];
    [next[index], next[targetIndex]] = [next[targetIndex], next[index]];

    const previous = projects;
    const normalized = next.map((project, projectIndex) => ({
      ...project,
      display_order: projectIndex,
    }));

    setProjects(normalized);
    setIsReordering(true);

    try {
      await reorderProjects(
        normalized.map((project) => ({
          id: project.id,
          display_order: project.display_order,
        })),
      );

      showToast({
        type: "success",
        title: "Order updated",
        message: "Project display order was saved.",
      });
    } catch (error) {
      setProjects(previous);

      showToast({
        type: "error",
        title: "Could not reorder projects",
        message: getErrorMessage(error),
      });
    } finally {
      setIsReordering(false);
    }
  }

  return (
    <div className="admin-page projects-page">
      <header className="admin-page-header projects-page__header">
        <div>
          <span className="admin-eyebrow">Portfolio content</span>
          <h1>Projects</h1>
          <p>
            Create, organize, publish, and manage the work displayed across
            your portfolio.
          </p>
        </div>

        <button
          className="admin-primary-action"
          type="button"
          onClick={() => void handleCreate()}
          disabled={isCreating}
        >
          {isCreating ? (
            <LoaderCircle className="projects-spin" size={19} />
          ) : (
            <Plus size={19} />
          )}
          {isCreating ? "Creating..." : "New project"}
        </button>
      </header>

      <section className="projects-summary" aria-label="Project summary">
        <div>
          <span>Total</span>
          <strong>{total}</strong>
          <small>All projects</small>
        </div>
        <div>
          <span>Published</span>
          <strong>{counts.published}</strong>
          <small>Visible in this view</small>
        </div>
        <div>
          <span>Drafts</span>
          <strong>{counts.draft}</strong>
          <small>Visible in this view</small>
        </div>
        <div>
          <span>Featured</span>
          <strong>{counts.featured}</strong>
          <small>Visible in this view</small>
        </div>
      </section>

      <section className="projects-toolbar">
        <label className="projects-search">
          <Search size={19} />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search projects..."
            aria-label="Search projects"
          />
        </label>

        <div className="projects-toolbar__filters">
          <div className="projects-segmented" aria-label="Project status">
            {(["all", "published", "draft"] as ProjectStatusFilter[]).map(
              (filter) => (
                <button
                  key={filter}
                  type="button"
                  className={
                    statusFilter === filter
                      ? "projects-segmented__button projects-segmented__button--active"
                      : "projects-segmented__button"
                  }
                  onClick={() => setStatusFilter(filter)}
                >
                  {filter === "all"
                    ? "All"
                    : filter === "published"
                      ? "Published"
                      : "Drafts"}
                </button>
              ),
            )}
          </div>

          <button
            className={
              featuredOnly
                ? "projects-featured-filter projects-featured-filter--active"
                : "projects-featured-filter"
            }
            type="button"
            onClick={() => setFeaturedOnly((current) => !current)}
          >
            <Sparkles size={17} />
            Featured
          </button>
        </div>
      </section>

      <section className="projects-panel">
        {isLoading ? (
          <div className="projects-state">
            <LoaderCircle className="projects-spin" size={28} />
            <strong>Loading projects</strong>
            <span>Fetching your portfolio projects...</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="projects-state">
            <div className="projects-state__icon">
              <FolderKanban size={28} />
            </div>
            <strong>No projects found</strong>
            <span>
              {debouncedSearch || statusFilter !== "all" || featuredOnly
                ? "Try changing your search or filters."
                : "Create your first project to get started."}
            </span>
          </div>
        ) : (
          <div className="projects-list">
            <AnimatePresence initial={false}>
              {projects.map((project, index) => (
                <motion.article
                  layout
                  key={project.id}
                  className="project-row"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="project-row__order">
                    <button
                      type="button"
                      aria-label={`Move ${project.title} up`}
                      disabled={index === 0 || isReordering}
                      onClick={() => void moveProject(index, -1)}
                    >
                      <ArrowUp size={17} />
                    </button>
                    <span>{index + 1}</span>
                    <button
                      type="button"
                      aria-label={`Move ${project.title} down`}
                      disabled={
                        index === projects.length - 1 || isReordering
                      }
                      onClick={() => void moveProject(index, 1)}
                    >
                      <ArrowDown size={17} />
                    </button>
                  </div>

                  <div className="project-row__cover">
                    {project.cover_thumbnail_url || project.cover_url ? (
                      <img
                        src={
                          project.cover_thumbnail_url ??
                          project.cover_url ??
                          undefined
                        }
                        alt=""
                      />
                    ) : (
                      <ImageOff size={24} />
                    )}
                  </div>

                  <div className="project-row__content">
                    <div className="project-row__title-line">
                      <h2>{project.title}</h2>
                      <span
                        className={
                          project.is_published
                            ? "project-status project-status--published"
                            : "project-status project-status--draft"
                        }
                      >
                        {project.is_published ? "Published" : "Draft"}
                      </span>
                      {project.is_featured && (
                        <span className="project-featured">
                          <Sparkles size={13} />
                          Featured
                        </span>
                      )}
                    </div>

                    <div className="project-row__meta">
                      <span>{project.project_type || "Type not set"}</span>
                      <span>{formatProjectDate(project.project_date)}</span>
                      <span>/{project.slug}</span>
                    </div>

                    <p>
                      {project.short_description ||
                        "No short description has been added yet."}
                    </p>

                    {(project.tags.length > 0 ||
                      project.technologies.length > 0) && (
                      <div className="project-row__chips">
                        {project.tags.slice(0, 3).map((tag) => (
                          <span key={`tag-${tag.id}`}>{tag.label}</span>
                        ))}
                        {project.technologies
                          .slice(0, Math.max(0, 4 - project.tags.length))
                          .map((technology) => (
                            <span key={`technology-${technology}`}>
                              {technology}
                            </span>
                          ))}
                      </div>
                    )}
                  </div>

                  <div className="project-row__actions">
                    {project.show_github_link && project.github_url && (
                      <a
                        href={project.github_url}
                        target="_blank"
                        rel="noreferrer"
                        aria-label={`Open ${project.title} GitHub repository`}
                        title="GitHub"
                      >
                        <GithubIcon size={18} />
                      </a>
                    )}

                    {project.demo_url && (
                      <a
                        href={project.demo_url}
                        target="_blank"
                        rel="noreferrer"
                        aria-label={`Open ${project.title} live demo`}
                        title="Live demo"
                      >
                        <ExternalLink size={18} />
                      </a>
                    )}

                    <button
                      type="button"
                      onClick={() => navigate(`/projects/${project.id}`)}
                      aria-label={`Edit ${project.title}`}
                      title="Edit"
                    >
                      <Pencil size={18} />
                    </button>

                    <button
                      className="project-row__delete"
                      type="button"
                      onClick={() => setDeleteTarget(project)}
                      aria-label={`Delete ${project.title}`}
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </motion.article>
              ))}
            </AnimatePresence>
          </div>
        )}
      </section>

      <AnimatePresence>
        {deleteTarget && (
          <motion.div
            className="projects-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="projects-modal-backdrop"
              type="button"
              aria-label="Close delete confirmation"
              onClick={() => {
                if (!isDeleting) {
                  setDeleteTarget(null);
                }
              }}
            />

            <motion.div
              className="projects-delete-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-project-title"
              initial={{ opacity: 0, y: 18, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.98 }}
              transition={{ duration: 0.2 }}
            >
              <div className="projects-delete-modal__icon">
                <Trash2 size={24} />
              </div>
              <span className="admin-eyebrow">Delete project</span>
              <h2 id="delete-project-title">Delete {deleteTarget.title}?</h2>
              <p>
                This removes the project and its project relationships.
                Media Library assets remain untouched.
              </p>

              <div className="projects-delete-modal__actions">
                <button
                  type="button"
                  onClick={() => setDeleteTarget(null)}
                  disabled={isDeleting}
                >
                  Cancel
                </button>
                <button
                  className="projects-delete-modal__confirm"
                  type="button"
                  onClick={() => void handleDelete()}
                  disabled={isDeleting}
                >
                  {isDeleting ? (
                    <LoaderCircle className="projects-spin" size={18} />
                  ) : (
                    <Trash2 size={18} />
                  )}
                  {isDeleting ? "Deleting..." : "Delete project"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
