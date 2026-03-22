import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SQLScriptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    dataset_id: uuid.UUID | None = None


class SQLScriptUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    dataset_id: uuid.UUID | None = None


class SQLScriptResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    dataset_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SQLScriptVersionCreate(BaseModel):
    major_version: int = Field(..., ge=0)
    minor_version: int = Field(..., ge=0)
    sql_body: str = Field(..., min_length=1)
    change_description: str | None = None
    env_config: dict = Field(default_factory=dict)


class SQLScriptVersionResponse(BaseModel):
    id: uuid.UUID
    script_id: uuid.UUID
    major_version: int
    minor_version: int
    sql_body: str
    change_description: str | None
    env_config: dict
    is_active: bool
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SQLValidateRequest(BaseModel):
    sql_body: str = Field(..., min_length=1)


class SQLValidateResponse(BaseModel):
    valid: bool
    error: str | None = None


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    expires_in_days: int | None = Field(None, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    created_by: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyCreateResponse(ApiKeyResponse):
    key: str  # Only returned on creation
