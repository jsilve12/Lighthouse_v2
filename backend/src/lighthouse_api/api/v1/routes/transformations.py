import uuid

import duckdb
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.database import get_db
from lighthouse_api.models.transformation import SQLScript, SQLScriptVersion
from lighthouse_api.schemas.transformation import (
    SQLScriptCreate,
    SQLScriptResponse,
    SQLScriptUpdate,
    SQLScriptVersionCreate,
    SQLScriptVersionResponse,
    SQLValidateResponse,
)

router = APIRouter(prefix="/scripts", tags=["transformations"])


@router.get("", response_model=list[SQLScriptResponse])
async def list_scripts(db: AsyncSession = Depends(get_db)) -> list[SQLScriptResponse]:
    result = await db.execute(select(SQLScript).order_by(SQLScript.name))
    return [SQLScriptResponse(**{c.name: getattr(s, c.name) for c in s.__table__.columns}) for s in result.scalars().all()]


@router.post("", response_model=SQLScriptResponse, status_code=201)
async def create_script(
    body: SQLScriptCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SQLScriptResponse:
    script = SQLScript(**body.model_dump())
    db.add(script)
    await db.flush()
    return SQLScriptResponse(**{c.name: getattr(script, c.name) for c in script.__table__.columns})


@router.get("/{script_id}", response_model=SQLScriptResponse)
async def get_script(script_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SQLScriptResponse:
    script = (await db.execute(select(SQLScript).where(SQLScript.id == script_id))).scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return SQLScriptResponse(**{c.name: getattr(script, c.name) for c in script.__table__.columns})


@router.put("/{script_id}", response_model=SQLScriptResponse)
async def update_script(
    script_id: uuid.UUID,
    body: SQLScriptUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SQLScriptResponse:
    script = (await db.execute(select(SQLScript).where(SQLScript.id == script_id))).scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(script, key, value)
    await db.flush()
    return SQLScriptResponse(**{c.name: getattr(script, c.name) for c in script.__table__.columns})


@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    script = (await db.execute(select(SQLScript).where(SQLScript.id == script_id))).scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    await db.delete(script)


@router.get("/{script_id}/versions", response_model=list[SQLScriptVersionResponse])
async def list_versions(script_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[SQLScriptVersionResponse]:
    result = await db.execute(
        select(SQLScriptVersion)
        .where(SQLScriptVersion.script_id == script_id)
        .order_by(SQLScriptVersion.major_version.desc(), SQLScriptVersion.minor_version.desc())
    )
    return [SQLScriptVersionResponse(**{c.name: getattr(v, c.name) for c in v.__table__.columns}) for v in result.scalars().all()]


@router.post("/{script_id}/versions", response_model=SQLScriptVersionResponse, status_code=201)
async def create_version(
    script_id: uuid.UUID,
    body: SQLScriptVersionCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SQLScriptVersionResponse:
    script = (await db.execute(select(SQLScript).where(SQLScript.id == script_id))).scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    version = SQLScriptVersion(
        script_id=script_id,
        created_by=user["email"],
        **body.model_dump(),
    )
    db.add(version)
    await db.flush()
    return SQLScriptVersionResponse(**{c.name: getattr(version, c.name) for c in version.__table__.columns})


@router.get("/versions/{version_id}", response_model=SQLScriptVersionResponse)
async def get_version(version_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SQLScriptVersionResponse:
    version = (await db.execute(select(SQLScriptVersion).where(SQLScriptVersion.id == version_id))).scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return SQLScriptVersionResponse(**{c.name: getattr(version, c.name) for c in version.__table__.columns})


@router.post("/versions/{version_id}/validate", response_model=SQLValidateResponse)
async def validate_sql(version_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SQLValidateResponse:
    version = (await db.execute(select(SQLScriptVersion).where(SQLScriptVersion.id == version_id))).scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    try:
        conn = duckdb.connect(":memory:")
        conn.execute(f"EXPLAIN {version.sql_body}")
        conn.close()
        return SQLValidateResponse(valid=True)
    except duckdb.Error as e:
        return SQLValidateResponse(valid=False, error=str(e))
