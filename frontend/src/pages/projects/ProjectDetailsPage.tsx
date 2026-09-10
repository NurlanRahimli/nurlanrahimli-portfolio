import {
  ArrowLeft,
  ArrowRight,
  Check,
  ExternalLink,
  Lightbulb,
  Package,
} from 'lucide-react'
import { SiGithub } from 'react-icons/si'
import { Link, Navigate, useParams } from 'react-router-dom'
import { getProjectBySlug, projects } from './projectData'

const bookaifyGallery = [
  {
    label: 'Dashboard',
    className: 'project-gallery-dashboard',
  },
  {
    label: 'AI Assistant',
    className: 'project-gallery-chat',
  },
  {
    label: 'Receipt OCR',
    className: 'project-gallery-receipt',
  },
  {
    label: 'Analytics',
    className: 'project-gallery-analytics',
  },
]

const projectMeta = {
  bookaify: {
    type: 'Web Application',
    date: 'Jun 2026',
    stats: [
      { value: '143', label: 'Unit Tests' },
      { value: '5', label: 'Services' },
      { value: '2', label: 'Months' },
      { value: 'Production', label: 'Status' },
    ],
    stack: {
      Frontend: ['React', 'Vite', 'TypeScript'],
      Backend: [
        'FastAPI',
        'PostgreSQL',
        'SQLAlchemy',
        'Redis',
        'RQ',
        'Docker',
        'OpenAI API',
      ],
      Infrastructure: ['Render', 'Vercel', 'GitHub Actions'],
    },
    learned:
      'This project strengthened my ability to combine multiple AI services with production backend architecture, asynchronous processing, tool calling, and complex financial workflows.',
    quote: 'Turning complex financial data into clear, useful interactions through AI.',
  },

  'ai-quiz-platform': {
    type: 'AI Application',
    date: 'Aug 2026',
    stats: [
      { value: 'AI', label: 'Explanations' },
      { value: 'OCR', label: 'Imports' },
      { value: 'SymPy', label: 'Math Engine' },
      { value: 'Full-Stack', label: 'Status' },
    ],
    stack: {
      Frontend: ['React', 'TypeScript', 'Vite'],
      Backend: ['FastAPI', 'PostgreSQL', 'SQLAlchemy', 'SymPy'],
      Testing: ['Pytest', 'Playwright'],
    },
    learned:
      'This project taught me how to combine deterministic systems with AI features so that generated explanations remain useful while grading and mathematical validation stay reliable.',
    quote: 'AI works best when intelligence and deterministic engineering support each other.',
  },

  'altura-group': {
    type: 'Corporate Platform',
    date: 'Sep 2026',
    stats: [
      { value: '3', label: 'Languages' },
      { value: 'R2', label: 'Media Storage' },
      { value: 'Admin', label: 'CMS' },
      { value: 'Production', label: 'Status' },
    ],
    stack: {
      Frontend: ['React', 'TypeScript', 'Vite', 'i18next'],
      Backend: ['FastAPI', 'PostgreSQL'],
      Infrastructure: ['Cloudflare R2', 'Render', 'Vercel'],
    },
    learned:
      'Building Altura Group gave me experience planning an entire production platform from public UX to administration, multilingual content, media infrastructure, and deployment.',
    quote: 'A production website is much more than its public-facing pages.',
  },
} as const

export function ProjectDetailsPage() {
  const { slug } = useParams()
  const project = getProjectBySlug(slug)

  if (!project) {
    return <Navigate to="/projects" replace />
  }

  const currentIndex = projects.findIndex((item) => item.slug === project.slug)
  const previousProject =
    projects[(currentIndex - 1 + projects.length) % projects.length]
  const nextProject = projects[(currentIndex + 1) % projects.length]

  const meta =
    projectMeta[project.slug as keyof typeof projectMeta] ??
    projectMeta.bookaify

  return (
    <div className="project-detail-v2">
      <div className="project-detail-v2-top">
        <Link to="/projects" className="project-detail-v2-back">
          <ArrowLeft aria-hidden="true" />
          <span>Back to Projects</span>
        </Link>

        <span className="project-detail-v2-motto">
          Ideas Into Reality
        </span>
      </div>

      <div className="project-detail-v2-hero">
        <div className="project-detail-v2-gallery">
          <div className={`project-gallery-main ${project.accent}`}>
            {project.image ? (
              <img src={project.image} alt={`${project.title} project`} />
            ) : (
              <>
                <div className="project-gallery-grid" />
                <div className="project-gallery-main-glow" />

                <div className="project-gallery-browser">
                  <div className="project-gallery-browser-bar">
                    <span />
                    <span />
                    <span />
                  </div>

                  <div className="project-gallery-browser-content">
                    <div className="project-gallery-sidebar">
                      <i />
                      <i />
                      <i />
                      <i />
                    </div>

                    <div className="project-gallery-dashboard-content">
                      <span className="project-gallery-small-label">
                        {project.title}
                      </span>

                      <strong>
                        {project.slug === 'bookaify'
                          ? 'Good morning, Nurlan 👋'
                          : project.title}
                      </strong>

                      <div className="project-gallery-metrics">
                        <i />
                        <i />
                        <i />
                        <i />
                      </div>

                      <div className="project-gallery-panels">
                        <i />
                        <i />
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="project-gallery-thumbnails">
            {bookaifyGallery.map((item, index) => (
              <button
                type="button"
                className={`project-gallery-thumb ${item.className}${
                  index === 0 ? ' is-active' : ''
                }`}
                key={item.label}
                aria-label={item.label}
              >
                <span>{item.label}</span>
              </button>
            ))}

            <button
              type="button"
              className="project-gallery-thumb project-gallery-more"
              aria-label="More project images"
            >
              <span>+8</span>
            </button>
          </div>
        </div>

        <div className="project-detail-v2-summary">
          <div className="project-detail-v2-meta">
            <span>{meta.type}</span>
            <time>{meta.date}</time>
          </div>

          <h1>{project.title}</h1>

          <h2>{project.description}</h2>

          <div className="project-detail-v2-overview">
            {project.overview.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>

          <div className="project-detail-v2-actions">
            {project.demo ? (
              <a
                href={project.demo}
                target="_blank"
                rel="noreferrer"
                className="project-detail-v2-button is-primary"
              >
                <ExternalLink aria-hidden="true" />
                <span>Live Demo</span>
              </a>
            ) : (
              <span className="project-detail-v2-button is-primary is-disabled">
                <ExternalLink aria-hidden="true" />
                <span>Live Demo</span>
              </span>
            )}

            {project.github ? (
              <a
                href={project.github}
                target="_blank"
                rel="noreferrer"
                className="project-detail-v2-button"
              >
                <SiGithub aria-hidden="true" />
                <span>View Code</span>
              </a>
            ) : (
              <span className="project-detail-v2-button is-disabled">
                <SiGithub aria-hidden="true" />
                <span>View Code</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="project-detail-v2-info-grid">
        <section className="project-detail-v2-card project-features-card">
          <div className="project-detail-v2-card-heading">
            <span className="project-detail-v2-card-icon">
              <Lightbulb aria-hidden="true" />
            </span>
            <h3>Key Features</h3>
          </div>

          <div className="project-detail-v2-feature-list">
            {project.features.map((feature) => (
              <div key={feature}>
                <span>
                  <Check aria-hidden="true" />
                </span>
                <p>{feature}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="project-detail-v2-card project-stack-card">
          <div className="project-detail-v2-card-heading">
            <span className="project-detail-v2-card-icon">
              <Package aria-hidden="true" />
            </span>
            <h3>Tech Stack</h3>
          </div>

          <div className="project-detail-v2-stack">
            {Object.entries(meta.stack).map(([group, technologies]) => (
              <div className="project-detail-v2-stack-group" key={group}>
                <strong>{group}</strong>

                <div>
                  {(technologies as readonly string[]).map((technology) => (
                    <span key={technology}>{technology}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>


      </div>

      <div className="project-detail-v2-navigation">
        <Link
          to={`/projects/${previousProject.slug}`}
          className="project-detail-v2-project-nav"
        >
          <ArrowLeft aria-hidden="true" />

          <div>
            <span>Previous Project</span>
            <strong>{previousProject.title}</strong>
          </div>
        </Link>

        <Link to="/projects" className="project-detail-v2-grid-link">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </Link>

        <Link
          to={`/projects/${nextProject.slug}`}
          className="project-detail-v2-project-nav is-next"
        >
          <div>
            <span>Next Project</span>
            <strong>{nextProject.title}</strong>
          </div>

          <ArrowRight aria-hidden="true" />
        </Link>
      </div>
    </div>
  )
}
