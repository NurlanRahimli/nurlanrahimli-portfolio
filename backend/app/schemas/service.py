from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ServiceIcon = Literal[
    "Lightbulb",
    "Code2",
    "CodeXml",
    "Terminal",
    "Braces",
    "Blocks",
    "Workflow",
    "GitBranch",
    "Database",
    "Server",
    "ServerCog",
    "Cloud",
    "CloudCog",
    "Globe2",
    "MonitorSmartphone",
    "Smartphone",
    "Laptop",
    "AppWindow",
    "BrainCircuit",
    "Bot",
    "Sparkles",
    "Cpu",
    "CircuitBoard",
    "Network",
    "Boxes",
    "Layers3",
    "Gauge",
    "Rocket",
    "ShieldCheck",
    "LockKeyhole",
    "ChartNoAxesCombined",
    "SearchCode",
]


class ServiceWrite(BaseModel):
    icon: ServiceIcon
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    is_active: bool = True

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ServiceCreate(ServiceWrite):
    pass


class ServiceUpdate(ServiceWrite):
    pass


class ServiceRead(BaseModel):
    id: int
    icon: ServiceIcon
    title: str
    description: str
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class ServiceList(BaseModel):
    items: list[ServiceRead]
    total: int
    limit: int
    offset: int


class ServiceOrderItem(BaseModel):
    id: int = Field(gt=0)
    display_order: int = Field(ge=0)


class ServiceReorder(BaseModel):
    items: list[ServiceOrderItem] = Field(min_length=1)


class PublicServiceRead(BaseModel):
    icon: ServiceIcon
    title: str
    description: str


class PublicServiceList(BaseModel):
    items: list[PublicServiceRead]
    total: int
