import { motion } from "framer-motion";
import { ArrowRight, FileText, FolderKanban, Image, Mail } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/authContext";

const overviewItems = [
  {
    label: "Projects",
    value: "Next",
    detail: "Project management",
    icon: FolderKanban,
  },
  {
    label: "Media",
    value: "Ready",
    detail: "R2 media storage",
    icon: Image,
  },
  {
    label: "Resume",
    value: "Planned",
    detail: "Experience & skills",
    icon: FileText,
  },
  {
    label: "Inquiries",
    value: "Planned",
    detail: "Contact submissions",
    icon: Mail,
  },
];

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <motion.div
      className="admin-page"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <section className="dashboard-hero">
        <div>
          <span className="admin-eyebrow">Control Center</span>

          <h1>Welcome back, Nurlan.</h1>

          <p>
            Manage the content and media powering your portfolio from one
            workspace.
          </p>
        </div>

        <div className="dashboard-hero__account">
          <span>Signed in as</span>
          <strong>{user?.email}</strong>
          <small>Super administrator</small>
        </div>
      </section>

      <section className="dashboard-overview" aria-label="Portfolio overview">
        {overviewItems.map((item, index) => {
          const Icon = item.icon;

          return (
            <motion.article
              className="overview-card"
              key={item.label}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.35,
                delay: 0.05 + index * 0.05,
              }}
            >
              <div className="overview-card__icon">
                <Icon size={22} />
              </div>

              <div>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                <small>{item.detail}</small>
              </div>
            </motion.article>
          );
        })}
      </section>

      <section className="dashboard-grid">
        <article className="dashboard-panel dashboard-panel--featured">
          <div className="dashboard-panel__heading">
            <div>
              <span className="admin-eyebrow">Available now</span>
              <h2>Media Library</h2>
            </div>

            <div className="dashboard-panel__icon">
              <Image size={24} />
            </div>
          </div>

          <p>
            Upload and manage portfolio images and PDF documents stored securely
            in Cloudflare R2.
          </p>

          <div className="dashboard-panel__features">
            <span>Image optimization</span>
            <span>WebP variants</span>
            <span>PDF documents</span>
            <span>Alt text</span>
          </div>

          <Link className="admin-primary-action" to="/media">
            Open Media Library
            <ArrowRight size={19} />
          </Link>
        </article>

        <article className="dashboard-panel">
          <div className="dashboard-panel__heading">
            <div>
              <span className="admin-eyebrow">Build progress</span>
              <h2>Management modules</h2>
            </div>
          </div>

          <div className="dashboard-progress-list">
            <div>
              <span>
                <i className="status-dot status-dot--ready" />
                Authentication
              </span>
              <strong>Ready</strong>
            </div>

            <div>
              <span>
                <i className="status-dot status-dot--ready" />
                Media Library
              </span>
              <strong>Backend ready</strong>
            </div>

            <div>
              <span>
                <i className="status-dot" />
                Projects
              </span>
              <strong>Next phase</strong>
            </div>

            <div>
              <span>
                <i className="status-dot" />
                Resume & Content
              </span>
              <strong>Planned</strong>
            </div>
          </div>
        </article>
      </section>
    </motion.div>
  );
}
