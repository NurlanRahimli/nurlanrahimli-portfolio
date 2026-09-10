export type ProjectDetail = {
  slug: string
  title: string
  eyebrow: string
  description: string
  overview: string[]
  technologies: string[]
  features: string[]
  role: string
  status: string
  year: string
  github?: string
  demo?: string
  image?: string
  accent: string
}

export const projects: ProjectDetail[] = [
  {
    slug: 'bookaify',
    title: 'Bookaify',
    eyebrow: 'AI · FULL-STACK',
    description:
      'AI-powered bookkeeping platform with conversational analytics, receipt processing, OCR, financial insights, and automated workflows.',
    overview: [
      'Bookaify is an AI-powered bookkeeping platform designed to make financial data easier to understand and act on through natural-language interaction.',
      'The platform combines a production FastAPI backend, PostgreSQL, Redis background jobs, receipt processing, OCR, analytics, and an LLM-powered assistant capable of querying and acting on business data.',
    ],
    technologies: [
      'React',
      'FastAPI',
      'PostgreSQL',
      'Redis',
      'OpenAI',
      'Python',
      'SQLAlchemy',
      'Docker',
    ],
    features: [
      'Conversational financial analytics and tool calling',
      'Receipt OCR, categorization, and transaction workflows',
      'Spending reports, summaries, and business insights',
      'Statement mode with filters and transaction navigation',
      'Background processing with Redis and RQ',
      'Secure authenticated backend APIs',
    ],
    role: 'Full-Stack / AI Engineer',
    status: 'Production Project',
    year: '2026',
    accent: 'project-accent-bookaify',
  },
  {
    slug: 'ai-quiz-platform',
    title: 'AI Quiz Platform',
    eyebrow: 'AI · EDUCATION',
    description:
      'Interactive quiz platform with AI explanations, OCR imports, deterministic math validation, analytics, and personalized learning tools.',
    overview: [
      'AI Quiz Platform is a full-stack learning application that combines traditional quiz workflows with AI-powered explanations, OCR imports, analytics, and conversational features.',
      'The project includes secure authentication, quiz ownership, attempt grading, deterministic math validation with SymPy, public discovery, following, password recovery, and AI-generated explanations for incorrect answers.',
    ],
    technologies: [
      'React',
      'TypeScript',
      'FastAPI',
      'PostgreSQL',
      'SymPy',
      'OpenAI',
      'Playwright',
      'Vite',
    ],
    features: [
      'AI-generated explanations for incorrect answers',
      'OCR import from PDF and image files',
      'Deterministic math-answer validation with SymPy',
      'Quiz discovery, profiles, search, and following',
      'Dashboard analytics and performance insights',
      'End-to-end testing with Playwright',
    ],
    role: 'Full-Stack / AI Engineer',
    status: 'Portfolio Project',
    year: '2026',
    accent: 'project-accent-quiz',
  },
  {
    slug: 'altura-group',
    title: 'Altura Group',
    eyebrow: 'FULL-STACK · PRODUCTION',
    description:
      'Production multilingual corporate platform with a complete admin system, project management, media workflows, and cloud infrastructure.',
    overview: [
      'Altura Group is a production corporate website and administration platform built for a construction company operating across multiple regions.',
      'The system includes multilingual public pages, project and service management, partner and certification workflows, media uploads, website-content management, and cloud-hosted infrastructure.',
    ],
    technologies: [
      'React',
      'TypeScript',
      'FastAPI',
      'PostgreSQL',
      'Cloudflare R2',
      'Vercel',
      'Render',
      'i18next',
    ],
    features: [
      'Multilingual public website in English, Azerbaijani, and Russian',
      'Full admin portal for projects, services, and content',
      'Multiple image uploads with cover selection and reordering',
      'Cloudflare R2 media storage and optimized previews',
      'Dynamic website content and regional presence management',
      'Production deployment with Vercel and Render',
    ],
    role: 'Full-Stack Engineer',
    status: 'Production Website',
    year: '2026',
    accent: 'project-accent-altura',
  },
]

export function getProjectBySlug(slug?: string) {
  return projects.find((project) => project.slug === slug)
}
