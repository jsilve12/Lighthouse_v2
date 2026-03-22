import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.database import get_db
from lighthouse_api.models.dataset import Dataset
from lighthouse_api.models.folder import Folder
from lighthouse_api.schemas.dataset import (
    DatasetCreate,
    DatasetListResponse,
    DatasetResponse,
    DatasetUpdate,
    VersionBumpRequest,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    search: str | None = None,
    source_type: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DatasetListResponse:
    query = select(Dataset)
    count_query = select(func.count(Dataset.id))

    if search:
        query = query.where(Dataset.name.ilike(f"%{search}%"))
        count_query = count_query.where(Dataset.name.ilike(f"%{search}%"))
    if source_type:
        query = query.where(Dataset.source_type == source_type)
        count_query = count_query.where(Dataset.source_type == source_type)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Dataset.name).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    datasets = list(result.scalars().all())

    items = []
    for ds in datasets:
        folder_count = (await db.execute(
            select(func.count(Folder.id)).where(Folder.dataset_id == ds.id)
        )).scalar() or 0
        items.append(DatasetResponse(
            **{c.name: getattr(ds, c.name) for c in ds.__table__.columns},
            folder_count=folder_count,
        ))

    return DatasetListResponse(items=items, total=total, page=page, size=size)


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    body: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> DatasetResponse:
    dataset = Dataset(**body.model_dump())
    db.add(dataset)
    await db.flush()
    return DatasetResponse(
        **{c.name: getattr(dataset, c.name) for c in dataset.__table__.columns},
        folder_count=0,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    folder_count = (await db.execute(
        select(func.count(Folder.id)).where(Folder.dataset_id == dataset.id)
    )).scalar() or 0

    return DatasetResponse(
        **{c.name: getattr(dataset, c.name) for c in dataset.__table__.columns},
        folder_count=folder_count,
    )


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: uuid.UUID,
    body: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> DatasetResponse:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(dataset, key, value)

    await db.flush()

    folder_count = (await db.execute(
        select(func.count(Folder.id)).where(Folder.dataset_id == dataset.id)
    )).scalar() or 0

    return DatasetResponse(
        **{c.name: getattr(dataset, c.name) for c in dataset.__table__.columns},
        folder_count=folder_count,
    )


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await db.delete(dataset)


@router.post("/{dataset_id}/bump-version", response_model=DatasetResponse)
async def bump_version(
    dataset_id: uuid.UUID,
    body: VersionBumpRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> DatasetResponse:
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if body.bump_type == "major":
        dataset.current_major_version += 1
        dataset.current_minor_version = 0
    else:
        dataset.current_minor_version += 1

    await db.flush()

    folder_count = (await db.execute(
        select(func.count(Folder.id)).where(Folder.dataset_id == dataset.id)
    )).scalar() or 0

    return DatasetResponse(
        **{c.name: getattr(dataset, c.name) for c in dataset.__table__.columns},
        folder_count=folder_count,
    )
