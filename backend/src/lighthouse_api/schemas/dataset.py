import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    source_type: str = Field(..., pattern=r"^(gcs_json|gcs_csv|gcs_jsonl|gcs_json_gz|delta)$")
    source_config: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    is_financial: bool = False
    is_pii: bool = False


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    source_type: str | None = Field(None, pattern=r"^(gcs_json|gcs_csv|gcs_jsonl|gcs_json_gz|delta)$")
    source_config: dict | None = None
    tags: list[str] | None = None
    is_financial: bool | None = None
    is_pii: bool | None = None


class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    source_type: str
    source_config: dict
    current_major_version: int
    current_minor_version: int
    tags: list
    is_financial: bool
    is_pii: bool
    folder_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int
    page: int
    size: int


class VersionBumpRequest(BaseModel):
    bump_type: str = Field(..., pattern=r"^(major|minor)$")
