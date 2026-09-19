import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronUp,
  CircleDot,
  LoaderCircle,
  MapPin,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useToast } from "../context/toastContext";
import {
  createExperience,
  deleteExperience,
  listExperiences,
  reorderExperiences,
  updateExperience,
} from "../services/experiencesApi";
import type {
  Experience,
  ExperienceStatusFilter,
  ExperienceWritePayload,
} from "../types/experience";

interface HighlightForm {
  key: string;
  text: string;
}

interface ExperienceForm {
  job_title: string;
  company: string;
  location: string;
  start_month: string;
  start_year: string;
  end_month: string;
  end_year: string;
  is_current: boolean;
  is_active: boolean;
  highlights: HighlightForm[];
}

const months = [
  ["01", "January"],
  ["02", "February"],
  ["03", "March"],
  ["04", "April"],
  ["05", "May"],
  ["06", "June"],
  ["07", "July"],
  ["08", "August"],
  ["09", "September"],
  ["10", "October"],
  ["11", "November"],
  ["12", "December"],
] as const;

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 45 }, (_, index) =>
  String(currentYear + 2 - index),
);

let highlightKey = 0;

function makeHighlight(text = ""): HighlightForm {
  highlightKey += 1;
  return {
    key: `highlight-${highlightKey}`,
    text,
  };
}

function createEmptyForm(): ExperienceForm {
  return {
    job_title: "",
    company: "",
    location: "",
    start_month: "",
    start_year: "",
    end_month: "",
    end_year: "",
    is_current: false,
    is_active: true,
    highlights: [makeHighlight()],
  };
}

function splitDate(value: string | null): {
  month: string;
  year: string;
} {
  if (!value) {
    return { month: "", year: "" };
  }

  const [year = "", month = ""] = value.split("-");
  return { month, year };
}

function monthLabel(value: string): string {
  return months.find(([month]) => month === value)?.[1] ?? "";
}

function formatExperienceDate(value: string): string {
  const { month, year } = splitDate(value);
  const label = monthLabel(month);

  if (!label || !year) {
    return value;
  }

  return `${label.slice(0, 3)} ${year}`;
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

export default function ExperiencesPage() {
  const { showToast } = useToast();

  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<ExperienceStatusFilter>("all");

  const [isLoading, setIsLoading] = useState(true);
  const [isReordering, setIsReordering] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);

  const [editorTarget, setEditorTarget] = useState<Experience | "new" | null>(
    null,
  );
  const [form, setForm] = useState<ExperienceForm>(() => createEmptyForm());
  const [isSaving, setIsSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<Experience | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 260);

    return () => window.clearTimeout(timer);
  }, [search]);

  const loadExperiences = useCallback(async () => {
    setIsLoading(true);

    try {
      const result = await listExperiences({
        search: debouncedSearch || undefined,
        isActive:
          statusFilter === "all" ? undefined : statusFilter === "active",
      });

      setExperiences(result.items);
      setTotal(result.total);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load experience",
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
        void loadExperiences();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [loadExperiences]);

  useEffect(() => {
    if (!editorTarget && !deleteTarget) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }

      if (deleteTarget) {
        setDeleteTarget(null);
      } else {
        setEditorTarget(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [deleteTarget, editorTarget]);

  const counts = useMemo(() => {
    const active = experiences.filter(
      (experience) => experience.is_active,
    ).length;

    const current = experiences.filter(
      (experience) => experience.is_current,
    ).length;

    return {
      active,
      inactive: experiences.length - active,
      current,
    };
  }, [experiences]);

  const hasActiveFilters = search.trim().length > 0 || statusFilter !== "all";
  const canReorder = !hasActiveFilters && !isLoading;

  function openCreate() {
    setForm(createEmptyForm());
    setEditorTarget("new");
  }

  function openEdit(experience: Experience) {
    const start = splitDate(experience.start_date);
    const end = splitDate(experience.end_date);

    setForm({
      job_title: experience.job_title,
      company: experience.company,
      location: experience.location ?? "",
      start_month: start.month,
      start_year: start.year,
      end_month: end.month,
      end_year: end.year,
      is_current: experience.is_current,
      is_active: experience.is_active,
      highlights:
        experience.highlights.length > 0
          ? experience.highlights.map((highlight) =>
              makeHighlight(highlight.text),
            )
          : [makeHighlight()],
    });

    setEditorTarget(experience);
  }

  function addHighlight() {
    setForm((current) => ({
      ...current,
      highlights: [...current.highlights, makeHighlight()],
    }));
  }

  function updateHighlight(key: string, text: string) {
    setForm((current) => ({
      ...current,
      highlights: current.highlights.map((highlight) =>
        highlight.key === key ? { ...highlight, text } : highlight,
      ),
    }));
  }

  function removeHighlight(key: string) {
    setForm((current) => {
      const next = current.highlights.filter(
        (highlight) => highlight.key !== key,
      );

      return {
        ...current,
        highlights: next.length > 0 ? next : [makeHighlight()],
      };
    });
  }

  function moveHighlight(index: number, direction: -1 | 1) {
    setForm((current) => {
      const targetIndex = index + direction;

      if (targetIndex < 0 || targetIndex >= current.highlights.length) {
        return current;
      }

      const highlights = [...current.highlights];
      [highlights[index], highlights[targetIndex]] = [
        highlights[targetIndex],
        highlights[index],
      ];

      return {
        ...current,
        highlights,
      };
    });
  }

  async function handleSave() {
    const jobTitle = form.job_title.trim();
    const company = form.company.trim();

    if (!jobTitle || !company) {
      showToast({
        type: "error",
        title: "Required fields missing",
        message: "Add the job title and company.",
      });
      return;
    }

    if (!form.start_month || !form.start_year) {
      showToast({
        type: "error",
        title: "Start date missing",
        message: "Choose both a start month and start year.",
      });
      return;
    }

    if (!form.is_current && (!form.end_month || !form.end_year)) {
      showToast({
        type: "error",
        title: "End date missing",
        message:
          "Choose an end month and year, or mark this as your current role.",
      });
      return;
    }

    const highlights = form.highlights
      .map((highlight) => highlight.text.trim())
      .filter(Boolean);

    if (highlights.length === 0) {
      showToast({
        type: "error",
        title: "Add an experience highlight",
        message:
          "Add at least one bullet describing your work or accomplishments.",
      });
      return;
    }

    const startDate = `${form.start_year}-${form.start_month}-01`;
    const endDate = form.is_current
      ? null
      : `${form.end_year}-${form.end_month}-01`;

    if (endDate && endDate < startDate) {
      showToast({
        type: "error",
        title: "Check the date range",
        message: "The end date cannot be before the start date.",
      });
      return;
    }

    const payload: ExperienceWritePayload = {
      job_title: jobTitle,
      company,
      location: form.location.trim() || null,
      start_date: startDate,
      end_date: endDate,
      is_current: form.is_current,
      is_active: form.is_active,
      highlights: highlights.map((text) => ({ text })),
    };

    setIsSaving(true);

    try {
      if (editorTarget === "new") {
        await createExperience(payload);

        showToast({
          type: "success",
          title: "Experience added",
          message: `${jobTitle} at ${company} was created.`,
        });
      } else if (editorTarget) {
        await updateExperience(editorTarget.id, payload);

        showToast({
          type: "success",
          title: "Experience updated",
          message: `${jobTitle} at ${company} was saved.`,
        });
      }

      setEditorTarget(null);
      await loadExperiences();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not save experience",
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
      await deleteExperience(deleteTarget.id);

      showToast({
        type: "success",
        title: "Experience deleted",
        message: `${deleteTarget.job_title} at ${deleteTarget.company} was removed.`,
      });

      setDeleteTarget(null);
      await loadExperiences();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not delete experience",
        message: getErrorMessage(error),
      });
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleToggle(experience: Experience) {
    if (savingId !== null) {
      return;
    }

    setSavingId(experience.id);

    try {
      await updateExperience(experience.id, {
        job_title: experience.job_title,
        company: experience.company,
        location: experience.location,
        start_date: experience.start_date,
        end_date: experience.end_date,
        is_current: experience.is_current,
        is_active: !experience.is_active,
        highlights: experience.highlights.map((highlight) => ({
          text: highlight.text,
        })),
      });

      showToast({
        type: "success",
        title: experience.is_active ? "Experience hidden" : "Experience active",
        message: experience.is_active
          ? `${experience.job_title} is no longer public.`
          : `${experience.job_title} can now appear publicly.`,
      });

      await loadExperiences();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not update experience",
        message: getErrorMessage(error),
      });
    } finally {
      setSavingId(null);
    }
  }

  async function moveExperience(index: number, direction: -1 | 1) {
    if (!canReorder || isReordering) {
      return;
    }

    const targetIndex = index + direction;

    if (targetIndex < 0 || targetIndex >= experiences.length) {
      return;
    }

    const previous = experiences;
    const next = [...experiences];

    [next[index], next[targetIndex]] = [next[targetIndex], next[index]];

    const normalized = next.map((experience, experienceIndex) => ({
      ...experience,
      display_order: experienceIndex,
    }));

    setExperiences(normalized);
    setIsReordering(true);

    try {
      await reorderExperiences(
        normalized.map((experience) => ({
          id: experience.id,
          display_order: experience.display_order,
        })),
      );

      showToast({
        type: "success",
        title: "Order updated",
        message: "Experience display order was saved.",
      });
    } catch (error) {
      setExperiences(previous);

      showToast({
        type: "error",
        title: "Could not reorder experience",
        message: getErrorMessage(error),
      });
    } finally {
      setIsReordering(false);
    }
  }

  return (
    <div className="admin-page experiences-page">
      <header className="admin-page-header experiences-page__header">
        <div>
          <span className="admin-eyebrow">Resume content</span>
          <h1>Experience</h1>
          <p>
            Build your professional timeline with structured roles, dates, and
            accomplishment-focused highlights.
          </p>
        </div>

        <button
          className="admin-primary-action"
          type="button"
          onClick={openCreate}
        >
          <Plus size={19} />
          Add experience
        </button>
      </header>

      <section className="experiences-summary" aria-label="Experience summary">
        <div>
          <span>Total roles</span>
          <strong>{total}</strong>
          <small>Professional experience</small>
        </div>

        <div>
          <span>Active</span>
          <strong>{counts.active}</strong>
          <small>Visible in this view</small>
        </div>

        <div>
          <span>Inactive</span>
          <strong>{counts.inactive}</strong>
          <small>Hidden in this view</small>
        </div>

        <div>
          <span>Current</span>
          <strong>{counts.current}</strong>
          <small>Marked as present</small>
        </div>
      </section>

      <section className="experiences-toolbar">
        <label className="experiences-search">
          <Search size={19} />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search roles, companies, locations..."
            aria-label="Search experience"
          />
        </label>

        <div className="experiences-segmented" aria-label="Experience status">
          {(["all", "active", "inactive"] as ExperienceStatusFilter[]).map(
            (filter) => (
              <button
                key={filter}
                type="button"
                className={
                  statusFilter === filter
                    ? "experiences-segmented__button experiences-segmented__button--active"
                    : "experiences-segmented__button"
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
        className={`experiences-reorder-note${
          hasActiveFilters ? " experiences-reorder-note--disabled" : ""
        }`}
      >
        {hasActiveFilters
          ? "Clear filters to reorder."
          : "Use the arrows to control the public experience order."}
      </div>

      <section className="experiences-panel">
        {isLoading ? (
          <div className="experiences-state">
            <LoaderCircle className="experiences-spin" size={30} />
            <strong>Loading experience</strong>
            <span>Fetching your professional timeline...</span>
          </div>
        ) : experiences.length === 0 ? (
          <div className="experiences-state">
            <div className="experiences-state__icon">
              <BriefcaseBusiness size={29} />
            </div>
            <strong>No experience found</strong>
            <span>
              {debouncedSearch || statusFilter !== "all"
                ? "Try changing your search or filters."
                : "Add your first professional experience to get started."}
            </span>
          </div>
        ) : (
          <div className="experiences-list">
            <AnimatePresence initial={false}>
              {experiences.map((experience, index) => (
                <motion.article
                  layout
                  key={experience.id}
                  className="experience-row"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="experience-row__order">
                    <button
                      type="button"
                      aria-label={`Move ${experience.job_title} up`}
                      disabled={!canReorder || index === 0 || isReordering}
                      onClick={() => void moveExperience(index, -1)}
                    >
                      <ArrowUp size={17} />
                    </button>

                    <span>{index + 1}</span>

                    <button
                      type="button"
                      aria-label={`Move ${experience.job_title} down`}
                      disabled={
                        !canReorder ||
                        index === experiences.length - 1 ||
                        isReordering
                      }
                      onClick={() => void moveExperience(index, 1)}
                    >
                      <ArrowDown size={17} />
                    </button>
                  </div>

                  <div className="experience-row__timeline">
                    <span />
                  </div>

                  <div className="experience-row__content">
                    <div className="experience-row__topline">
                      <div>
                        <div className="experience-row__title">
                          <h2>{experience.job_title}</h2>

                          <span
                            className={
                              experience.is_active
                                ? "experience-status experience-status--active"
                                : "experience-status experience-status--inactive"
                            }
                          >
                            {experience.is_active ? "Active" : "Inactive"}
                          </span>

                          {experience.is_current ? (
                            <span className="experience-current">Current</span>
                          ) : null}
                        </div>

                        <div className="experience-row__company">
                          <Building2 size={16} />
                          <strong>{experience.company}</strong>
                        </div>
                      </div>

                      <div className="experience-row__date">
                        <CalendarDays size={16} />
                        <span>
                          {formatExperienceDate(experience.start_date)}
                          {" — "}
                          {experience.is_current
                            ? "Present"
                            : experience.end_date
                              ? formatExperienceDate(experience.end_date)
                              : ""}
                        </span>
                      </div>
                    </div>

                    {experience.location ? (
                      <div className="experience-row__location">
                        <MapPin size={15} />
                        <span>{experience.location}</span>
                      </div>
                    ) : null}

                    {experience.highlights.length > 0 ? (
                      <ul className="experience-row__highlights">
                        {experience.highlights.slice(0, 3).map((highlight) => (
                          <li key={highlight.id}>{highlight.text}</li>
                        ))}
                      </ul>
                    ) : null}

                    {experience.highlights.length > 3 ? (
                      <span className="experience-row__more">
                        +{experience.highlights.length - 3} more{" "}
                        {experience.highlights.length - 3 === 1
                          ? "highlight"
                          : "highlights"}
                      </span>
                    ) : null}
                  </div>

                  <div className="experience-row__actions">
                    <button
                      className={
                        experience.is_active
                          ? "experience-visibility experience-visibility--active"
                          : "experience-visibility"
                      }
                      type="button"
                      disabled={savingId !== null}
                      onClick={() => void handleToggle(experience)}
                      title={
                        experience.is_active
                          ? "Deactivate experience"
                          : "Activate experience"
                      }
                    >
                      {savingId === experience.id ? (
                        <LoaderCircle className="experiences-spin" size={17} />
                      ) : (
                        <Check size={17} />
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => openEdit(experience)}
                      aria-label={`Edit ${experience.job_title}`}
                      title="Edit"
                    >
                      <Pencil size={18} />
                    </button>

                    <button
                      className="experience-row__delete"
                      type="button"
                      onClick={() => setDeleteTarget(experience)}
                      aria-label={`Delete ${experience.job_title}`}
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
        {editorTarget ? (
          <motion.div
            className="experiences-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="experiences-modal-backdrop"
              type="button"
              aria-label="Close experience editor"
              onClick={() => setEditorTarget(null)}
            />

            <motion.div
              className="experience-editor"
              role="dialog"
              aria-modal="true"
              aria-labelledby="experience-editor-title"
              initial={{ opacity: 0, y: 18, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.985 }}
              transition={{ duration: 0.2 }}
            >
              <header className="experience-editor__header">
                <div>
                  <span className="admin-eyebrow">
                    {editorTarget === "new"
                      ? "New experience"
                      : "Edit experience"}
                  </span>

                  <h2 id="experience-editor-title">
                    {editorTarget === "new"
                      ? "Add experience"
                      : form.job_title || "Edit experience"}
                  </h2>

                  <p>
                    Add the role, timeline, and concise highlights that best
                    represent your work.
                  </p>
                </div>

                <button
                  className="experience-editor__close"
                  type="button"
                  aria-label="Close"
                  onClick={() => setEditorTarget(null)}
                >
                  <X size={20} />
                </button>
              </header>

              <div className="experience-editor__body">
                <section className="experience-editor__section">
                  <div className="experience-editor__section-heading">
                    <div className="experience-editor__section-icon">
                      <BriefcaseBusiness size={19} />
                    </div>
                    <div>
                      <strong>Role details</strong>
                      <span>
                        The position and organization shown on your resume.
                      </span>
                    </div>
                  </div>

                  <div className="experience-editor__grid">
                    <label className="experience-field">
                      <span>Job title</span>
                      <input
                        value={form.job_title}
                        maxLength={200}
                        placeholder="Software Engineer"
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            job_title: event.target.value,
                          }))
                        }
                      />
                    </label>

                    <label className="experience-field">
                      <span>Company</span>
                      <input
                        value={form.company}
                        maxLength={200}
                        placeholder="Company name"
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            company: event.target.value,
                          }))
                        }
                      />
                    </label>
                  </div>

                  <label className="experience-field">
                    <span>Location</span>
                    <div className="experience-field__with-icon">
                      <MapPin size={17} />
                      <input
                        value={form.location}
                        maxLength={200}
                        placeholder="Sacramento, CA · Remote"
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            location: event.target.value,
                          }))
                        }
                      />
                    </div>
                    <small>
                      Optional. City, region, Remote, or a combination.
                    </small>
                  </label>
                </section>

                <section className="experience-editor__section">
                  <div className="experience-editor__section-heading">
                    <div className="experience-editor__section-icon">
                      <CalendarDays size={19} />
                    </div>
                    <div>
                      <strong>Timeline</strong>
                      <span>
                        Month and year are enough for a clean resume timeline.
                      </span>
                    </div>
                  </div>

                  <div className="experience-date-block">
                    <div className="experience-date-block__label">
                      <span>Start date</span>
                    </div>

                    <div className="experience-date-selects">
                      <label>
                        <span>Month</span>
                        <div className="experience-select">
                          <select
                            value={form.start_month}
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                start_month: event.target.value,
                              }))
                            }
                          >
                            <option value="">Select month</option>
                            {months.map(([value, label]) => (
                              <option key={value} value={value}>
                                {label}
                              </option>
                            ))}
                          </select>
                          <ChevronDown size={17} />
                        </div>
                      </label>

                      <label>
                        <span>Year</span>
                        <div className="experience-select">
                          <select
                            value={form.start_year}
                            onChange={(event) =>
                              setForm((current) => ({
                                ...current,
                                start_year: event.target.value,
                              }))
                            }
                          >
                            <option value="">Select year</option>
                            {years.map((year) => (
                              <option key={year} value={year}>
                                {year}
                              </option>
                            ))}
                          </select>
                          <ChevronDown size={17} />
                        </div>
                      </label>
                    </div>
                  </div>

                  <label className="experience-editor__current">
                    <div>
                      <strong>I currently work here</strong>
                      <span>
                        The public timeline will display “Present” instead of an
                        end date.
                      </span>
                    </div>

                    <input
                      type="checkbox"
                      checked={form.is_current}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          is_current: event.target.checked,
                          end_month: event.target.checked
                            ? ""
                            : current.end_month,
                          end_year: event.target.checked
                            ? ""
                            : current.end_year,
                        }))
                      }
                    />

                    <span className="experience-editor__switch" />
                  </label>

                  <AnimatePresence initial={false}>
                    {!form.is_current ? (
                      <motion.div
                        className="experience-date-block"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.18 }}
                      >
                        <div className="experience-date-block__label">
                          <span>End date</span>
                        </div>

                        <div className="experience-date-selects">
                          <label>
                            <span>Month</span>
                            <div className="experience-select">
                              <select
                                value={form.end_month}
                                onChange={(event) =>
                                  setForm((current) => ({
                                    ...current,
                                    end_month: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Select month</option>
                                {months.map(([value, label]) => (
                                  <option key={value} value={value}>
                                    {label}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown size={17} />
                            </div>
                          </label>

                          <label>
                            <span>Year</span>
                            <div className="experience-select">
                              <select
                                value={form.end_year}
                                onChange={(event) =>
                                  setForm((current) => ({
                                    ...current,
                                    end_year: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Select year</option>
                                {years.map((year) => (
                                  <option key={year} value={year}>
                                    {year}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown size={17} />
                            </div>
                          </label>
                        </div>
                      </motion.div>
                    ) : null}
                  </AnimatePresence>
                </section>

                <section className="experience-editor__section">
                  <div className="experience-editor__section-heading experience-editor__section-heading--action">
                    <div className="experience-editor__section-heading-main">
                      <div className="experience-editor__section-icon">
                        <CircleDot size={19} />
                      </div>
                      <div>
                        <strong>Highlights</strong>
                        <span>
                          Keep each point concise and accomplishment-focused.
                        </span>
                      </div>
                    </div>

                    <button
                      className="experience-add-highlight"
                      type="button"
                      onClick={addHighlight}
                    >
                      <Plus size={17} />
                      Add highlight
                    </button>
                  </div>

                  <div className="experience-highlights-editor">
                    <AnimatePresence initial={false}>
                      {form.highlights.map((highlight, index) => (
                        <motion.div
                          layout
                          key={highlight.key}
                          className="experience-highlight-field"
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.98 }}
                        >
                          <div className="experience-highlight-field__number">
                            {index + 1}
                          </div>

                          <textarea
                            value={highlight.text}
                            rows={3}
                            maxLength={1000}
                            placeholder="Built, improved, led, designed, optimized..."
                            onChange={(event) =>
                              updateHighlight(highlight.key, event.target.value)
                            }
                          />

                          <div className="experience-highlight-field__actions">
                            <button
                              type="button"
                              disabled={index === 0}
                              aria-label="Move highlight up"
                              onClick={() => moveHighlight(index, -1)}
                            >
                              <ChevronUp size={17} />
                            </button>

                            <button
                              type="button"
                              disabled={index === form.highlights.length - 1}
                              aria-label="Move highlight down"
                              onClick={() => moveHighlight(index, 1)}
                            >
                              <ChevronDown size={17} />
                            </button>

                            <button
                              className="experience-highlight-field__delete"
                              type="button"
                              aria-label="Delete highlight"
                              onClick={() => removeHighlight(highlight.key)}
                            >
                              <Trash2 size={17} />
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </section>

                <label className="experience-editor__active">
                  <div>
                    <strong>Active experience</strong>
                    <span>
                      Active roles are eligible to appear on your public
                      portfolio.
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

                  <span className="experience-editor__switch" />
                </label>
              </div>

              <footer className="experience-editor__footer">
                <button
                  className="experience-secondary-button"
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
                    <LoaderCircle className="experiences-spin" size={18} />
                  ) : (
                    <Check size={18} />
                  )}

                  {isSaving ? "Saving..." : "Save experience"}
                </button>
              </footer>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {deleteTarget ? (
          <motion.div
            className="experiences-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="experiences-modal-backdrop"
              type="button"
              aria-label="Close delete confirmation"
              onClick={() => setDeleteTarget(null)}
            />

            <motion.div
              className="experience-delete-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="experience-delete-title"
              initial={{ opacity: 0, y: 14, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.985 }}
            >
              <div className="experience-delete-modal__icon">
                <Trash2 size={22} />
              </div>

              <span className="admin-eyebrow">Delete experience</span>

              <h2 id="experience-delete-title">
                Remove {deleteTarget.job_title}?
              </h2>

              <p>
                This permanently removes the role at{" "}
                <strong>{deleteTarget.company}</strong> and all of its
                highlights from your portfolio database.
              </p>

              <div className="experience-delete-modal__actions">
                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={() => setDeleteTarget(null)}
                >
                  Cancel
                </button>

                <button
                  className="experience-delete-modal__confirm"
                  type="button"
                  disabled={isDeleting}
                  onClick={() => void handleDelete()}
                >
                  {isDeleting ? (
                    <LoaderCircle className="experiences-spin" size={17} />
                  ) : (
                    <Trash2 size={17} />
                  )}

                  {isDeleting ? "Deleting..." : "Delete experience"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
