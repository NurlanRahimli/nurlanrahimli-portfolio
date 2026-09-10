import { Download, Send } from 'lucide-react'
import { FaGithub, FaLinkedinIn } from 'react-icons/fa6'
import { Link } from 'react-router-dom'

export function ProfileCard() {
  return (
    <aside className="ryancv-card-started">
      <div className="ryancv-card-backdrop" />

      <div className="ryancv-profile">
        <div className="ryancv-profile-content">
          <div className="ryancv-profile-slide">
            <img
              className="ryancv-profile-image"
              src="/profile-assets/ryancv-profile.jpg"
              alt=""
            />

            <div className="ryancv-profile-image-overlay" />

            <img
              className="ryancv-rprof-before"
              src="/profile-assets/profile-shape-before.svg"
              alt=""
              aria-hidden="true"
            />

            <img
              className="ryancv-rprof-after"
              src="/profile-assets/profile-shape-after.svg"
              alt=""
              aria-hidden="true"
            />
          </div>

          <div className="ryancv-profile-identity">
            <h1>Nurlan Rahimli</h1>
            <p>Software Engineer</p>

            <div className="ryancv-profile-socials">
              <a
                href="https://github.com/NurlanRahimli"
                target="_blank"
                rel="noreferrer"
                aria-label="GitHub"
              >
                <FaGithub />
              </a>

              <a
                href="https://www.linkedin.com"
                target="_blank"
                rel="noreferrer"
                aria-label="LinkedIn"
              >
                <FaLinkedinIn />
              </a>
            </div>
          </div>
        </div>

        <div className="ryancv-profile-actions">
          <button type="button">
            <span>Download CV</span>
            <Download size={16} />
          </button>

          <Link to="/contact">
            <span>Contact Me</span>
            <Send size={16} />
          </Link>
        </div>
      </div>
    </aside>
  )
}
