import { Download, Mail } from 'lucide-react'
import { FaGithub, FaLinkedinIn } from 'react-icons/fa6'
import { Link } from 'react-router-dom'

export function ProfileCard() {
  return (
    <aside className="profile-card">
      <div className="profile-image-placeholder">
        <span>NR</span>
      </div>

      <div className="profile-card-content">
        <p className="profile-eyebrow">Software Engineer</p>

        <h2>Nurlan Rahimli</h2>

        <p className="profile-role">
          Full-Stack Developer
          <span>AI / ML Engineer</span>
        </p>

        <p className="profile-description">
          I build full-stack and AI-powered applications focused on useful,
          polished digital experiences.
        </p>

        <div className="profile-socials">
          <a
            href="https://github.com/NurlanRahimli"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
          >
            <FaGithub size={18} />
          </a>

          <a
            href="https://www.linkedin.com"
            target="_blank"
            rel="noreferrer"
            aria-label="LinkedIn"
          >
            <FaLinkedinIn size={18} />
          </a>

          <Link to="/contact" aria-label="Contact">
            <Mail size={19} />
          </Link>
        </div>

        <div className="profile-actions">
          <button type="button" className="profile-action profile-action-muted">
            <Download size={17} />
            Resume
          </button>

          <Link to="/contact" className="profile-action">
            Contact Me
          </Link>
        </div>
      </div>
    </aside>
  )
}
