from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ProjectTagInput(BaseModel):
    label: str = Field(min_length=1, max_length=80)


class ProjectTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    display_order: int


class ProjectImageInput(BaseModel):
    media_asset_id: int = Field(gt=0)
    label: str | None = Field(default=None, max_length=120)


class ProjectImageRead(BaseModel):
    id: int
    media_asset_id: int
    label: str | None
    display_order: int
    media_url: str | None = None
    thumbnail_url: str | None = None
    alt_text: str | None = None


class ProjectFeatureInput(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ProjectFeatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    display_order: int


class ProjectTechItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectTechItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_order: int


class ProjectTechGroupInput(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    items: list[ProjectTechItemInput] = Field(default_factory=list)


class ProjectTechGroupRead(BaseModel):
    id: int
    label: str
    display_order: int
    items: list[ProjectTechItemRead]


class ProjectVideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mux_upload_id: str | None
    mux_asset_id: str | None
    mux_playback_id: str | None
    status: str
    duration_seconds: float | None
    aspect_ratio: str | None
    original_filename: str | None
    error_message: str | None

    pending_mux_upload_id: str | None
    pending_mux_asset_id: str | None
    pending_mux_playback_id: str | None
    pending_status: str | None
    pending_duration_seconds: float | None
    pending_aspect_ratio: str | None
    pending_original_filename: str | None
    pending_error_message: str | None

    cleanup_pending: bool
    cleanup_error_message: str | None

    created_at: datetime
    updated_at: datetime


class ProjectWrite(BaseModel):
    slug: str | None = Field(
        default=None,
        max_length=160,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    title: str = Field(default="", max_length=200)
    project_type: str | None = Field(
        default=None,
        max_length=120,
    )
    short_description: str | None = Field(
        default=None,
        max_length=500,
    )
    long_description: str | None = None
    project_date: date | None = None

    cover_media_asset_id: int | None = Field(
        default=None,
        gt=0,
    )

    github_url: HttpUrl | None = None
    show_github_link: bool = False
    demo_url: HttpUrl | None = None

    is_featured: bool = False
    is_published: bool = False

    tags: list[ProjectTagInput] = Field(
        default_factory=list,
    )
    images: list[ProjectImageInput] = Field(
        default_factory=list,
    )
    features: list[ProjectFeatureInput] = Field(
        default_factory=list,
    )
    tech_groups: list[ProjectTechGroupInput] = Field(
        default_factory=list,
    )

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator(
        "project_type",
        "short_description",
        "long_description",
        mode="before",
    )
    @classmethod
    def strip_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator(
        "slug",
        mode="before",
    )
    @classmethod
    def empty_slug_to_none(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator(
        "github_url",
        "demo_url",
        mode="before",
    )
    @classmethod
    def empty_url_to_none(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ProjectCreate(ProjectWrite):
    pass


class ProjectUpdate(ProjectWrite):
    pass


class ProjectRead(BaseModel):
    id: int
    slug: str
    title: str
    project_type: str | None
    short_description: str | None
    long_description: str | None
    project_date: date | None

    cover_media_asset_id: int | None
    cover_url: str | None = None
    cover_thumbnail_url: str | None = None

    github_url: str | None
    show_github_link: bool
    demo_url: str | None

    is_featured: bool
    is_published: bool
    display_order: int

    tags: list[ProjectTagRead]
    images: list[ProjectImageRead]
    features: list[ProjectFeatureRead]
    tech_groups: list[ProjectTechGroupRead]
    video: ProjectVideoRead | None

    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    id: int
    slug: str
    title: str
    project_type: str | None
    short_description: str | None
    project_date: date | None

    cover_media_asset_id: int | None
    cover_url: str | None = None
    cover_thumbnail_url: str | None = None

    github_url: str | None
    show_github_link: bool
    demo_url: str | None

    is_featured: bool
    is_published: bool
    display_order: int

    tags: list[ProjectTagRead]
    technologies: list[str]

    created_at: datetime
    updated_at: datetime


class ProjectList(BaseModel):
    items: list[ProjectListItem]
    total: int
    limit: int
    offset: int


class ProjectOrderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0)


class ProjectReorder(BaseModel):
    items: list[ProjectOrderItem] = Field(min_length=1)


class PublicProjectNavigation(BaseModel):
    slug: str
    title: str


class PublicProjectListItem(BaseModel):
    slug: str
    title: str
    project_type: str
    short_description: str
    project_date: date
    cover_url: str | None
    cover_thumbnail_url: str | None
    github_url: str | None
    demo_url: str | None
    is_featured: bool
    display_order: int
    tags: list[ProjectTagRead]
    technologies: list[str]


class PublicProjectList(BaseModel):
    items: list[PublicProjectListItem]
    total: int


class PublicProjectRead(BaseModel):
    slug: str
    title: str
    project_type: str
    short_description: str
    long_description: str
    project_date: date

    cover_url: str | None
    cover_thumbnail_url: str | None

    github_url: str | None
    demo_url: str | None

    is_featured: bool
    display_order: int

    tags: list[ProjectTagRead]
    images: list[ProjectImageRead]
    features: list[ProjectFeatureRead]
    tech_groups: list[ProjectTechGroupRead]
    video: ProjectVideoRead | None

    previous_project: PublicProjectNavigation | None
    next_project: PublicProjectNavigation | None


class ProjectVideoUploadCreate(BaseModel):
    original_filename: str = Field(
        min_length=1,
        max_length=255,
    )

    @field_validator(
        "original_filename",
        mode="before",
    )
    @classmethod
    def normalize_original_filename(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ProjectVideoUploadResponse(BaseModel):
    project_id: int
    upload_id: str
    upload_url: str
    status: str
