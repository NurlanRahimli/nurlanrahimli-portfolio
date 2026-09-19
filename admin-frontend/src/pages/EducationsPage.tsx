import { AxiosError } from "axios";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  CalendarDays,
  Check,
  ChevronDown,
  FileCheck2,
  FileText,
  GraduationCap,
  LoaderCircle,
  MapPin,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ContentMediaPicker } from "../components/content/ContentMediaPicker";
import { useToast } from "../context/toastContext";
import {
  createEducation,
  deleteEducation,
  listEducations,
  reorderEducations,
  updateEducation,
} from "../services/educationsApi";
import type {
  Education,
  EducationStatusFilter,
  EducationWritePayload,
} from "../types/education";
import type { MediaAsset } from "../types/media";

interface EducationForm {
  title: string;
  location: string;
  startMonth: string;
  startYear: string;
  endMonth: string;
  endYear: string;
  isCurrent: boolean;
  description: string;
  certification_media_asset_id: number | null;
  certification_filename: string | null;
  certification_url: string | null;
  is_active: boolean;
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
const years = Array.from({ length: 55 }, (_, index) =>
  String(currentYear + 2 - index),
);

function createEmptyForm(): EducationForm {
  return {
    title: "",
    location: "",
    startMonth: "",
    startYear: "",
    endMonth: "",
    endYear: "",
    isCurrent: false,
    description: "",
    certification_media_asset_id: null,
    certification_filename: null,
    certification_url: null,
    is_active: true,
  };
}

function splitDate(value: string): { month: string; year: string } {
  const [year = "", month = ""] = value.split("-");
  return { month, year };
}

function formatEducationDate(value: string): string {
  const { month, year } = splitDate(value);
  const label = months.find(([item]) => item === month)?.[1];

  return label && year ? `${label.slice(0, 3)} ${year}` : value;
}

function formatEducationRange(education: Education): string {
  const start = formatEducationDate(education.start_date);
  const end = education.is_current
    ? "Present"
    : education.end_date
      ? formatEducationDate(education.end_date)
      : "";

  return end ? `${start} — ${end}` : start;
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

export default function EducationsPage() {
  const { showToast } = useToast();

  const [educations, setEducations] = useState<Education[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<EducationStatusFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isReordering, setIsReordering] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [editorTarget, setEditorTarget] = useState<Education | "new" | null>(
    null,
  );
  const [form, setForm] = useState<EducationForm>(() => createEmptyForm());
  const [isSaving, setIsSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Education | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [mediaPickerOpen, setMediaPickerOpen] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 260);

    return () => window.clearTimeout(timer);
  }, [search]);

  const loadEducations = useCallback(async () => {
    setIsLoading(true);

    try {
      const result = await listEducations({
        search: debouncedSearch || undefined,
        isActive:
          statusFilter === "all" ? undefined : statusFilter === "active",
      });

      setEducations(result.items);
      setTotal(result.total);
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load education",
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
        void loadEducations();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [loadEducations]);

  useEffect(() => {
    if (!editorTarget && !deleteTarget) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || mediaPickerOpen) {
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
  }, [deleteTarget, editorTarget, mediaPickerOpen]);

  const counts = useMemo(() => {
    const active = educations.filter((item) => item.is_active).length;
    const certificates = educations.filter(
      (item) => item.certification_media_asset_id !== null,
    ).length;

    return {
      active,
      inactive: educations.length - active,
      certificates,
    };
  }, [educations]);

  const hasActiveFilters = search.trim().length > 0 || statusFilter !== "all";
  const canReorder = !hasActiveFilters && !isLoading;

  function openCreate() {
    setForm(createEmptyForm());
    setEditorTarget("new");
  }

  function openEdit(education: Education) {
    const startDate = splitDate(education.start_date);
    const endDate = education.end_date
      ? splitDate(education.end_date)
      : { month: "", year: "" };

    setForm({
      title: education.title,
      location: education.location,
      startMonth: startDate.month,
      startYear: startDate.year,
      endMonth: endDate.month,
      endYear: endDate.year,
      isCurrent: education.is_current,
      description: education.description ?? "",
      certification_media_asset_id: education.certification_media_asset_id,
      certification_filename: education.certification_filename,
      certification_url: education.certification_url,
      is_active: education.is_active,
    });

    setEditorTarget(education);
  }

  function handleCertificateSelect(asset: MediaAsset) {
    setForm((current) => ({
      ...current,
      certification_media_asset_id: asset.id,
      certification_filename: asset.original_filename,
      certification_url: asset.url,
    }));
  }

  async function handleSave() {
    const title = form.title.trim();
    const location = form.location.trim();

    if (!title || !location) {
      showToast({
        type: "error",
        title: "Required fields missing",
        message: "Add the education title and location.",
      });
      return;
    }

    if (!form.startMonth || !form.startYear) {
      showToast({
        type: "error",
        title: "Start date missing",
        message: "Choose both a start month and start year.",
      });
      return;
    }

    if (!form.isCurrent && (!form.endMonth || !form.endYear)) {
      showToast({
        type: "error",
        title: "End date missing",
        message:
          "Choose both an end month and end year, or mark this education as current.",
      });
      return;
    }

    const startDate = `${form.startYear}-${form.startMonth}-01`;
    const endDate = form.isCurrent
      ? null
      : `${form.endYear}-${form.endMonth}-01`;

    if (endDate && endDate < startDate) {
      showToast({
        type: "error",
        title: "Invalid date range",
        message: "End date cannot be before the start date.",
      });
      return;
    }

    const payload: EducationWritePayload = {
      title,
      location,
      start_date: startDate,
      end_date: endDate,
      is_current: form.isCurrent,
      description: form.description.trim() || null,
      certification_media_asset_id: form.certification_media_asset_id,
      is_active: form.is_active,
    };

    setIsSaving(true);

    try {
      if (editorTarget === "new") {
        await createEducation(payload);

        showToast({
          type: "success",
          title: "Education added",
          message: `${title} was added to your education timeline.`,
        });
      } else if (editorTarget) {
        await updateEducation(editorTarget.id, payload);

        showToast({
          type: "success",
          title: "Education updated",
          message: `${title} was saved.`,
        });
      }

      setEditorTarget(null);
      await loadEducations();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not save education",
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
      await deleteEducation(deleteTarget.id);

      showToast({
        type: "success",
        title: "Education deleted",
        message: `${deleteTarget.title} was removed.`,
      });

      setDeleteTarget(null);
      await loadEducations();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not delete education",
        message: getErrorMessage(error),
      });
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleToggle(education: Education) {
    if (savingId !== null) {
      return;
    }

    setSavingId(education.id);

    try {
      await updateEducation(education.id, {
        title: education.title,
        location: education.location,
        start_date: education.start_date,
        end_date: education.end_date,
        is_current: education.is_current,
        description: education.description,
        certification_media_asset_id: education.certification_media_asset_id,
        is_active: !education.is_active,
      });

      showToast({
        type: "success",
        title: education.is_active ? "Education hidden" : "Education active",
        message: education.is_active
          ? `${education.title} is no longer public.`
          : `${education.title} can now appear publicly.`,
      });

      await loadEducations();
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not update education",
        message: getErrorMessage(error),
      });
    } finally {
      setSavingId(null);
    }
  }

  async function moveEducation(index: number, direction: -1 | 1) {
    if (!canReorder || isReordering) {
      return;
    }

    const targetIndex = index + direction;

    if (targetIndex < 0 || targetIndex >= educations.length) {
      return;
    }

    const previous = educations;
    const next = [...educations];

    [next[index], next[targetIndex]] = [next[targetIndex], next[index]];

    const normalized = next.map((education, educationIndex) => ({
      ...education,
      display_order: educationIndex,
    }));

    setEducations(normalized);
    setIsReordering(true);

    try {
      await reorderEducations(
        normalized.map((education) => ({
          id: education.id,
          display_order: education.display_order,
        })),
      );

      showToast({
        type: "success",
        title: "Order updated",
        message: "Education display order was saved.",
      });
    } catch (error) {
      setEducations(previous);

      showToast({
        type: "error",
        title: "Could not reorder education",
        message: getErrorMessage(error),
      });
    } finally {
      setIsReordering(false);
    }
  }

  return (
    <div className="admin-page educations-page">
      <header className="admin-page-header educations-page__header">
        <div>
          <span className="admin-eyebrow">Resume content</span>
          <h1>Education</h1>
          <p>
            Manage your academic background, credentials, and supporting
            certificate documents.
          </p>
        </div>

        <button
          className="admin-primary-action"
          type="button"
          onClick={openCreate}
        >
          <Plus size={19} />
          Add education
        </button>
      </header>

      <section className="educations-summary" aria-label="Education summary">
        <div>
          <span>Total entries</span>
          <strong>{total}</strong>
          <small>Education history</small>
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
          <span>Certificates</span>
          <strong>{counts.certificates}</strong>
          <small>Attached in this view</small>
        </div>
      </section>

      <section className="educations-toolbar">
        <label className="educations-search">
          <Search size={19} />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search education, locations, descriptions..."
            aria-label="Search education"
          />
        </label>

        <div className="educations-segmented" aria-label="Education status">
          {(["all", "active", "inactive"] as EducationStatusFilter[]).map(
            (filter) => (
              <button
                key={filter}
                type="button"
                className={
                  statusFilter === filter
                    ? "educations-segmented__button educations-segmented__button--active"
                    : "educations-segmented__button"
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
        className={`educations-reorder-note${
          hasActiveFilters ? " educations-reorder-note--disabled" : ""
        }`}
      >
        {hasActiveFilters
          ? "Clear filters to reorder."
          : "Use the arrows to control the public education order."}
      </div>

      <section className="educations-panel">
        {isLoading ? (
          <div className="educations-state">
            <LoaderCircle className="educations-spin" size={30} />
            <strong>Loading education</strong>
            <span>Fetching your academic timeline...</span>
          </div>
        ) : educations.length === 0 ? (
          <div className="educations-state">
            <div className="educations-state__icon">
              <GraduationCap size={29} />
            </div>
            <strong>No education found</strong>
            <span>
              {debouncedSearch || statusFilter !== "all"
                ? "Try changing your search or filters."
                : "Add your first education entry to get started."}
            </span>
          </div>
        ) : (
          <div className="educations-list">
            <AnimatePresence initial={false}>
              {educations.map((education, index) => (
                <motion.article
                  layout
                  key={education.id}
                  className="education-row"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="education-row__order">
                    <button
                      type="button"
                      aria-label={`Move ${education.title} up`}
                      disabled={!canReorder || index === 0 || isReordering}
                      onClick={() => void moveEducation(index, -1)}
                    >
                      <ArrowUp size={17} />
                    </button>

                    <span>{index + 1}</span>

                    <button
                      type="button"
                      aria-label={`Move ${education.title} down`}
                      disabled={
                        !canReorder ||
                        index === educations.length - 1 ||
                        isReordering
                      }
                      onClick={() => void moveEducation(index, 1)}
                    >
                      <ArrowDown size={17} />
                    </button>
                  </div>

                  <div className="education-row__timeline">
                    <span />
                  </div>

                  <div className="education-row__content">
                    <div className="education-row__topline">
                      <div>
                        <div className="education-row__title">
                          <h2>{education.title}</h2>
                          <span
                            className={
                              education.is_active
                                ? "education-status education-status--active"
                                : "education-status education-status--inactive"
                            }
                          >
                            {education.is_active ? "Active" : "Inactive"}
                          </span>
                        </div>

                        <div className="education-row__location">
                          <MapPin size={16} />
                          <strong>{education.location}</strong>
                        </div>
                      </div>

                      <div className="education-row__date">
                        <CalendarDays size={16} />
                        <span>{formatEducationRange(education)}</span>
                      </div>
                    </div>

                    {education.description ? (
                      <p className="education-row__description">
                        {education.description}
                      </p>
                    ) : null}

                    {education.certification_media_asset_id ? (
                      <div className="education-row__certificate">
                        <FileCheck2 size={16} />
                        <span>
                          {education.certification_filename ||
                            "Certificate PDF"}
                        </span>

                        {education.certification_url ? (
                          <a
                            href={education.certification_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Preview
                          </a>
                        ) : null}
                      </div>
                    ) : null}
                  </div>

                  <div className="education-row__actions">
                    <button
                      className={
                        education.is_active
                          ? "education-visibility education-visibility--active"
                          : "education-visibility"
                      }
                      type="button"
                      disabled={savingId !== null}
                      onClick={() => void handleToggle(education)}
                      title={
                        education.is_active
                          ? "Deactivate education"
                          : "Activate education"
                      }
                    >
                      {savingId === education.id ? (
                        <LoaderCircle className="educations-spin" size={17} />
                      ) : (
                        <Check size={17} />
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => openEdit(education)}
                      aria-label={`Edit ${education.title}`}
                      title="Edit"
                    >
                      <Pencil size={18} />
                    </button>

                    <button
                      className="education-row__delete"
                      type="button"
                      onClick={() => setDeleteTarget(education)}
                      aria-label={`Delete ${education.title}`}
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
            className="educations-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="educations-modal-backdrop"
              type="button"
              aria-label="Close education editor"
              onClick={() => setEditorTarget(null)}
            />

            <motion.div
              className="education-editor"
              role="dialog"
              aria-modal="true"
              aria-labelledby="education-editor-title"
              initial={{ opacity: 0, y: 18, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.985 }}
              transition={{ duration: 0.2 }}
            >
              <header className="education-editor__header">
                <div>
                  <span className="admin-eyebrow">
                    {editorTarget === "new"
                      ? "New education"
                      : "Edit education"}
                  </span>
                  <h2 id="education-editor-title">
                    {editorTarget === "new"
                      ? "Add education"
                      : form.title || "Edit education"}
                  </h2>
                  <p>
                    Add your academic background and optionally attach a
                    supporting certificate.
                  </p>
                </div>

                <button
                  className="education-editor__close"
                  type="button"
                  aria-label="Close"
                  onClick={() => setEditorTarget(null)}
                >
                  <X size={20} />
                </button>
              </header>

              <div className="education-editor__body">
                <section className="education-editor__section">
                  <div className="education-editor__section-heading">
                    <div className="education-editor__section-icon">
                      <GraduationCap size={19} />
                    </div>
                    <div>
                      <strong>Education details</strong>
                      <span>
                        The qualification and location shown on your resume.
                      </span>
                    </div>
                  </div>

                  <label className="education-field">
                    <span>Title</span>
                    <input
                      value={form.title}
                      maxLength={250}
                      placeholder="Bachelor of Science in Computer Science"
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          title: event.target.value,
                        }))
                      }
                    />
                  </label>

                  <label className="education-field">
                    <span>Location</span>
                    <div className="education-field__with-icon">
                      <MapPin size={17} />
                      <input
                        value={form.location}
                        maxLength={200}
                        placeholder="Sacramento, CA"
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            location: event.target.value,
                          }))
                        }
                      />
                    </div>
                  </label>
                </section>

                <section className="education-editor__section">
                  <div className="education-editor__section-heading">
                    <div className="education-editor__section-icon">
                      <CalendarDays size={19} />
                    </div>
                    <div>
                      <strong>Education period</strong>
                      <span>
                        Add the start and end dates for this education entry.
                      </span>
                    </div>
                  </div>

                  <div className="education-period">
                    <div className="education-period__group">
                      <div className="education-period__label">
                        <span>Start Date</span>
                        <small>Required</small>
                      </div>

                      <div className="education-date-selects">
                        <label>
                          <span>Month</span>
                          <div className="education-select">
                            <select
                              value={form.startMonth}
                              onChange={(event) =>
                                setForm((current) => ({
                                  ...current,
                                  startMonth: event.target.value,
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
                          <div className="education-select">
                            <select
                              value={form.startYear}
                              onChange={(event) =>
                                setForm((current) => ({
                                  ...current,
                                  startYear: event.target.value,
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

                    <div
                      className={`education-period__group${
                        form.isCurrent
                          ? " education-period__group--disabled"
                          : ""
                      }`}
                    >
                      <div className="education-period__label">
                        <span>End Date</span>
                        <small>{form.isCurrent ? "Present" : "Required"}</small>
                      </div>

                      <div className="education-date-selects">
                        <label>
                          <span>Month</span>
                          <div className="education-select">
                            <select
                              value={form.endMonth}
                              disabled={form.isCurrent}
                              onChange={(event) =>
                                setForm((current) => ({
                                  ...current,
                                  endMonth: event.target.value,
                                }))
                              }
                            >
                              <option value="">
                                {form.isCurrent ? "Present" : "Select month"}
                              </option>
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
                          <div className="education-select">
                            <select
                              value={form.endYear}
                              disabled={form.isCurrent}
                              onChange={(event) =>
                                setForm((current) => ({
                                  ...current,
                                  endYear: event.target.value,
                                }))
                              }
                            >
                              <option value="">
                                {form.isCurrent ? "Present" : "Select year"}
                              </option>
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
                  </div>

                  <label className="education-current-toggle">
                    <div>
                      <strong>Currently studying here</strong>
                      <span>
                        Use Present as the end date for this education.
                      </span>
                    </div>

                    <input
                      type="checkbox"
                      checked={form.isCurrent}
                      onChange={(event) => {
                        const checked = event.target.checked;

                        setForm((current) => ({
                          ...current,
                          isCurrent: checked,
                          endMonth: checked ? "" : current.endMonth,
                          endYear: checked ? "" : current.endYear,
                        }));
                      }}
                    />

                    <span className="education-current-toggle__switch" />
                  </label>
                </section>

                <section className="education-editor__section">
                  <div className="education-editor__section-heading">
                    <div className="education-editor__section-icon">
                      <FileText size={19} />
                    </div>
                    <div>
                      <strong>Description</strong>
                      <span>
                        Optional context about the program, studies, or
                        achievement.
                      </span>
                    </div>
                  </div>

                  <label className="education-field">
                    <span>Description</span>
                    <textarea
                      value={form.description}
                      rows={5}
                      maxLength={5000}
                      placeholder="Add a concise description..."
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          description: event.target.value,
                        }))
                      }
                    />
                    <small>
                      {form.description.length.toLocaleString()} / 5,000
                    </small>
                  </label>
                </section>

                <section className="education-editor__section">
                  <div className="education-editor__section-heading">
                    <div className="education-editor__section-icon">
                      <FileCheck2 size={19} />
                    </div>
                    <div>
                      <strong>Certification</strong>
                      <span>
                        Optional PDF stored safely in your Media Library.
                      </span>
                    </div>
                  </div>

                  {form.certification_media_asset_id ? (
                    <div className="education-certificate-selected">
                      <div className="education-certificate-selected__icon">
                        <FileCheck2 size={22} />
                      </div>

                      <div>
                        <strong>
                          {form.certification_filename || "Certificate PDF"}
                        </strong>
                        <span>Selected from Media Library</span>
                      </div>

                      {form.certification_url ? (
                        <a
                          href={form.certification_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Preview
                        </a>
                      ) : null}
                    </div>
                  ) : (
                    <div className="education-certificate-empty">
                      <FileText size={27} />
                      <strong>No certificate selected</strong>
                      <span>
                        Choose or upload a PDF from your Media Library.
                      </span>
                    </div>
                  )}

                  <div className="education-certificate-actions">
                    <button
                      className="education-secondary-button"
                      type="button"
                      onClick={() => setMediaPickerOpen(true)}
                    >
                      <FileText size={17} />
                      {form.certification_media_asset_id
                        ? "Replace certificate"
                        : "Choose certificate"}
                    </button>

                    {form.certification_media_asset_id ? (
                      <button
                        className="education-text-button education-text-button--danger"
                        type="button"
                        onClick={() =>
                          setForm((current) => ({
                            ...current,
                            certification_media_asset_id: null,
                            certification_filename: null,
                            certification_url: null,
                          }))
                        }
                      >
                        Remove
                      </button>
                    ) : null}
                  </div>
                </section>

                <label className="education-editor__active">
                  <div>
                    <strong>Active education</strong>
                    <span>
                      Active entries are eligible to appear on your public
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
                  <span className="education-editor__switch" />
                </label>
              </div>

              <footer className="education-editor__footer">
                <button
                  className="education-secondary-button"
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
                    <LoaderCircle className="educations-spin" size={18} />
                  ) : (
                    <Check size={18} />
                  )}
                  {isSaving ? "Saving..." : "Save education"}
                </button>
              </footer>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {deleteTarget ? (
          <motion.div
            className="educations-modal-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="educations-modal-backdrop"
              type="button"
              aria-label="Close delete confirmation"
              onClick={() => setDeleteTarget(null)}
            />

            <motion.div
              className="education-delete-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="education-delete-title"
              initial={{ opacity: 0, y: 14, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.985 }}
            >
              <div className="education-delete-modal__icon">
                <Trash2 size={22} />
              </div>

              <span className="admin-eyebrow">Delete education</span>
              <h2 id="education-delete-title">Remove {deleteTarget.title}?</h2>

              <p>
                This permanently removes the education entry from your portfolio
                database. Its certificate file will remain safely stored in
                Media Library.
              </p>

              <div className="education-delete-modal__actions">
                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={() => setDeleteTarget(null)}
                >
                  Cancel
                </button>

                <button
                  className="education-delete-modal__confirm"
                  type="button"
                  disabled={isDeleting}
                  onClick={() => void handleDelete()}
                >
                  {isDeleting ? (
                    <LoaderCircle className="educations-spin" size={17} />
                  ) : (
                    <Trash2 size={17} />
                  )}
                  {isDeleting ? "Deleting..." : "Delete education"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <ContentMediaPicker
        isOpen={mediaPickerOpen}
        mode="education"
        selectedId={form.certification_media_asset_id}
        onClose={() => setMediaPickerOpen(false)}
        onSelect={handleCertificateSelect}
      />
    </div>
  );
}
