import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lighthouse_api.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from lighthouse_api.models.folder import Folder
    from lighthouse_api.models.pipeline import Pipeline
    from lighthouse_api.models.transformation import SQLScript


class Dataset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    current_major_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    current_minor_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    is_financial: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_pii: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    folders: Mapped[list["Folder"]] = relationship("Folder", back_populates="dataset", cascade="all, delete-orphan")
    scripts: Mapped[list["SQLScript"]] = relationship("SQLScript", back_populates="dataset")
    pipelines: Mapped[list["Pipeline"]] = relationship("Pipeline", back_populates="dataset")
