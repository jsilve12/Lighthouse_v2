import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.database import get_db
from lighthouse_api.models.dataset import Dataset
from lighthouse_api.models.folder import Folder
from lighthouse_api.models.schema import SchemaVersion
from lighthouse_api.schemas.folder import FolderCreate, FolderResponse, FolderUpdate

router = APIRouter(tags=["folders"])


@router.get("/datasets/{dataset_id}/folders", response_model=list[FolderResponse])
async def list_folders(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FolderResponse]:
    ds = (await db.execute(select(Dataset).where(Dataset.id == dataset_id))).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    result = await db.execute(
        select(Folder).where(Folder.dataset_id == dataset_id).order_by(Folder.sort_order, Folder.name)
    )
    folders = list(result.scalars().all())

    items = []
    for f in folders:
        schema_count = (await db.execute(
            select(func.count(SchemaVersion.id)).where(SchemaVersion.folder_id == f.id)
        )).scalar() or 0
        items.append(FolderResponse(
            **{c.name: getattr(f, c.name) for c in f.__table__.columns},
            schema_count=schema_count,
        ))
    return items


@router.post("/datasets/{dataset_id}/folders", response_model=FolderResponse, status_code=201)
async def create_folder(
    dataset_id: uuid.UUID,
    body: FolderCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> FolderResponse:
    ds = (await db.execute(select(Dataset).where(Dataset.id == dataset_id))).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    folder = Folder(dataset_id=dataset_id, **body.model_dump())
    db.add(folder)
    await db.flush()
    return FolderResponse(
        **{c.name: getattr(folder, c.name) for c in folder.__table__.columns},
        schema_count=0,
    )


@router.get("/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FolderResponse:
    folder = (await db.execute(select(Folder).where(Folder.id == folder_id))).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    schema_count = (await db.execute(
        select(func.count(SchemaVersion.id)).where(SchemaVersion.folder_id == folder.id)
    )).scalar() or 0

    return FolderResponse(
        **{c.name: getattr(folder, c.name) for c in folder.__table__.columns},
        schema_count=schema_count,
    )


@router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> FolderResponse:
    folder = (await db.execute(select(Folder).where(Folder.id == folder_id))).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(folder, key, value)
    await db.flush()

    schema_count = (await db.execute(
        select(func.count(SchemaVersion.id)).where(SchemaVersion.folder_id == folder.id)
    )).scalar() or 0

    return FolderResponse(
        **{c.name: getattr(folder, c.name) for c in folder.__table__.columns},
        schema_count=schema_count,
    )


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    folder = (await db.execute(select(Folder).where(Folder.id == folder_id))).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    await db.delete(folder)
