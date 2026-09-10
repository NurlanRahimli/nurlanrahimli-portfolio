import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowUpRight,
  ExternalLink,
  Search,
} from 'lucide-react'
import { SiGithub } from 'react-icons/si'

import { projects } from './projectData'

export function ProjectsPage() {
  const [query, setQuery] = useState('')

  const filteredProjects = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    if (!normalizedQuery) {
      return projects
    }

    return projects.filter((project) => {
      const searchableText = [
        project.title,
        project.description,
        ...project.technologies,
      ]
        .join(' ')
        .toLowerCase()

      return searchableText.includes(normalizedQuery)
    })
  }, [query])

  return (
    <>
      <div className="content projects-content">
        <div className="title">
          <span>Projects</span>
        </div>

        <div className="projects-toolbar">
          <div className="projects-toolbar-copy">
            <span className="projects-count">
              {filteredProjects.length.toString().padStart(2, '0')}
            </span>
            <span className="projects-count-label">
              Selected projects
            </span>
          </div>

          <label className="projects-search">
            <Search aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search projects..."
              aria-label="Search projects"
            />
          </label>
        </div>

        {filteredProjects.length > 0 ? (
          <div className="projects-grid">
            {filteredProjects.map((project, index) => (
              <article className="project-card" key={project.title}>
                <div className={`project-preview ${project.accent}`}>
                  {project.image ? (
                    <img src={project.image} alt="" />
                  ) : (
                    <>
                      <div className="project-preview-grid" />
                      <div className="project-preview-glow" />

                      <div className="project-preview-content">
                        <span className="project-preview-number">
                          {String(index + 1).padStart(2, '0')}
                        </span>

                        <span className="project-preview-name">
                          {project.title}
                        </span>
                      </div>
                    </>
                  )}
                </div>

                <div className="project-card-body">
                  <Link
                    to={`/projects/${project.slug}`}
                    className="project-card-heading project-card-link"
                  >
                    <div>
                      <span className="project-eyebrow">
                        {project.eyebrow}
                      </span>

                      <h2>{project.title}</h2>
                    </div>

                    <ArrowUpRight
                      className="project-heading-arrow"
                      aria-hidden="true"
                    />
                  </Link>

                  <p className="project-description">
                    {project.description}
                  </p>

                  <div className="project-technologies">
                    {project.technologies.map((technology) => (
                      <span key={technology}>{technology}</span>
                    ))}
                  </div>
                </div>

                <div className="project-card-actions">
                  {project.github ? (
                    <a
                      href={project.github}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <SiGithub aria-hidden="true" />
                      <span>Code</span>
                    </a>
                  ) : (
                    <span className="project-action-disabled">
                      <SiGithub aria-hidden="true" />
                      <span>Code</span>
                    </span>
                  )}

                  {project.demo ? (
                    <a
                      href={project.demo}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <ExternalLink aria-hidden="true" />
                      <span>Live Demo</span>
                    </a>
                  ) : (
                    <span className="project-action-disabled">
                      <ExternalLink aria-hidden="true" />
                      <span>Live Demo</span>
                    </span>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="projects-empty">
            <Search aria-hidden="true" />
            <strong>No projects found</strong>
            <span>Try another project name or technology.</span>
          </div>
        )}
      </div>
    </>
  )
}
