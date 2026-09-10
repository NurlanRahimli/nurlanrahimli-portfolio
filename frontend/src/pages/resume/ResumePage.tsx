import { useState } from 'react'
import { FaAngleRight, FaBriefcase, FaChevronLeft, FaChevronRight, FaGraduationCap } from 'react-icons/fa6'

const experienceItems = [
  {
    date: '2013 - Present',
    name: 'Art Director',
    company: 'Envato Inc.',
    description:
      'Collaborate with creative and development teams on the execution of ideas.',
  },
  {
    date: '2011 - 2012',
    name: 'Team Leader',
    company: 'Google Inc.',
    description:
      'Monitored technical aspects of the web design for projects. What to expect from the design process.',
  },
  {
    date: '2009 - 2010',
    name: 'Senior Designer',
    company: 'Upwork Inc.',
    description:
      'Design website and apps performance using latest technology.',
  },
]

const educationItems = [
  {
    date: '2006 - 2008',
    name: 'Art University',
    company: 'New York',
    description:
      "Bachelor's Degree in Computer Science Technical Institute, Jefferson, Missouri.",
  },
  {
    date: '2005 - 2006',
    name: 'Art Course',
    company: 'Paris',
    description: 'Coursework - Sketch, Adobe Photoshop, Web Design.',
  },
  {
    date: '2004 - 2005',
    name: 'Web Design Course',
    company: 'London',
    description: 'Created and converted Sketch layouts for web design.',
  },
]

const testimonials = [
  {
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    name: 'Helen Floyd',
    company: 'Art Director',
    image: '/images/testi1-184x184.jpg',
  },
  {
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    name: 'Robert Chase',
    company: 'CEO',
    image: '/images/testi2-184x184.jpg',
  },
  {
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    name: 'John Doe',
    company: 'Art Director',
    image: '/images/avatar2-184x184.png',
  },
]

export function ResumePage() {
  const [activeTestimonial, setActiveTestimonial] = useState(0)

  const showPreviousTestimonial = () => {
    setActiveTestimonial((current) =>
      current === 0 ? testimonials.length - 1 : current - 1,
    )
  }

  const showNextTestimonial = () => {
    setActiveTestimonial((current) =>
      current === testimonials.length - 1 ? 0 : current + 1,
    )
  }

  return (
    <div className="resume-page">
      <div className="content custom-text resume-main-heading">
        <div className="title">
          <span>Resume</span>
        </div>
      </div>

      <div className="resume-section-row">
        <div className="resume-section-column">
          <div className="resume-title border-line-h">
            <div className="icon">
              <FaBriefcase aria-hidden="true" />
            </div>

            <div className="name">
              <span>Experience</span>
            </div>
          </div>

          <div className="resume-items line-timeline">
            {experienceItems.map((item, index) => (
              <div
                className={`resume-item border-line-h ${
                  index === 0 ? 'active' : ''
                }`}
                key={`${item.date}-${item.name}`}
              >
                <div className="date">
                  <span>{item.date}</span>
                </div>

                <div className="name">
                  <span>{item.name}</span>
                </div>

                <div className="company">
                  <span>{item.company}</span>
                </div>

                <div className="single-post-text">
                  <div>
                    <p>{item.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="resume-section-column resume-section-column-education">
          <div className="resume-title border-line-h">
            <div className="icon">
              <FaGraduationCap aria-hidden="true" />
            </div>

            <div className="name">
              <span>Education</span>
            </div>
          </div>

          <div className="resume-items line-timeline">
            {educationItems.map((item) => (
              <div
                className="resume-item border-line-h"
                key={`${item.date}-${item.name}`}
              >
                <div className="date">
                  <span>{item.date}</span>
                </div>

                <div className="name">
                  <span>{item.name}</span>
                </div>

                <div className="company">
                  <span>{item.company}</span>
                </div>

                <div className="single-post-text">
                  <div>
                    <p>{item.description}</p>
                  </div>
                </div>

                <a
                  className="lnk lnk-2 resume-certificate-link"
                  href="#"
                  onClick={(event) => event.preventDefault()}
                >
                  <span className="text">Certificate</span>
                  <FaAngleRight aria-hidden="true" />
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="content testimonials">
        <div className="title">
          <span>Testimonials</span>
        </div>

        <div className="testimonial-items">
          <div className="revs-carousel">
            <button
              aria-label="Previous testimonial"
              className="revs-arrow revs-arrow-prev"
              onClick={showPreviousTestimonial}
              type="button"
            >
              <FaChevronLeft aria-hidden="true" />
            </button>

            <div className="revs-slider-window">
              <div
                className="revs-slider-track"
                style={{
                  transform: `translateX(-${activeTestimonial * 100}%)`,
                }}
              >
                {testimonials.map((testimonial) => (
                  <div className="revs-slide" key={testimonial.name}>
                    <div className="revs-item">
                      <div className="text">
                        <div>{testimonial.text}</div>
                      </div>

                      <div className="user">
                        <div className="img">
                          <img
                            src={testimonial.image}
                            alt={testimonial.name}
                          />
                        </div>

                        <div className="info">
                          <div className="name">
                            <span>{testimonial.name}</span>
                          </div>

                          <div className="company">
                            <span>{testimonial.company}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              aria-label="Next testimonial"
              className="revs-arrow revs-arrow-next"
              onClick={showNextTestimonial}
              type="button"
            >
              <FaChevronRight aria-hidden="true" />
            </button>

            <div className="revs-pagination">
              {testimonials.map((testimonial, index) => (
                <button
                  aria-label={`Show testimonial ${index + 1}`}
                  className={`revs-pagination-bullet ${
                    activeTestimonial === index ? 'active' : ''
                  }`}
                  key={testimonial.name}
                  onClick={() => setActiveTestimonial(index)}
                  type="button"
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
