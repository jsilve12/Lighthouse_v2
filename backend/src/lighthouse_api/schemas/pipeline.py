import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    dataset_id: uuid.UUID | None = None


class PipelineUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class PipelineResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    dataset_id: uuid.UUID | None
    is_active: bool
    step_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineStepCreate(BaseModel):
    script_version_id: uuid.UUID
    step_order: int = Field(..., ge=0)
    step_name: str = Field(..., min_length=1, max_length=255)
    timeout_seconds: int = Field(300, ge=1, le=3600)
    retry_count: int = Field(0, ge=0, le=5)


class PipelineStepResponse(BaseModel):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    script_version_id: uuid.UUID
    step_order: int
    step_name: str
    timeout_seconds: int
    retry_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StepReorderItem(BaseModel):
    step_id: uuid.UUID
    new_order: int


class StepReorderRequest(BaseModel):
    steps: list[StepReorderItem]


class TriggerRunRequest(BaseModel):
    environment: str = Field(..., pattern=r"^(qa|prod)$")


class PipelineRunResponse(BaseModel):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    environment: str
    status: str
    triggered_by: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    env_snapshot: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunStepLogResponse(BaseModel):
    id: uuid.UUID
    pipeline_run_id: uuid.UUID
    step_id: uuid.UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    log_output: str | None
    rows_affected: int | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunDetailResponse(PipelineRunResponse):
    step_logs: list[PipelineRunStepLogResponse] = Field(default_factory=list)
