import { AxiosError } from "axios";
import { motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  Check,
  GripVertical,
  LoaderCircle,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useToast } from "../../context/toastContext";
import {
  createService,
  deleteService,
  getServices,
  reorderServices,
  updateService,
} from "../../services/servicesApi";
import type {
  Service,
  ServiceIconName,
  ServicePayload,
} from "../../types/service";
import { getServiceIcon, SERVICE_ICON_OPTIONS } from "./serviceIcons";

type StatusFilter = "all" | "active" | "inactive";

interface ServiceFormState {
  icon: ServiceIconName;
  title: string;
  description: string;
  is_active: boolean;
}

const EMPTY_FORM: ServiceFormState = {
  icon: "Code2",
  title: "",
  description: "",
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

function toPayload(form: ServiceFormState): ServicePayload {
  return {
    icon: form.icon,
    title: form.title.trim(),
    description: form.description.trim(),
    is_active: form.is_active,
  };
}

function toForm(service: Service): ServiceFormState {
  return {
    icon: service.icon,
    title: service.title,
    description: service.description,
    is_active: service.is_active,
  };
}

export function ServicesContentPanel() {
  const { showToast } = useToast();

  const [services, setServices] = useState<Service[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [form, setForm] = useState<ServiceFormState>(EMPTY_FORM);
  const [isSaving, setIsSaving] = useState(false);

  const [serviceToDelete, setServiceToDelete] = useState<Service | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [reorderingId, setReorderingId] = useState<number | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 250);

    return () => window.clearTimeout(timer);
  }, [search]);

  const reorderEnabled = debouncedSearch.length === 0 && statusFilter === "all";

  const loadServices = useCallback(async () => {
    setIsLoading(true);

    try {
      const response = await getServices({
        search: debouncedSearch || undefined,
        is_active:
          statusFilter === "all" ? undefined : statusFilter === "active",
        limit: 100,
        offset: 0,
      });

      setServices(response.items);
      setTotal(response.total);
    } catch (error) {
      showToast({
        type: "error",
        title: "Couldn't load services",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, showToast, statusFilter]);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  useEffect(() => {
    if (!editorOpen && !serviceToDelete) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }

      if (serviceToDelete && !isDeleting) {
        setServiceToDelete(null);
        return;
      }

      if (editorOpen && !isSaving) {
        setEditorOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editorOpen, isDeleting, isSaving, serviceToDelete]);

  const activeCount = useMemo(
    () => services.filter((service) => service.is_active).length,
    [services],
  );

  const openCreate = () => {
    setEditingService(null);
    setForm({ ...EMPTY_FORM });
    setEditorOpen(true);
  };

  const openEdit = (service: Service) => {
    setEditingService(service);
    setForm(toForm(service));
    setEditorOpen(true);
  };

  const closeEditor = () => {
    if (isSaving) {
      return;
    }

    setEditorOpen(false);
  };

  const handleSave = async () => {
    const payload = toPayload(form);

    if (!payload.title) {
      showToast({
        type: "error",
        title: "Title required",
        message: "Give this service a title before saving.",
      });
      return;
    }

    if (!payload.description) {
      showToast({
        type: "error",
        title: "Description required",
        message: "Add a short description of what you provide.",
      });
      return;
    }

    setIsSaving(true);

    try {
      if (editingService) {
        await updateService(editingService.id, payload);

        showToast({
          type: "success",
          title: "Service updated",
          message: `${payload.title} was saved successfully.`,
        });
      } else {
        await createService(payload);

        showToast({
          type: "success",
          title: "Service created",
          message: `${payload.title} was added to your portfolio.`,
        });
      }

      setEditorOpen(false);
      await loadServices();
    } catch (error) {
      showToast({
        type: "error",
        title: editingService
          ? "Couldn't update service"
          : "Couldn't create service",
        message: getErrorMessage(error),
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleActive = async (service: Service) => {
    try {
      await updateService(service.id, {
        icon: service.icon,
        title: service.title,
        description: service.description,
        is_active: !service.is_active,
      });

      showToast({
        type: "success",
        title: service.is_active ? "Service hidden" : "Service published",
        message: service.is_active
          ? `${service.title} is no longer public.`
          : `${service.title} is now visible publicly.`,
      });

      await loadServices();
    } catch (error) {
      showToast({
        type: "error",
        title: "Couldn't update service",
        message: getErrorMessage(error),
      });
    }
  };

  const handleDelete = async () => {
    if (!serviceToDelete) {
      return;
    }

    setIsDeleting(true);

    try {
      await deleteService(serviceToDelete.id);

      showToast({
        type: "success",
        title: "Service deleted",
        message: `${serviceToDelete.title} was removed.`,
      });

      setServiceToDelete(null);
      await loadServices();
    } catch (error) {
      showToast({
        type: "error",
        title: "Couldn't delete service",
        message: getErrorMessage(error),
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const moveService = async (service: Service, direction: -1 | 1) => {
    if (!reorderEnabled || reorderingId !== null) {
      return;
    }

    const currentIndex = services.findIndex((item) => item.id === service.id);
    const targetIndex = currentIndex + direction;

    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= services.length) {
      return;
    }

    const next = [...services];
    const [moved] = next.splice(currentIndex, 1);
    next.splice(targetIndex, 0, moved);

    const previous = services;
    setServices(next);
    setReorderingId(service.id);

    try {
      await reorderServices(
        next.map((item, index) => ({
          id: item.id,
          display_order: index,
        })),
      );

      showToast({
        type: "success",
        title: "Order updated",
        message: `${service.title} was moved ${direction < 0 ? "up" : "down"}.`,
      });

      await loadServices();
    } catch (error) {
      setServices(previous);

      showToast({
        type: "error",
        title: "Couldn't reorder services",
        message: getErrorMessage(error),
      });
    } finally {
      setReorderingId(null);
    }
  };

  return (
    <>
      <motion.div
        className="services-content"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <section className="services-overview">
          <div className="services-overview__copy">
            <span className="services-overview__eyebrow">
              <Sparkles size={16} />
              Portfolio services
            </span>

            <h2>What you offer</h2>

            <p>
              Manage the services shown on your portfolio. Choose a clear visual
              icon, write concise copy, and control the order visitors see them
              in.
            </p>
          </div>

          <div className="services-overview__actions">
            <div className="services-overview__stat">
              <strong>{total}</strong>
              <span>{total === 1 ? "Service" : "Services"}</span>
            </div>

            <div className="services-overview__stat">
              <strong>{activeCount}</strong>
              <span>Visible here</span>
            </div>

            <button
              type="button"
              className="admin-primary-action"
              onClick={openCreate}
            >
              <Plus size={18} />
              Add service
            </button>
          </div>
        </section>

        <section className="services-manager">
          <header className="services-manager__toolbar">
            <div className="services-search">
              <Search size={18} />
              <input
                type="search"
                value={search}
                placeholder="Search services..."
                aria-label="Search services"
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

            <div
              className="services-status-filter"
              aria-label="Filter services"
            >
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
                      ? "services-status-filter__button services-status-filter__button--active"
                      : "services-status-filter__button"
                  }
                  onClick={() => setStatusFilter(value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </header>

          {!reorderEnabled ? (
            <div className="services-reorder-note">
              <GripVertical size={17} />
              Clear search and filters to change the public display order.
            </div>
          ) : null}

          {isLoading ? (
            <div className="services-state">
              <LoaderCircle className="website-content-spin" size={30} />
              <strong>Loading services</strong>
              <span>Fetching your current portfolio services...</span>
            </div>
          ) : services.length === 0 ? (
            <div className="services-state services-state--empty">
              <div className="services-state__icon">
                <Sparkles size={25} />
              </div>
              <strong>
                {debouncedSearch || statusFilter !== "all"
                  ? "No matching services"
                  : "No services yet"}
              </strong>
              <span>
                {debouncedSearch || statusFilter !== "all"
                  ? "Try another search or clear your filters."
                  : "Add your first service to start building this section."}
              </span>

              {!debouncedSearch && statusFilter === "all" ? (
                <button
                  type="button"
                  className="about-secondary-button"
                  onClick={openCreate}
                >
                  <Plus size={17} />
                  Add first service
                </button>
              ) : null}
            </div>
          ) : (
            <div className="services-list">
              {services.map((service, index) => {
                const Icon = getServiceIcon(service.icon);
                const moving = reorderingId === service.id;

                return (
                  <motion.article
                    layout
                    key={service.id}
                    className={`service-admin-card${
                      !service.is_active ? " service-admin-card--inactive" : ""
                    }`}
                  >
                    <div className="service-admin-card__order">
                      <GripVertical size={18} />

                      <div>
                        <button
                          type="button"
                          aria-label={`Move ${service.title} up`}
                          disabled={
                            !reorderEnabled ||
                            index === 0 ||
                            reorderingId !== null
                          }
                          onClick={() => void moveService(service, -1)}
                        >
                          <ArrowUp size={15} />
                        </button>

                        <button
                          type="button"
                          aria-label={`Move ${service.title} down`}
                          disabled={
                            !reorderEnabled ||
                            index === services.length - 1 ||
                            reorderingId !== null
                          }
                          onClick={() => void moveService(service, 1)}
                        >
                          <ArrowDown size={15} />
                        </button>
                      </div>
                    </div>

                    <div className="service-admin-card__icon">
                      <Icon size={25} strokeWidth={1.8} />
                    </div>

                    <div className="service-admin-card__body">
                      <div className="service-admin-card__title-row">
                        <h3>{service.title}</h3>

                        <span
                          className={`service-status${
                            service.is_active ? " service-status--active" : ""
                          }`}
                        >
                          <span />
                          {service.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <p>{service.description}</p>

                      <span className="service-admin-card__icon-name">
                        Icon · {service.icon}
                      </span>
                    </div>

                    <div className="service-admin-card__actions">
                      <label
                        className="service-active-toggle"
                        title={
                          service.is_active
                            ? "Hide from public website"
                            : "Show on public website"
                        }
                      >
                        <input
                          type="checkbox"
                          checked={service.is_active}
                          onChange={() => void handleToggleActive(service)}
                        />
                        <span />
                      </label>

                      <button
                        type="button"
                        className="service-card-action"
                        aria-label={`Edit ${service.title}`}
                        onClick={() => openEdit(service)}
                      >
                        <Pencil size={17} />
                      </button>

                      <button
                        type="button"
                        className="service-card-action service-card-action--danger"
                        aria-label={`Delete ${service.title}`}
                        onClick={() => setServiceToDelete(service)}
                      >
                        <Trash2 size={17} />
                      </button>

                      {moving ? (
                        <LoaderCircle
                          className="website-content-spin service-card-loader"
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
          className="service-modal"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeEditor();
            }
          }}
        >
          <motion.section
            className="service-modal__dialog service-editor"
            role="dialog"
            aria-modal="true"
            aria-labelledby="service-editor-title"
            initial={{ opacity: 0, scale: 0.97, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.18 }}
          >
            <header className="service-modal__header">
              <div>
                <span className="service-modal__eyebrow">
                  {editingService ? "Edit service" : "New service"}
                </span>
                <h2 id="service-editor-title">
                  {editingService
                    ? editingService.title
                    : "Add a portfolio service"}
                </h2>
                <p>
                  Choose an icon and write the copy visitors will see on your
                  portfolio.
                </p>
              </div>

              <button
                type="button"
                className="service-modal__close"
                aria-label="Close service editor"
                disabled={isSaving}
                onClick={closeEditor}
              >
                <X size={20} />
              </button>
            </header>

            <div className="service-editor__body">
              <div className="service-editor__fields">
                <label className="about-field">
                  <span>Service title</span>
                  <input
                    value={form.title}
                    maxLength={200}
                    placeholder="Full-Stack Development"
                    autoFocus
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        title: event.target.value,
                      }))
                    }
                  />
                  <small>Keep it clear and immediately understandable.</small>
                </label>

                <label className="about-field">
                  <span>Description</span>
                  <textarea
                    className="service-description-input"
                    value={form.description}
                    rows={5}
                    placeholder="Building complete web applications from polished frontend interfaces to reliable APIs and backend systems."
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        description: event.target.value,
                      }))
                    }
                  />
                  <small>
                    A concise explanation of the value this service provides.
                  </small>
                </label>

                <label className="service-editor__visibility">
                  <div>
                    <strong>Publicly visible</strong>
                    <span>Show this service on the public portfolio.</span>
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

                  <span className="service-visibility-switch">
                    <span />
                  </span>
                </label>
              </div>

              <div className="service-icon-picker">
                <div className="service-icon-picker__heading">
                  <div>
                    <span>Service icon</span>
                    <p>Pick the symbol that best represents this service.</p>
                  </div>

                  {(() => {
                    const PreviewIcon = getServiceIcon(form.icon);

                    return (
                      <div className="service-icon-picker__preview">
                        <PreviewIcon size={23} />
                      </div>
                    );
                  })()}
                </div>

                <div className="service-icon-picker__grid">
                  {SERVICE_ICON_OPTIONS.map((option) => {
                    const Icon = option.icon;
                    const selected = form.icon === option.name;

                    return (
                      <button
                        key={option.name}
                        type="button"
                        className={`service-icon-option${
                          selected ? " service-icon-option--selected" : ""
                        }`}
                        title={option.label}
                        aria-label={`Use ${option.label} icon`}
                        aria-pressed={selected}
                        onClick={() =>
                          setForm((current) => ({
                            ...current,
                            icon: option.name,
                          }))
                        }
                      >
                        <span className="service-icon-option__visual">
                          <Icon size={21} strokeWidth={1.8} />
                        </span>
                        <span>{option.label}</span>

                        {selected ? (
                          <span className="service-icon-option__check">
                            <Check size={12} strokeWidth={3} />
                          </span>
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <footer className="service-modal__footer">
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
                  : editingService
                    ? "Save changes"
                    : "Add service"}
              </button>
            </footer>
          </motion.section>
        </div>
      ) : null}

      {serviceToDelete ? (
        <div
          className="service-modal"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !isDeleting) {
              setServiceToDelete(null);
            }
          }}
        >
          <motion.section
            className="service-modal__dialog service-delete-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="service-delete-title"
            initial={{ opacity: 0, scale: 0.97, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.17 }}
          >
            <div className="service-delete-dialog__icon">
              <Trash2 size={24} />
            </div>

            <h2 id="service-delete-title">Delete this service?</h2>

            <p>
              <strong>{serviceToDelete.title}</strong> will be permanently
              removed. This action can't be undone.
            </p>

            <div className="service-delete-dialog__actions">
              <button
                type="button"
                className="about-secondary-button"
                disabled={isDeleting}
                onClick={() => setServiceToDelete(null)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="service-danger-button"
                disabled={isDeleting}
                onClick={() => void handleDelete()}
              >
                {isDeleting ? (
                  <LoaderCircle className="website-content-spin" size={17} />
                ) : (
                  <Trash2 size={17} />
                )}
                {isDeleting ? "Deleting..." : "Delete service"}
              </button>
            </div>
          </motion.section>
        </div>
      ) : null}
    </>
  );
}
