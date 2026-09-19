import { AxiosError } from "axios";
import { motion } from "framer-motion";
import {
  SiFacebook,
  SiGithub,
  SiInstagram,
  SiLeetcode,
  SiX,
  SiYoutube,
} from "react-icons/si";
import { FaLinkedin } from "react-icons/fa6";
import {
  ArrowDown,
  ArrowUp,
  BriefcaseBusiness,
  Check,
  FileText,
  Globe2,
  Image as ImageIcon,
  Link2,
  LoaderCircle,
  MapPin,
  Plus,
  Save,
  Trash2,
  UserRound,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AboutRichTextEditor } from "../components/content/AboutRichTextEditor";
import { ContentMediaPicker } from "../components/content/ContentMediaPicker";
import { SkillsContentPanel } from "../components/content/SkillsContentPanel";
import { ServicesContentPanel } from "../components/content/ServicesContentPanel";
import { useToast } from "../context/toastContext";
import { getAboutContent, updateAboutContent } from "../services/aboutApi";
import type { MediaAsset } from "../types/media";
import type {
  AboutContent,
  AboutContentPayload,
  AvailabilityMode,
} from "../types/about";

type ContentTab = "about" | "skills" | "services" | "contact";

interface AboutForm {
  full_name: string;
  profile_media_asset_id: number | null;
  profile_image_url: string | null;
  resume_media_asset_id: number | null;
  resume_url: string | null;
  resume_filename: string | null;
  about_html: string;
  experience_years: number;
  location: string;
  is_available: boolean;
  availability_modes: AvailabilityMode[];
  software_fields: string[];
  social_links: Array<{
    platform: string;
    url: string;
  }>;
}

const EMPTY_FORM: AboutForm = {
  full_name: "",
  profile_media_asset_id: null,
  profile_image_url: null,
  resume_media_asset_id: null,
  resume_url: null,
  resume_filename: null,
  about_html: "",
  experience_years: 0,
  location: "",
  is_available: true,
  availability_modes: ["remote"],
  software_fields: [""],
  social_links: [],
};

const CONTENT_TABS: Array<{
  id: ContentTab;
  label: string;
  description: string;
}> = [
  {
    id: "about",
    label: "About",
    description: "Identity and profile",
  },
  {
    id: "skills",
    label: "Skills",
    description: "Technology stack",
  },
  {
    id: "services",
    label: "Services",
    description: "What you offer",
  },
  {
    id: "contact",
    label: "Contact",
    description: "Public contact details",
  },
];

const AVAILABILITY_OPTIONS: Array<{
  value: AvailabilityMode;
  label: string;
  description: string;
}> = [
  {
    value: "remote",
    label: "Remote",
    description: "Open to fully remote opportunities.",
  },
  {
    value: "onsite",
    label: "On-site",
    description: "Available to work from an office.",
  },
  {
    value: "hybrid",
    label: "Hybrid",
    description: "Comfortable combining remote and office work.",
  },
];

const SOCIAL_PLATFORMS = [
  { value: "LinkedIn", label: "LinkedIn", icon: FaLinkedin },
  { value: "GitHub", label: "GitHub", icon: SiGithub },
  { value: "X", label: "X", icon: SiX },
  { value: "Instagram", label: "Instagram", icon: SiInstagram },
  { value: "YouTube", label: "YouTube", icon: SiYoutube },
  { value: "Facebook", label: "Facebook", icon: SiFacebook },
  { value: "LeetCode", label: "LeetCode", icon: SiLeetcode },
  { value: "Other", label: "Other", icon: Plus },
] as const;

function getSocialPlatformSelection(platform: string) {
  const normalized = platform.trim().toLowerCase();

  if (!normalized) {
    return "";
  }

  const known = SOCIAL_PLATFORMS.find(
    (option) =>
      option.value !== "Other" && option.value.toLowerCase() === normalized,
  );

  return known?.value ?? "Other";
}

function normalizeUniqueValue(value: string) {
  return value.trim().replace(/\s+/g, " ").toLowerCase();
}

function findDuplicateValue(values: string[]) {
  const seen = new Set<string>();

  for (const value of values) {
    const trimmed = value.trim();

    if (!trimmed) {
      continue;
    }

    const normalized = normalizeUniqueValue(trimmed);

    if (seen.has(normalized)) {
      return trimmed;
    }

    seen.add(normalized);
  }

  return null;
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
          .map((message) =>
            message
              .replace(/^Value error,\s*/i, "")
              .replace(/Software fields/gi, "Professional titles"),
          )
          .join(" ");
      }
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

function toForm(content: AboutContent | null): AboutForm {
  if (!content) {
    return { ...EMPTY_FORM };
  }

  return {
    full_name: content.full_name,
    profile_media_asset_id: content.profile_media_asset_id,
    profile_image_url:
      content.profile_thumbnail_url ?? content.profile_image_url,
    resume_media_asset_id: content.resume_media_asset_id,
    resume_url: content.resume_url,
    resume_filename: content.resume_filename,
    about_html: content.about_html,
    experience_years: content.experience_years,
    location: content.location,
    is_available: content.is_available,
    availability_modes: [...content.availability_modes],
    software_fields:
      content.software_fields.length > 0
        ? [...content.software_fields]
            .sort((a, b) => a.display_order - b.display_order)
            .map((field) => field.name)
        : [""],
    social_links: [...content.social_links]
      .sort((a, b) => a.display_order - b.display_order)
      .map((link) => ({
        platform: link.platform,
        url: link.url,
      })),
  };
}

function comparableForm(form: AboutForm) {
  return JSON.stringify({
    full_name: form.full_name,
    profile_media_asset_id: form.profile_media_asset_id,
    resume_media_asset_id: form.resume_media_asset_id,
    about_html: form.about_html,
    experience_years: form.experience_years,
    location: form.location,
    is_available: form.is_available,
    availability_modes: form.availability_modes,
    software_fields: form.software_fields,
    social_links: form.social_links,
  });
}

function initials(value: string) {
  const parts = value.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 0) {
    return "NR";
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export default function WebsiteContentPage() {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<ContentTab>("about");
  const [form, setForm] = useState<AboutForm>(EMPTY_FORM);
  const [savedSnapshot, setSavedSnapshot] = useState(
    comparableForm(EMPTY_FORM),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [mediaPickerMode, setMediaPickerMode] = useState<
    "profile" | "resume" | null
  >(null);

  const isDirty = useMemo(
    () => comparableForm(form) !== savedSnapshot,
    [form, savedSnapshot],
  );

  const loadAbout = useCallback(async () => {
    setIsLoading(true);

    try {
      const content = await getAboutContent();
      const nextForm = toForm(content);

      setForm(nextForm);
      setSavedSnapshot(comparableForm(nextForm));
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not load About content",
        message: getErrorMessage(error),
      });
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    void loadAbout();
  }, [loadAbout]);

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

  function updateSoftwareField(index: number, value: string) {
    setForm((current) => ({
      ...current,
      software_fields: current.software_fields.map((field, fieldIndex) =>
        fieldIndex === index ? value : field,
      ),
    }));
  }

  function addSoftwareField() {
    setForm((current) => {
      if (current.software_fields.length >= 4) {
        return current;
      }

      return {
        ...current,
        software_fields: [...current.software_fields, ""],
      };
    });
  }

  function removeSoftwareField(index: number) {
    setForm((current) => {
      const next = current.software_fields.filter(
        (_, fieldIndex) => fieldIndex !== index,
      );

      return {
        ...current,
        software_fields: next.length > 0 ? next : [""],
      };
    });
  }

  function moveSoftwareField(index: number, direction: -1 | 1) {
    setForm((current) => {
      const target = index + direction;

      if (target < 0 || target >= current.software_fields.length) {
        return current;
      }

      const next = [...current.software_fields];
      [next[index], next[target]] = [next[target], next[index]];

      return {
        ...current,
        software_fields: next,
      };
    });
  }

  function toggleAvailabilityMode(mode: AvailabilityMode) {
    setForm((current) => ({
      ...current,
      availability_modes: current.availability_modes.includes(mode)
        ? current.availability_modes.filter((item) => item !== mode)
        : [...current.availability_modes, mode],
    }));
  }

  function addSocialLink() {
    setForm((current) => ({
      ...current,
      social_links: [
        ...current.social_links,
        {
          platform: "",
          url: "",
        },
      ],
    }));
  }

  function updateSocialLink(
    index: number,
    field: "platform" | "url",
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      social_links: current.social_links.map((link, linkIndex) =>
        linkIndex === index
          ? {
              ...link,
              [field]: value,
            }
          : link,
      ),
    }));
  }

  function removeSocialLink(index: number) {
    setForm((current) => ({
      ...current,
      social_links: current.social_links.filter(
        (_, linkIndex) => linkIndex !== index,
      ),
    }));
  }

  function moveSocialLink(index: number, direction: -1 | 1) {
    setForm((current) => {
      const target = index + direction;

      if (target < 0 || target >= current.social_links.length) {
        return current;
      }

      const next = [...current.social_links];
      [next[index], next[target]] = [next[target], next[index]];

      return {
        ...current,
        social_links: next,
      };
    });
  }

  async function handleSave() {
    if (isSaving) {
      return;
    }

    const softwareFields = form.software_fields
      .map((field) => field.trim())
      .filter(Boolean);

    if (!form.full_name.trim()) {
      showToast({
        type: "error",
        title: "Full name required",
        message: "Add your full name before saving About content.",
      });
      return;
    }

    if (softwareFields.length === 0) {
      showToast({
        type: "error",
        title: "Professional title required",
        message: "Add at least one professional title.",
      });
      return;
    }

    const duplicateSoftwareField = findDuplicateValue(softwareFields);

    if (duplicateSoftwareField) {
      showToast({
        type: "error",
        title: "Duplicate professional title",
        message: `“${duplicateSoftwareField}” has already been added. Each title must be unique.`,
      });
      return;
    }

    if (form.is_available && form.availability_modes.length === 0) {
      showToast({
        type: "error",
        title: "Choose availability",
        message: "Select at least one availability mode.",
      });
      return;
    }

    const incompleteSocialLink = form.social_links.some(
      (link) => !link.platform.trim() || !link.url.trim(),
    );

    if (incompleteSocialLink) {
      showToast({
        type: "error",
        title: "Complete social links",
        message: "Each social link needs both a platform and URL.",
      });
      return;
    }

    const duplicateSocialPlatform = findDuplicateValue(
      form.social_links.map((link) => link.platform),
    );

    if (duplicateSocialPlatform) {
      showToast({
        type: "error",
        title: "Duplicate social platform",
        message: `“${duplicateSocialPlatform}” has already been added. Choose each platform only once.`,
      });
      return;
    }

    const payload: AboutContentPayload = {
      full_name: form.full_name.trim(),
      profile_media_asset_id: form.profile_media_asset_id,
      resume_media_asset_id: form.resume_media_asset_id,
      about_html: form.about_html,
      experience_years: Math.max(0, Math.round(form.experience_years || 0)),
      location: form.location.trim(),
      is_available: form.is_available,
      availability_modes: form.is_available ? form.availability_modes : [],
      software_fields: softwareFields.map((name) => ({ name })),
      social_links: form.social_links.map((link) => ({
        platform: link.platform.trim(),
        url: link.url.trim(),
      })),
    };

    setIsSaving(true);

    try {
      const saved = await updateAboutContent(payload);
      const nextForm = toForm(saved);

      setForm(nextForm);
      setSavedSnapshot(comparableForm(nextForm));

      showToast({
        type: "success",
        title: "About content saved",
        message: "Your portfolio About content has been updated.",
      });
    } catch (error) {
      showToast({
        type: "error",
        title: "Could not save About content",
        message: getErrorMessage(error),
      });
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="admin-page website-content-page">
      <header className="admin-page-header website-content-page__header">
        <div>
          <span className="admin-eyebrow">Portfolio content</span>
          <h1>Website Content</h1>
          <p>
            Manage the content that powers the main sections of your public
            portfolio.
          </p>
        </div>

        {activeTab === "about" ? (
          <div className="website-content-page__save-area">
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
              disabled={isLoading || isSaving || !isDirty}
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
        ) : null}
      </header>

      <nav className="website-content-tabs" aria-label="Website content">
        {CONTENT_TABS.map((tab) => {
          const available =
            tab.id === "about" || tab.id === "skills" || tab.id === "services";

          return (
            <button
              key={tab.id}
              className={`website-content-tab${
                activeTab === tab.id ? " website-content-tab--active" : ""
              }`}
              type="button"
              disabled={!available}
              onClick={() => {
                if (available) {
                  setActiveTab(tab.id);
                }
              }}
            >
              <strong>{tab.label}</strong>
              <span>
                {available ? tab.description : `${tab.description} · Soon`}
              </span>
            </button>
          );
        })}
      </nav>

      {activeTab === "about" ? (
        isLoading ? (
          <section className="website-content-state">
            <LoaderCircle className="website-content-spin" size={32} />
            <strong>Loading About content</strong>
            <span>Fetching your portfolio profile...</span>
          </section>
        ) : (
          <motion.div
            className="about-content-layout"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="about-content-main">
              <section className="about-content-card about-identity-card">
                <header className="about-content-card__header">
                  <div className="about-content-card__icon">
                    <UserRound size={21} />
                  </div>
                  <div>
                    <h2>Profile & identity</h2>
                    <p>
                      Your primary identity and profile image across the
                      portfolio.
                    </p>
                  </div>
                </header>

                <div className="about-profile-row">
                  <div className="about-profile-photo">
                    {form.profile_image_url ? (
                      <img src={form.profile_image_url} alt="" />
                    ) : (
                      <span>{initials(form.full_name)}</span>
                    )}
                  </div>

                  <div className="about-profile-copy">
                    <strong>Profile image</strong>
                    <p>Choose a polished portrait from your Media Library.</p>

                    <div className="about-inline-actions">
                      <button
                        type="button"
                        className="about-secondary-button"
                        onClick={() => setMediaPickerMode("profile")}
                      >
                        <ImageIcon size={17} />
                        Choose image
                      </button>

                      {form.profile_media_asset_id ? (
                        <button
                          type="button"
                          className="about-text-button"
                          onClick={() =>
                            setForm((current) => ({
                              ...current,
                              profile_media_asset_id: null,
                              profile_image_url: null,
                            }))
                          }
                        >
                          Remove
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>

                <label className="about-field">
                  <span>Full name</span>
                  <input
                    value={form.full_name}
                    maxLength={200}
                    placeholder="Nurlan Rahimli"
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        full_name: event.target.value,
                      }))
                    }
                  />
                  <small>
                    Used as your main public-facing name across the portfolio.
                  </small>
                </label>
              </section>

              <section className="about-content-card">
                <header className="about-content-card__header about-content-card__header--action">
                  <div className="about-content-card__heading">
                    <div className="about-content-card__icon">
                      <BriefcaseBusiness size={21} />
                    </div>
                    <div>
                      <h2>Professional titles</h2>
                      <p>
                        These can rotate through the animated title treatment on
                        your public site.
                      </p>
                    </div>
                  </div>

                  <button
                    className="about-secondary-button"
                    type="button"
                    disabled={form.software_fields.length >= 4}
                    onClick={addSoftwareField}
                  >
                    <Plus size={17} />
                    Add title
                  </button>
                </header>

                <div className="about-title-list">
                  {form.software_fields.map((field, index) => (
                    <div className="about-title-row" key={index}>
                      <div className="about-title-row__order">
                        <button
                          type="button"
                          aria-label={`Move title ${index + 1} up`}
                          disabled={index === 0}
                          onClick={() => moveSoftwareField(index, -1)}
                        >
                          <ArrowUp size={16} />
                        </button>

                        <span>{index + 1}</span>

                        <button
                          type="button"
                          aria-label={`Move title ${index + 1} down`}
                          disabled={index === form.software_fields.length - 1}
                          onClick={() => moveSoftwareField(index, 1)}
                        >
                          <ArrowDown size={16} />
                        </button>
                      </div>

                      <input
                        value={field}
                        maxLength={120}
                        placeholder={
                          index === 0
                            ? "Software Engineer"
                            : index === 1
                              ? "AI Engineer"
                              : "Add another professional title"
                        }
                        onChange={(event) =>
                          updateSoftwareField(index, event.target.value)
                        }
                      />

                      <button
                        className="about-icon-button about-icon-button--danger"
                        type="button"
                        aria-label={`Remove title ${index + 1}`}
                        disabled={form.software_fields.length === 1}
                        onClick={() => removeSoftwareField(index)}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  ))}
                </div>

                <div className="about-card-note">
                  <span>{form.software_fields.length}/4 titles</span>
                  <span>Order controls the public animation sequence.</span>
                </div>
              </section>

              <section className="about-content-card">
                <header className="about-content-card__header">
                  <div className="about-content-card__icon">
                    <FileText size={21} />
                  </div>
                  <div>
                    <h2>About me</h2>
                    <p>
                      Write this exactly as you want it formatted on your
                      portfolio.
                    </p>
                  </div>
                </header>

                <AboutRichTextEditor
                  value={form.about_html}
                  disabled={isSaving}
                  onChange={(about_html) =>
                    setForm((current) => ({
                      ...current,
                      about_html,
                    }))
                  }
                />
              </section>

              <section className="about-content-card">
                <header className="about-content-card__header">
                  <div className="about-content-card__icon">
                    <Globe2 size={21} />
                  </div>
                  <div>
                    <h2>Social profiles</h2>
                    <p>
                      Add the public profiles you want visitors to be able to
                      reach.
                    </p>
                  </div>
                </header>

                {form.social_links.length === 0 ? (
                  <div className="about-empty-inline">
                    <Link2 size={21} />
                    <div>
                      <strong>No social profiles yet</strong>
                      <span>
                        Add LinkedIn, GitHub, X, YouTube, LeetCode, or another
                        profile.
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="about-social-list">
                    {form.social_links.map((link, index) => (
                      <div className="about-social-row" key={index}>
                        <div className="about-social-row__order">
                          <button
                            type="button"
                            aria-label={`Move social link ${index + 1} up`}
                            disabled={index === 0}
                            onClick={() => moveSocialLink(index, -1)}
                          >
                            <ArrowUp size={16} />
                          </button>
                          <button
                            type="button"
                            aria-label={`Move social link ${index + 1} down`}
                            disabled={index === form.social_links.length - 1}
                            onClick={() => moveSocialLink(index, 1)}
                          >
                            <ArrowDown size={16} />
                          </button>
                        </div>

                        <div className="about-field">
                          <span>Platform</span>

                          <div
                            className="about-social-platforms"
                            role="group"
                            aria-label={`Choose platform for social profile ${index + 1}`}
                          >
                            {SOCIAL_PLATFORMS.map((platform) => {
                              const selected =
                                getSocialPlatformSelection(link.platform) ===
                                platform.value;

                              const PlatformIcon = platform.icon;

                              return (
                                <button
                                  key={platform.value}
                                  className={`about-social-platform${
                                    selected
                                      ? " about-social-platform--selected"
                                      : ""
                                  }`}
                                  type="button"
                                  title={platform.label}
                                  aria-label={platform.label}
                                  aria-pressed={selected}
                                  disabled={isSaving}
                                  onClick={() => {
                                    if (platform.value === "Other") {
                                      const currentSelection =
                                        getSocialPlatformSelection(
                                          link.platform,
                                        );

                                      updateSocialLink(
                                        index,
                                        "platform",
                                        currentSelection === "Other"
                                          ? link.platform
                                          : "",
                                      );
                                      return;
                                    }

                                    updateSocialLink(
                                      index,
                                      "platform",
                                      platform.value,
                                    );
                                  }}
                                >
                                  <PlatformIcon
                                    className="about-social-platform__icon"
                                    size={19}
                                    aria-hidden="true"
                                  />
                                </button>
                              );
                            })}
                          </div>

                          {getSocialPlatformSelection(link.platform) ===
                          "Other" ? (
                            <input
                              className="about-social-platform__custom"
                              value={link.platform}
                              maxLength={80}
                              placeholder="Platform name"
                              disabled={isSaving}
                              onChange={(event) =>
                                updateSocialLink(
                                  index,
                                  "platform",
                                  event.target.value,
                                )
                              }
                            />
                          ) : null}
                        </div>

                        <label className="about-field">
                          <span>Profile URL</span>
                          <input
                            type="url"
                            value={link.url}
                            placeholder="https://..."
                            onChange={(event) =>
                              updateSocialLink(index, "url", event.target.value)
                            }
                          />
                        </label>

                        <button
                          className="about-icon-button about-icon-button--danger"
                          type="button"
                          aria-label={`Remove ${link.platform || "social link"}`}
                          onClick={() => removeSocialLink(index)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <button
                  className="about-secondary-button about-add-social"
                  type="button"
                  onClick={addSocialLink}
                >
                  <Plus size={17} />
                  Add social profile
                </button>
              </section>
            </div>

            <aside className="about-content-sidebar">
              <section className="about-content-card">
                <header className="about-content-card__header">
                  <div className="about-content-card__icon">
                    <BriefcaseBusiness size={21} />
                  </div>
                  <div>
                    <h2>Career details</h2>
                    <p>Quick facts shown alongside your profile.</p>
                  </div>
                </header>

                <label className="about-field">
                  <span>Years of experience</span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={form.experience_years}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        experience_years: Number(event.target.value),
                      }))
                    }
                  />
                </label>

                <label className="about-field">
                  <span>Location</span>
                  <div className="about-input-with-icon">
                    <MapPin size={18} />
                    <input
                      value={form.location}
                      maxLength={255}
                      placeholder="Sacramento, California"
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          location: event.target.value,
                        }))
                      }
                    />
                  </div>
                  <small>
                    Free-form text. Use whatever wording you prefer.
                  </small>
                </label>
              </section>

              <section className="about-content-card">
                <header className="about-content-card__header">
                  <div className="about-content-card__icon">
                    <Globe2 size={21} />
                  </div>
                  <div>
                    <h2>Availability</h2>
                    <p>
                      Control whether and how you are open to opportunities.
                    </p>
                  </div>
                </header>

                <label className="about-availability-toggle">
                  <div>
                    <strong>Available for opportunities</strong>
                    <span>
                      Show visitors that you're currently open to new work.
                    </span>
                  </div>

                  <input
                    type="checkbox"
                    checked={form.is_available}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        is_available: event.target.checked,
                      }))
                    }
                  />
                  <span className="about-switch" />
                </label>

                <div
                  className={`about-availability-options${
                    !form.is_available
                      ? " about-availability-options--disabled"
                      : ""
                  }`}
                >
                  {AVAILABILITY_OPTIONS.map((option) => {
                    const selected = form.availability_modes.includes(
                      option.value,
                    );

                    return (
                      <button
                        key={option.value}
                        className={`about-availability-option${
                          selected ? " about-availability-option--selected" : ""
                        }`}
                        type="button"
                        disabled={!form.is_available}
                        onClick={() => toggleAvailabilityMode(option.value)}
                      >
                        <span className="about-availability-option__check">
                          {selected ? <Check size={15} /> : null}
                        </span>
                        <span>
                          <strong>{option.label}</strong>
                          <small>{option.description}</small>
                        </span>
                      </button>
                    );
                  })}
                </div>
              </section>

              <section className="about-content-card">
                <header className="about-content-card__header">
                  <div className="about-content-card__icon">
                    <FileText size={21} />
                  </div>
                  <div>
                    <h2>Résumé</h2>
                    <p>Your downloadable public résumé PDF.</p>
                  </div>
                </header>

                {form.resume_media_asset_id ? (
                  <div className="about-resume-selected">
                    <div className="about-resume-selected__icon">
                      <FileText size={23} />
                    </div>
                    <div>
                      <strong>{form.resume_filename || "Résumé PDF"}</strong>
                      <span>Selected from Media Library</span>
                    </div>
                  </div>
                ) : (
                  <div className="about-resume-empty">
                    <FileText size={26} />
                    <strong>No résumé selected</strong>
                    <span>Choose or upload a PDF from your Media Library.</span>
                  </div>
                )}

                <div className="about-resume-actions">
                  <button
                    className="about-secondary-button"
                    type="button"
                    onClick={() => setMediaPickerMode("resume")}
                  >
                    <FileText size={17} />
                    {form.resume_media_asset_id
                      ? "Replace résumé"
                      : "Choose résumé"}
                  </button>

                  {form.resume_url ? (
                    <a
                      className="about-text-button"
                      href={form.resume_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Preview
                    </a>
                  ) : null}

                  {form.resume_media_asset_id ? (
                    <button
                      className="about-text-button about-text-button--danger"
                      type="button"
                      onClick={() =>
                        setForm((current) => ({
                          ...current,
                          resume_media_asset_id: null,
                          resume_url: null,
                          resume_filename: null,
                        }))
                      }
                    >
                      Remove
                    </button>
                  ) : null}
                </div>
              </section>
            </aside>
          </motion.div>
        )
      ) : null}
      {activeTab === "skills" ? <SkillsContentPanel /> : null}
      {activeTab === "services" ? <ServicesContentPanel /> : null}

      <ContentMediaPicker
        isOpen={mediaPickerMode !== null}
        mode={mediaPickerMode ?? "profile"}
        selectedId={
          mediaPickerMode === "resume"
            ? form.resume_media_asset_id
            : form.profile_media_asset_id
        }
        onClose={() => setMediaPickerMode(null)}
        onSelect={(asset: MediaAsset) => {
          if (mediaPickerMode === "resume") {
            setForm((current) => ({
              ...current,
              resume_media_asset_id: asset.id,
              resume_url: asset.url,
              resume_filename: asset.original_filename,
            }));
            return;
          }

          const preview =
            asset.variants.find((variant) => variant.variant_name === "small")
              ?.url ??
            asset.variants.find((variant) => variant.variant_name === "medium")
              ?.url ??
            asset.variants.find(
              (variant) => variant.variant_name === "thumbnail",
            )?.url ??
            asset.url;

          setForm((current) => ({
            ...current,
            profile_media_asset_id: asset.id,
            profile_image_url: preview,
          }));
        }}
      />
    </div>
  );
}
