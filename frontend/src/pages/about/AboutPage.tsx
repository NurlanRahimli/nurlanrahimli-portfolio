export function AboutPage() {
  return (
    <>
      <div className="content about">
        <div className="title">
          <span>About Me</span>
        </div>

        <div className="row">
          <div className="col col-d-6 col-t-12 col-m-12 border-line-v">
            <div className="text-box">
              <div>
                <strong>Hello! I’m Nurlan Rahimli.</strong>{' '}
                Software Engineer focused on building modern full-stack and
                AI-powered applications. I enjoy creating thoughtful frontend
                experiences, reliable backend systems, and intelligent product
                features.
              </div>
            </div>
          </div>

          <div className="col col-d-6 col-t-12 col-m-12 border-line-v">
            <div className="info-list">
              <ul>
                <li>
                  <strong>
                    <span>Focus:</span>
                  </strong>
                  <span>AI / Full-Stack</span>
                </li>

                <li>
                  <strong>
                    <span>Residence:</span>
                  </strong>
                  <span>USA</span>
                </li>

                <li>
                  <strong>
                    <span>Freelance:</span>
                  </strong>
                  <span>Available</span>
                </li>

                <li>
                  <strong>
                    <span>Location:</span>
                  </strong>
                  <span>California, USA</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="clear" />
        </div>
      </div>

      <div className="content services">
        <div className="title">
          <span>My Services</span>
        </div>

        <div className="row service-items border-line-v">
          <div className="col col-d-6 col-t-6 col-m-12 border-line-h">
            <div className="service-item">
              <div className="icon">
                <svg viewBox="0 0 352 512" aria-hidden="true">
                  <path d="M176 80c-52.94 0-96 43.06-96 96 0 8.84 7.16 16 16 16s16-7.16 16-16c0-35.3 28.72-64 64-64 8.84 0 16-7.16 16-16s-7.16-16-16-16zM96.06 459.17c0 3.15.93 6.22 2.68 8.84l24.51 36.84c2.97 4.46 7.97 7.14 13.32 7.14h78.85c5.36 0 10.36-2.68 13.32-7.14l24.51-36.84c1.74-2.62 2.67-5.7 2.68-8.84l.05-43.18H96.02l.04 43.18zM176 0C73.72 0 0 82.97 0 176c0 44.37 16.45 84.85 43.56 115.78 16.64 18.99 42.74 58.8 52.42 92.16v.06h48v-.12c-.01-4.77-.72-9.51-2.15-14.07-5.59-17.81-22.82-64.77-62.17-109.67-20.54-23.43-31.52-53.15-31.61-84.14-.2-73.64 59.67-128 127.95-128 70.58 0 128 57.42 128 128 0 30.97-11.24 60.85-31.65 84.14-39.11 44.61-56.42 91.47-62.1 109.46a47.507 47.507 0 0 0-2.22 14.3v.1h48v-.05c9.68-33.37 35.78-73.18 52.42-92.16C335.55 260.85 352 220.37 352 176 352 78.8 273.2 0 176 0z" />
                </svg>
              </div>

              <div className="name">
                <span>Full-Stack Development</span>
              </div>

              <div className="desc">
                <div>
                  <p>
                    Building complete web applications from polished frontend
                    interfaces to reliable APIs and backend systems.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="col col-d-6 col-t-6 col-m-12 border-line-h">
            <div className="service-item">
              <div className="icon">
                <svg viewBox="0 0 512 512" aria-hidden="true">
                  <path d="M12.41 148.02l232.94 105.67c6.8 3.09 14.49 3.09 21.29 0l232.94-105.67c16.55-7.51 16.55-32.52 0-40.03L266.65 2.31a25.607 25.607 0 0 0-21.29 0L12.41 107.98c-16.55 7.51-16.55 32.53 0 40.04zm487.18 88.28l-58.09-26.33-161.64 73.27c-7.56 3.43-15.59 5.17-23.86 5.17s-16.29-1.74-23.86-5.17L70.51 209.97l-58.1 26.33c-16.55 7.5-16.55 32.5 0 40l232.94 105.59c6.8 3.08 14.49 3.08 21.29 0L499.59 276.3c16.55-7.5 16.55-32.5 0-40zm0 127.8l-57.87-26.23-161.86 73.37c-7.56 3.43-15.59 5.17-23.86 5.17s-16.29-1.74-23.86-5.17L70.29 337.87 12.41 364.1c-16.55 7.5-16.55 32.5 0 40l232.94 105.59c6.8 3.08 14.49 3.08 21.29 0L499.59 404.1c16.55-7.5 16.55-32.5 0-40z" />
                </svg>
              </div>

              <div className="name">
                <span>AI &amp; ML</span>
              </div>

              <div className="desc">
                <div>
                  <p>
                    Building intelligent product features using machine
                    learning, LLMs, automation, and modern AI systems.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="col col-d-6 col-t-6 col-m-12 border-line-h">
            <div className="service-item">
              <div className="icon">
                <svg viewBox="0 0 576 512" aria-hidden="true">
                  <path d="M528 32H48C21.5 32 0 53.5 0 80v352c0 26.5 21.5 48 48 48h480c26.5 0 48-21.5 48-48V80c0-26.5-21.5-48-48-48zm-352 96c35.3 0 64 28.7 64 64s-28.7 64-64 64-64-28.7-64-64 28.7-64 64-64zm112 236.8c0 10.6-10 19.2-22.4 19.2H86.4C74 384 64 375.4 64 364.8v-19.2c0-31.8 30.1-57.6 67.2-57.6h5c12.3 5.1 25.7 8 39.8 8s27.6-2.9 39.8-8h5c37.1 0 67.2 25.8 67.2 57.6v19.2zM512 312c0 4.4-3.6 8-8 8H360c-4.4 0-8-3.6-8-8v-16c0-4.4 3.6-8 8-8h144c4.4 0 8 3.6 8 8v16zm0-64c0 4.4-3.6 8-8 8H360c-4.4 0-8-3.6-8-8v-16c0-4.4 3.6-8 8-8h144c4.4 0 8 3.6 8 8v16zm0-64c0 4.4-3.6 8-8 8H360c-4.4 0-8-3.6-8-8v-16c0-4.4 3.6-8 8-8h144c4.4 0 8 3.6 8 8v16z" />
                </svg>
              </div>

              <div className="name">
                <span>Backend &amp; APIs</span>
              </div>

              <div className="desc">
                <div>
                  <p>
                    Designing APIs, databases, authentication, background jobs,
                    integrations, and production backend architecture.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="col col-d-6 col-t-6 col-m-12 border-line-h">
            <div className="service-item">
              <div className="icon">
                <svg viewBox="0 0 448 512" aria-hidden="true">
                  <path d="M400 32H48C21.5 32 0 53.5 0 80v352c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V80c0-26.5-21.5-48-48-48zM127 384.5c-5.5 9.6-17.8 12.8-27.3 7.3-9.6-5.5-12.8-17.8-7.3-27.3l14.3-24.7c16.1-4.9 29.3-1.1 39.6 11.4L127 384.5zm138.9-53.9H84c-11 0-20-9-20-20s9-20 20-20h51l65.4-113.2-20.5-35.4c-5.5-9.6-2.2-21.8 7.3-27.3 9.6-5.5 21.8-2.2 27.3 7.3l8.9 15.4 8.9-15.4c5.5-9.6 17.8-12.8 27.3-7.3 9.6 5.5 21.8 2.2 27.3 7.3l-85.8 148.6h62.1c20.2 0 31.5 23.7 22.7 40zm98.1 0h-29l19.6 33.9c5.5 9.6 2.2 21.8-7.3 27.3-9.6 5.5-21.8 2.2-27.3-7.3-32.9-56.9-57.5-99.7-74-128.1-16.7-29-4.8-58 7.1-67.8 13.1 22.7 32.7 56.7 58.9 102h52c11 0 20 9 20 20 0 11.1-9 20-20 20z" />
                </svg>
              </div>

              <div className="name">
                <span>LLM Applications</span>
              </div>

              <div className="desc">
                <div>
                  <p>
                    Developing conversational tools, tool-calling workflows,
                    business automation, and AI-powered assistants.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="clear" />
        </div>
      </div>
    </>
  )
}
