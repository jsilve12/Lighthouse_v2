import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AlarmRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    metric_name: str = Field(..., min_length=1, max_length=255)
    condition: str = Field(..., pattern=r"^(gt|lt|gte|lte|deviation_pct|schema_drift)$")
    threshold: float
    lookback_runs: int = Field(5, ge=1, le=100)


class AlarmRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    metric_name: str | None = None
    condition: str | None = Field(None, pattern=r"^(gt|lt|gte|lte|deviation_pct|schema_drift)$")
    threshold: float | None = None
    lookback_runs: int | None = Field(None, ge=1, le=100)
    is_active: bool | None = None


class AlarmRuleResponse(BaseModel):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    name: str
    metric_name: str
    condition: str
    threshold: float
    lookback_runs: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlarmEventResponse(BaseModel):
    id: uuid.UUID
    alarm_rule_id: uuid.UUID
    pipeline_run_id: uuid.UUID
    triggered_value: float
    message: str
    acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RunStatisticResponse(BaseModel):
    id: uuid.UUID
    pipeline_run_id: uuid.UUID
    step_id: uuid.UUID | None
    metric_name: str
    metric_value: float
    metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    total_pipelines: int
    active_pipelines: int
    recent_runs: list[dict]
    active_alarms: int
    success_rate_7d: float
