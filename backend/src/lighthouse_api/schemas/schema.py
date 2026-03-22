import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SchemaFieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    field_type: str = Field(..., min_length=1, max_length=100)
    nullable: bool = True
    description: str | None = None
    is_encrypted: bool = False
    is_pii: bool = False
    is_financial: bool = False
    parent_field_id: uuid.UUID | None = None
    array_element: bool = False
    sort_order: int = 0
    custom_metadata: dict = Field(default_factory=dict)


class SchemaFieldResponse(BaseModel):
    id: uuid.UUID
    schema_version_id: uuid.UUID
    name: str
    field_type: str
    nullable: bool
    description: str | None
    is_encrypted: bool
    is_pii: bool
    is_financial: bool
    parent_field_id: uuid.UUID | None
    array_element: bool
    sort_order: int
    custom_metadata: dict
    children: list["SchemaFieldResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SchemaVersionCreate(BaseModel):
    major_version: int = Field(..., ge=0)
    minor_version: int = Field(..., ge=0)
    description: str | None = None
    custom_metadata_schema: dict | None = None
    data_location_pattern: str | None = Field(None, max_length=1024)
    fields: list[SchemaFieldCreate] = Field(default_factory=list)


class SchemaVersionUpdate(BaseModel):
    description: str | None = None
    is_active: bool | None = None
    custom_metadata_schema: dict | None = None
    data_location_pattern: str | None = None


class SchemaVersionResponse(BaseModel):
    id: uuid.UUID
    folder_id: uuid.UUID
    major_version: int
    minor_version: int
    description: str | None
    is_active: bool
    custom_metadata_schema: dict | None
    data_location_pattern: str | None
    field_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SchemaVersionDetailResponse(SchemaVersionResponse):
    fields: list[SchemaFieldResponse] = Field(default_factory=list)
