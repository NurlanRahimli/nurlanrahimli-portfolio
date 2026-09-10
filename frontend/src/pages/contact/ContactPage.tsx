import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowRight,
  Mail,
  MapPin,
  Phone,
  Send,
  UserRound,
  Zap,
} from 'lucide-react'
import { SiGithub } from 'react-icons/si'
import { FaLinkedin } from 'react-icons/fa'

const contactDetails = {
  email: 'nurlanrahimli@gmail.com',
  phone: '+1 (000) 000-0000',
  location: 'Sacramento, California',
  linkedin: 'linkedin.com/in/nurlan-rahimli',
  linkedinUrl: 'https://www.linkedin.com',
  github: 'github.com/NurlanRahimli',
  githubUrl: 'https://github.com/NurlanRahimli',
}

export function ContactPage() {
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitted(true)

    window.setTimeout(() => {
      setSubmitted(false)
    }, 3500)
  }

  return (
    <div className="contact-page-v2">
      <div className="contact-topbar">
        <span className="contact-topbar-line" />
        <span>Ideas Into Reality</span>
      </div>

      <section className="contact-hero">
        <div className="contact-hero-copy">
          <span className="contact-kicker">
            <i />
            Let&apos;s Connect
          </span>

          <h1>
            Get In <span>Touch</span>
          </h1>

          <p>
            Have a project in mind, a question, or just want to say hello?
            <br />
            I&apos;d love to hear from you.
          </p>
        </div>

        <div className="contact-hero-visual">
          <div className="contact-globe">
            <span className="contact-globe-ring contact-globe-ring-one" />
            <span className="contact-globe-ring contact-globe-ring-two" />
            <span className="contact-globe-ring contact-globe-ring-three" />
            <span className="contact-globe-axis contact-globe-axis-one" />
            <span className="contact-globe-axis contact-globe-axis-two" />

            <span className="contact-globe-dot" />

            <div className="contact-globe-location">
              <span>Based in Sacramento, California</span>
              <span>Open to remote work worldwide</span>
            </div>
          </div>

          <div className="contact-stats">
            <div>
              <strong>03+</strong>
              <span>Years of Experience</span>
            </div>

            <div>
              <strong>10+</strong>
              <span>Projects Built</span>
            </div>

            <div>
              <strong>100%</strong>
              <span>Commitment to Quality</span>
            </div>
          </div>
        </div>
      </section>

      <section className="contact-main-grid">
        <div className="contact-panel contact-form-panel">
          <div className="contact-panel-heading">
            <span className="contact-panel-icon">
              <Send aria-hidden="true" />
            </span>

            <div>
              <h2>Send a Message</h2>
            </div>
          </div>

          <p className="contact-panel-intro">
            Fill out the form below and I&apos;ll get back to you as soon as
            possible.
          </p>

          <form className="contact-form" onSubmit={handleSubmit}>
            <div className="contact-form-row">
              <label>
                <span>Your Name</span>
                <input
                  type="text"
                  name="name"
                  placeholder="John Doe"
                  required
                />
              </label>

              <label>
                <span>Your Email</span>
                <input
                  type="email"
                  name="email"
                  placeholder="john@example.com"
                  required
                />
              </label>
            </div>

            <label>
              <span>Subject</span>
              <input
                type="text"
                name="subject"
                placeholder="Project Inquiry"
                required
              />
            </label>

            <label>
              <span>Message</span>
              <textarea
                name="message"
                placeholder="Tell me about your project, idea, or question..."
                rows={6}
                required
              />
            </label>

            <button type="submit" className="contact-submit">
              <Send aria-hidden="true" />
              <span>{submitted ? 'Message Ready' : 'Send Message'}</span>
            </button>

            {submitted && (
              <p className="contact-submit-note">
                The form design is ready. We&apos;ll connect actual message
                delivery when we build the backend.
              </p>
            )}
          </form>
        </div>

        <div className="contact-panel contact-info-panel">
          <div className="contact-panel-heading">
            <span className="contact-panel-icon">
              <UserRound aria-hidden="true" />
            </span>

            <div>
              <h2>Contact Information</h2>
            </div>
          </div>

          <p className="contact-panel-intro">
            Feel free to reach out through any of the channels below.
          </p>

          <div className="contact-info-list">
            <a
              href={`mailto:${contactDetails.email}`}
              className="contact-info-item"
            >
              <span className="contact-info-icon">
                <Mail aria-hidden="true" />
              </span>

              <div className="contact-info-copy">
                <span>Email</span>
                <strong>{contactDetails.email}</strong>
              </div>

              <span className="contact-info-action">
                Send an email
                <ArrowRight aria-hidden="true" />
              </span>
            </a>

            <a
              href={`tel:${contactDetails.phone.replace(/[^\d+]/g, '')}`}
              className="contact-info-item"
            >
              <span className="contact-info-icon">
                <Phone aria-hidden="true" />
              </span>

              <div className="contact-info-copy">
                <span>Phone</span>
                <strong>{contactDetails.phone}</strong>
              </div>

              <span className="contact-info-action">
                Call me
                <ArrowRight aria-hidden="true" />
              </span>
            </a>

            <a
              href="https://www.google.com/maps/search/?api=1&query=Sacramento%2C%20California"
              target="_blank"
              rel="noreferrer"
              className="contact-info-item"
            >
              <span className="contact-info-icon">
                <MapPin aria-hidden="true" />
              </span>

              <div className="contact-info-copy">
                <span>Location</span>
                <strong>{contactDetails.location}</strong>
              </div>

              <span className="contact-info-action">
                View on map
                <ArrowRight aria-hidden="true" />
              </span>
            </a>

            <a
              href={contactDetails.linkedinUrl}
              target="_blank"
              rel="noreferrer"
              className="contact-info-item"
            >
              <span className="contact-info-icon">
                <FaLinkedin aria-hidden="true" />
              </span>

              <div className="contact-info-copy">
                <span>LinkedIn</span>
                <strong>{contactDetails.linkedin}</strong>
              </div>

              <span className="contact-info-action">
                Visit profile
                <ArrowRight aria-hidden="true" />
              </span>
            </a>

            <a
              href={contactDetails.githubUrl}
              target="_blank"
              rel="noreferrer"
              className="contact-info-item"
            >
              <span className="contact-info-icon">
                <SiGithub aria-hidden="true" />
              </span>

              <div className="contact-info-copy">
                <span>GitHub</span>
                <strong>{contactDetails.github}</strong>
              </div>

              <span className="contact-info-action">
                Visit profile
                <ArrowRight aria-hidden="true" />
              </span>
            </a>
          </div>
        </div>
      </section>

      <section className="contact-closing">
        <div className="contact-closing-main">
          <div className="contact-panel-heading">
            <span className="contact-panel-icon">
              <Zap aria-hidden="true" />
            </span>

            <div>
              <h2>Let&apos;s Build Something Meaningful</h2>
            </div>
          </div>

          <p>
            I&apos;m always open to new opportunities, collaborations, and
            interesting projects.
            <br />
            Whether you have a specific idea or just want to chat, feel free to
            reach out.
          </p>
        </div>

        <div className="contact-closing-quote">
          <span className="contact-quote-mark">“</span>

          <div>
            <p>Good software comes from good conversations.</p>
            <span>— Nurlan Rahimli</span>
          </div>
        </div>
      </section>
    </div>
  )
}
