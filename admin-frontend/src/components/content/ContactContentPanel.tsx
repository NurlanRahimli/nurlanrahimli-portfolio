import { AxiosError } from "axios";
import { motion } from "framer-motion";
import {
  BarChart3,
  Check,
  Hash,
  LoaderCircle,
  Mail,
  Phone,
  Save,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useToast } from "../../context/toastContext";
import {
  getContactContent,
  updateContactContent,
} from "../../services/contactApi";
import type {
  ContactContent,
  ContactContentPayload,
} from "../../types/contact";

interface ContactForm {
  projects_built: string;
  email: string;
  phone_number: string;
}

const EMPTY_FORM: ContactForm = {
  projects_built: "0",
  email: "",
  phone_number: "",
};

function toForm(content: ContactContent | null): ContactForm {
  if (!content) {
    return { ...EMPTY_FORM };
  }

  return {
    projects_built: String(content.projects_built),
    email: content.email,
    phone_number: content.phone_number,
  };
}

function comparableForm(form: ContactForm) {
  return JSON.stringify({
    projects_built: form.projects_built.trim(),
    email: form.email.trim(),
    phone_number: form.phone_number.trim(),
  });
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
        return messages
          .map((message) => message.replace(/^Value error,\s*/i, ""))
          .join(" ");
      }
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

export function ContactContentPanel() {
  const { showToast } = useToast();
  const [form, setForm] = useState<ContactForm>(EMPTY_FORM);
  const [savedSnapshot, setSavedSnapshot] = useState(
    comparableForm(EMPTY_FORM),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const isDirty = useMemo(
    () => comparableForm(form) !== savedSnapshot,
    [form, savedSnapshot],
  );

  const loadContact = useCallback(async () => {
    setIsLoading(true);

    try {
      const content = await getContactContent();
      const nextForm = toForm(content);

      setForm(nextForm);
      setSavedSnapshot(comparableForm(nextForm));
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load Contact content",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    void loadContact();
  }, [loadContact]);

  useEffect(() => {
    if (!isDirty) {
      return;
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [isDirty]);

  async function handleSave() {
    if (isSaving) {
      return;
    }

    const projectsBuilt = Number(form.projects_built);

    if (
      !Number.isInteger(projectsBuilt) ||
      !Number.isFinite(projectsBuilt) ||
      projectsBuilt < 0
    ) {
      showToast({
        type: "error",
        title: "Projects built is invalid",
        message: "Enter a whole number of zero or greater.",
      });
      return;
    }

    const email = form.email.trim();
    const phoneNumber = form.phone_number.trim();

    if (!email) {
      showToast({
        type: "error",
        title: "Email required",
        message: "Add the public email address for your portfolio.",
      });
      return;
    }

    if (!phoneNumber) {
      showToast({
        type: "error",
        title: "Phone number required",
        message: "Add the public phone number for your portfolio.",
      });
      return;
    }

    const payload: ContactContentPayload = {
      projects_built: projectsBuilt,
      email,
      phone_number: phoneNumber,
    };

    setIsSaving(true);

    try {
      const saved = await updateContactContent(payload);
      const nextForm = toForm(saved);

      setForm(nextForm);
      setSavedSnapshot(comparableForm(nextForm));

      showToast({
        type: "success",
        title: "Contact content saved",
        message: "Your public contact details have been updated.",
      });
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not save Contact content",
        message: getErrorMessage(error),
      });
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <section className="website-content-state">
        <LoaderCircle className="website-content-spin" size={32} />
        <strong>Loading Contact content</strong>
        <span>Fetching your public contact details...</span>
      </section>
    );
  }

  return (
    <motion.div
      className="contact-content-panel"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <section className="contact-content-card">
        <div className="contact-content-card__top">
          <div className="contact-content-card__heading">
            <div className="contact-content-card__icon">
              <BarChart3 size={22} />
            </div>

            <div>
              <span className="contact-content-card__eyebrow">
                Public information
              </span>
              <h2>Contact details</h2>
              <p>
                Keep the key numbers and contact information shown on your
                portfolio up to date.
              </p>
            </div>
          </div>

          <div className="contact-content-save">
            <span
              className={`website-content-page__save-status${
                isDirty ? " website-content-page__save-status--dirty" : ""
              }`}
            >
              <span />
              {isDirty ? "Unsaved changes" : "All changes saved"}
            </span>

            <button
              className="admin-primary-action"
              type="button"
              disabled={isSaving || !isDirty}
              onClick={() => void handleSave()}
            >
              {isSaving ? (
                <LoaderCircle className="website-content-spin" size={18} />
              ) : isDirty ? (
                <Save size={18} />
              ) : (
                <Check size={18} />
              )}

              {isSaving ? "Saving..." : isDirty ? "Save changes" : "Saved"}
            </button>
          </div>
        </div>

        <div className="contact-content-fields">
          <label className="contact-content-field contact-content-field--projects">
            <span className="contact-content-field__label">
              <span className="contact-content-field__label-icon">
                <Hash size={18} />
              </span>
              <span>
                <strong>Projects built</strong>
                <small>Total number displayed on your public portfolio.</small>
              </span>
            </span>

            <input
              type="number"
              min={0}
              step={1}
              inputMode="numeric"
              value={form.projects_built}
              disabled={isSaving}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  projects_built: event.target.value,
                }))
              }
            />
          </label>

          <label className="contact-content-field">
            <span className="contact-content-field__label">
              <span className="contact-content-field__label-icon">
                <Mail size={18} />
              </span>
              <span>
                <strong>Email address</strong>
                <small>The email visitors can use to reach you.</small>
              </span>
            </span>

            <input
              type="email"
              autoComplete="email"
              maxLength={320}
              placeholder="hello@example.com"
              value={form.email}
              disabled={isSaving}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  email: event.target.value,
                }))
              }
            />
          </label>

          <label className="contact-content-field">
            <span className="contact-content-field__label">
              <span className="contact-content-field__label-icon">
                <Phone size={18} />
              </span>
              <span>
                <strong>Phone number</strong>
                <small>Formatting is preserved exactly as you enter it.</small>
              </span>
            </span>

            <input
              type="tel"
              autoComplete="tel"
              maxLength={80}
              placeholder="+1 (916) 555-1234"
              value={form.phone_number}
              disabled={isSaving}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  phone_number: event.target.value,
                }))
              }
            />
          </label>
        </div>

        <footer className="contact-content-card__footer">
          <div>
            <Check size={17} />
            <span>
              These values are exposed through the public portfolio API.
            </span>
          </div>
        </footer>
      </section>
    </motion.div>
  );
}
