import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lighthouse_api.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from lighthouse_api.models.folder import Folder


class SchemaVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "schema_versions"
    __table_args__ = (UniqueConstraint("folder_id", "major_version", "minor_version", name="uq_schema_versions_folder_version"),)

    folder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    major_version: Mapped[int] = mapped_column(Integer, nullable=False)
    minor_version: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    custom_metadata_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_location_pattern: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="Regex pattern matching GCS paths this schema applies to"
    )

    folder: Mapped["Folder"] = relationship("Folder", back_populates="schema_versions")
    fields: Mapped[list["SchemaField"]] = relationship("SchemaField", back_populates="schema_version", cascade="all, delete-orphan")


class SchemaField(UUIDMixin, Base):
    __tablename__ = "schema_fields"
    __table_args__ = (
        UniqueConstraint("schema_version_id", "name", "parent_field_id", name="uq_schema_fields_version_name_parent"),
        Index("ix_schema_fields_pii", "is_pii", postgresql_where="is_pii = true"),
        Index("ix_schema_fields_financial", "is_financial", postgresql_where="is_financial = true"),
    )

    schema_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schema_versions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(100), nullable=False)
    nullable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_pii: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_financial: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    parent_field_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("schema_fields.id"), nullable=True)
    array_element: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    custom_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at = TimestampMixin.created_at

    schema_version: Mapped["SchemaVersion"] = relationship("SchemaVersion", back_populates="fields")
    children: Mapped[list["SchemaField"]] = relationship("SchemaField", back_populates="parent")
    parent: Mapped["SchemaField | None"] = relationship("SchemaField", back_populates="children", remote_side="SchemaField.id")
