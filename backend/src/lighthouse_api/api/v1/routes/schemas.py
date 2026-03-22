import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.database import get_db
from lighthouse_api.models.folder import Folder
from lighthouse_api.models.schema import SchemaField, SchemaVersion
from lighthouse_api.schemas.schema import (
    SchemaFieldCreate,
    SchemaFieldResponse,
    SchemaVersionCreate,
    SchemaVersionDetailResponse,
    SchemaVersionResponse,
    SchemaVersionUpdate,
)

router = APIRouter(tags=["schemas"])


def _build_field_tree(fields: list[SchemaField]) -> list[SchemaFieldResponse]:
    field_map: dict[uuid.UUID, SchemaFieldResponse] = {}
    roots: list[SchemaFieldResponse] = []

    for f in sorted(fields, key=lambda x: x.sort_order):
        resp = SchemaFieldResponse(
            **{c.name: getattr(f, c.name) for c in f.__table__.columns},
            children=[],
        )
        field_map[f.id] = resp

    for f in fields:
        resp = field_map[f.id]
        if f.parent_field_id and f.parent_field_id in field_map:
            field_map[f.parent_field_id].children.append(resp)
        else:
            roots.append(resp)

    return roots


@router.get("/folders/{folder_id}/schemas", response_model=list[SchemaVersionResponse])
async def list_schemas(
    folder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SchemaVersionResponse]:
    folder = (await db.execute(select(Folder).where(Folder.id == folder_id))).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    result = await db.execute(
        select(SchemaVersion)
        .where(SchemaVersion.folder_id == folder_id)
        .order_by(SchemaVersion.major_version.desc(), SchemaVersion.minor_version.desc())
    )
    schemas = list(result.scalars().all())

    items = []
    for s in schemas:
        field_count = (await db.execute(
            select(func.count(SchemaField.id)).where(SchemaField.schema_version_id == s.id)
        )).scalar() or 0
        items.append(SchemaVersionResponse(
            **{c.name: getattr(s, c.name) for c in s.__table__.columns},
            field_count=field_count,
        ))
    return items


@router.post("/folders/{folder_id}/schemas", response_model=SchemaVersionDetailResponse, status_code=201)
async def create_schema(
    folder_id: uuid.UUID,
    body: SchemaVersionCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SchemaVersionDetailResponse:
    folder = (await db.execute(select(Folder).where(Folder.id == folder_id))).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    schema_version = SchemaVersion(
        folder_id=folder_id,
        major_version=body.major_version,
        minor_version=body.minor_version,
        description=body.description,
        custom_metadata_schema=body.custom_metadata_schema,
        data_location_pattern=body.data_location_pattern,
    )
    db.add(schema_version)
    await db.flush()

    created_fields = []
    for field_data in body.fields:
        field = SchemaField(
            schema_version_id=schema_version.id,
            **field_data.model_dump(),
        )
        db.add(field)
        created_fields.append(field)
    await db.flush()

    field_tree = _build_field_tree(created_fields)

    return SchemaVersionDetailResponse(
        **{c.name: getattr(schema_version, c.name) for c in schema_version.__table__.columns},
        field_count=len(created_fields),
        fields=field_tree,
    )


@router.get("/schemas/{schema_id}", response_model=SchemaVersionDetailResponse)
async def get_schema(
    schema_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SchemaVersionDetailResponse:
    result = await db.execute(
        select(SchemaVersion)
        .options(selectinload(SchemaVersion.fields))
        .where(SchemaVersion.id == schema_id)
    )
    schema = result.scalar_one_or_none()
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    field_tree = _build_field_tree(list(schema.fields))

    return SchemaVersionDetailResponse(
        **{c.name: getattr(schema, c.name) for c in schema.__table__.columns},
        field_count=len(schema.fields),
        fields=field_tree,
    )


@router.put("/schemas/{schema_id}", response_model=SchemaVersionResponse)
async def update_schema(
    schema_id: uuid.UUID,
    body: SchemaVersionUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SchemaVersionResponse:
    schema = (await db.execute(select(SchemaVersion).where(SchemaVersion.id == schema_id))).scalar_one_or_none()
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(schema, key, value)
    await db.flush()

    field_count = (await db.execute(
        select(func.count(SchemaField.id)).where(SchemaField.schema_version_id == schema.id)
    )).scalar() or 0

    return SchemaVersionResponse(
        **{c.name: getattr(schema, c.name) for c in schema.__table__.columns},
        field_count=field_count,
    )


@router.get("/schemas/{schema_id}/sensitive-fields", response_model=list[SchemaFieldResponse])
async def get_sensitive_fields(
    schema_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[SchemaFieldResponse]:
    result = await db.execute(
        select(SchemaField).where(
            SchemaField.schema_version_id == schema_id,
            (SchemaField.is_pii.is_(True) | SchemaField.is_encrypted.is_(True) | SchemaField.is_financial.is_(True)),
        )
    )
    fields = list(result.scalars().all())
    return [
        SchemaFieldResponse(**{c.name: getattr(f, c.name) for c in f.__table__.columns}, children=[])
        for f in fields
    ]


@router.get("/schemas/compare")
async def compare_schemas(
    left: uuid.UUID = Query(...),
    right: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    left_result = await db.execute(
        select(SchemaField).where(SchemaField.schema_version_id == left).order_by(SchemaField.sort_order)
    )
    right_result = await db.execute(
        select(SchemaField).where(SchemaField.schema_version_id == right).order_by(SchemaField.sort_order)
    )
    left_fields = {f.name: f for f in left_result.scalars().all()}
    right_fields = {f.name: f for f in right_result.scalars().all()}

    added = [name for name in right_fields if name not in left_fields]
    removed = [name for name in left_fields if name not in right_fields]
    changed = []
    for name in left_fields:
        if name in right_fields:
            lf, rf = left_fields[name], right_fields[name]
            diffs = {}
            for attr in ("field_type", "nullable", "is_pii", "is_encrypted", "is_financial"):
                if getattr(lf, attr) != getattr(rf, attr):
                    diffs[attr] = {"old": getattr(lf, attr), "new": getattr(rf, attr)}
            if diffs:
                changed.append({"field": name, "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}
