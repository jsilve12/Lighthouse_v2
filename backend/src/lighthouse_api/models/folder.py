import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lighthouse_api.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from lighthouse_api.models.dataset import Dataset
    from lighthouse_api.models.schema import SchemaVersion


class Folder(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("dataset_id", "name", name="uq_folders_dataset_name"),)

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="folders")
    schema_versions: Mapped[list["SchemaVersion"]] = relationship(
        "SchemaVersion", back_populates="folder", cascade="all, delete-orphan"
    )
