import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lighthouse_api.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from lighthouse_api.models.dataset import Dataset
    from lighthouse_api.models.transformation import SQLScriptVersion


class Pipeline(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "pipelines"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    dataset: Mapped["Dataset | None"] = relationship("Dataset", back_populates="pipelines")
    steps: Mapped[list["PipelineStep"]] = relationship(
        "PipelineStep", back_populates="pipeline", cascade="all, delete-orphan", order_by="PipelineStep.step_order"
    )
    runs: Mapped[list["PipelineRun"]] = relationship("PipelineRun", back_populates="pipeline")


class PipelineStep(UUIDMixin, Base):
    __tablename__ = "pipeline_steps"
    __table_args__ = (
        UniqueConstraint("pipeline_id", "step_order", name="uq_pipeline_steps_pipeline_order"),
    )

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    script_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_script_versions.id"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="300")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="steps")
    script_version: Mapped["SQLScriptVersion"] = relationship("SQLScriptVersion")


class PipelineRun(UUIDMixin, Base):
    __tablename__ = "pipeline_runs"
    __table_args__ = (
        Index("ix_pipeline_runs_pipeline_status", "pipeline_id", "status"),
        Index("ix_pipeline_runs_created_at", "created_at"),
    )

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipelines.id"), nullable=False
    )
    environment: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    env_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="runs")
    step_logs: Mapped[list["PipelineRunStepLog"]] = relationship(
        "PipelineRunStepLog", back_populates="pipeline_run", cascade="all, delete-orphan"
    )


class PipelineRunStepLog(UUIDMixin, Base):
    __tablename__ = "pipeline_run_step_logs"

    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False
    )
    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_steps.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    log_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    rows_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pipeline_run: Mapped["PipelineRun"] = relationship("PipelineRun", back_populates="step_logs")
    step: Mapped["PipelineStep"] = relationship("PipelineStep")
