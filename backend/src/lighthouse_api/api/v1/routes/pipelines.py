import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.database import get_db
from lighthouse_api.models.pipeline import Pipeline, PipelineRun, PipelineRunStepLog, PipelineStep
from lighthouse_api.schemas.pipeline import (
    PipelineCreate,
    PipelineResponse,
    PipelineRunDetailResponse,
    PipelineRunResponse,
    PipelineRunStepLogResponse,
    PipelineStepCreate,
    PipelineStepResponse,
    PipelineUpdate,
    StepReorderRequest,
    TriggerRunRequest,
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("", response_model=list[PipelineResponse])
async def list_pipelines(db: AsyncSession = Depends(get_db)) -> list[PipelineResponse]:
    result = await db.execute(select(Pipeline).order_by(Pipeline.name))
    pipelines = list(result.scalars().all())
    items = []
    for p in pipelines:
        step_count = (await db.execute(
            select(func.count(PipelineStep.id)).where(PipelineStep.pipeline_id == p.id)
        )).scalar() or 0
        items.append(PipelineResponse(
            **{c.name: getattr(p, c.name) for c in p.__table__.columns},
            step_count=step_count,
        ))
    return items


@router.post("", response_model=PipelineResponse, status_code=201)
async def create_pipeline(
    body: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> PipelineResponse:
    pipeline = Pipeline(**body.model_dump())
    db.add(pipeline)
    await db.flush()
    return PipelineResponse(
        **{c.name: getattr(pipeline, c.name) for c in pipeline.__table__.columns},
        step_count=0,
    )


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> PipelineResponse:
    pipeline = (await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))).scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    step_count = (await db.execute(
        select(func.count(PipelineStep.id)).where(PipelineStep.pipeline_id == pipeline.id)
    )).scalar() or 0
    return PipelineResponse(
        **{c.name: getattr(pipeline, c.name) for c in pipeline.__table__.columns},
        step_count=step_count,
    )


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: uuid.UUID,
    body: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> PipelineResponse:
    pipeline = (await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))).scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(pipeline, key, value)
    await db.flush()
    step_count = (await db.execute(
        select(func.count(PipelineStep.id)).where(PipelineStep.pipeline_id == pipeline.id)
    )).scalar() or 0
    return PipelineResponse(
        **{c.name: getattr(pipeline, c.name) for c in pipeline.__table__.columns},
        step_count=step_count,
    )


@router.delete("/{pipeline_id}", status_code=204)
async def delete_pipeline(
    pipeline_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    pipeline = (await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))).scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    await db.delete(pipeline)


# Steps
@router.get("/{pipeline_id}/steps", response_model=list[PipelineStepResponse])
async def list_steps(pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[PipelineStepResponse]:
    result = await db.execute(
        select(PipelineStep).where(PipelineStep.pipeline_id == pipeline_id).order_by(PipelineStep.step_order)
    )
    return [
        PipelineStepResponse(**{c.name: getattr(s, c.name) for c in s.__table__.columns})
        for s in result.scalars().all()
    ]


@router.post("/{pipeline_id}/steps", response_model=PipelineStepResponse, status_code=201)
async def create_step(
    pipeline_id: uuid.UUID,
    body: PipelineStepCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> PipelineStepResponse:
    step = PipelineStep(pipeline_id=pipeline_id, **body.model_dump())
    db.add(step)
    await db.flush()
    return PipelineStepResponse(**{c.name: getattr(step, c.name) for c in step.__table__.columns})


@router.put("/{pipeline_id}/steps/reorder")
async def reorder_steps(
    pipeline_id: uuid.UUID,
    body: StepReorderRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    for item in body.steps:
        step = (await db.execute(
            select(PipelineStep).where(PipelineStep.id == item.step_id, PipelineStep.pipeline_id == pipeline_id)
        )).scalar_one_or_none()
        if step:
            step.step_order = item.new_order
    await db.flush()
    return {"status": "reordered"}


@router.delete("/pipeline-steps/{step_id}", status_code=204)
async def delete_step(
    step_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    step = (await db.execute(select(PipelineStep).where(PipelineStep.id == step_id))).scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    await db.delete(step)


# Runs
@router.post("/{pipeline_id}/trigger", response_model=PipelineRunResponse)
async def trigger_run(
    pipeline_id: uuid.UUID,
    body: TriggerRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> PipelineRunResponse:
    pipeline = (await db.execute(
        select(Pipeline).options(selectinload(Pipeline.steps)).where(Pipeline.id == pipeline_id)
    )).scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    if not pipeline.steps:
        raise HTTPException(status_code=400, detail="Pipeline has no steps")

    # Collect env snapshot from all script versions
    env_snapshot = {}
    for step in pipeline.steps:
        sv = (await db.execute(
            select(SQLScriptVersion).where(SQLScriptVersion.id == step.script_version_id)
        )).scalar_one_or_none()
        if sv and sv.env_config:
            for var_name, env_map in sv.env_config.items():
                resolved = env_map.get(body.environment, env_map.get("default"))
                if resolved is not None:
                    env_snapshot[var_name] = resolved

    run = PipelineRun(
        pipeline_id=pipeline_id,
        environment=body.environment,
        triggered_by=user["email"],
        env_snapshot=env_snapshot,
    )
    db.add(run)
    await db.flush()

    # Create step logs
    for step in pipeline.steps:
        step_log = PipelineRunStepLog(
            pipeline_run_id=run.id,
            step_id=step.id,
        )
        db.add(step_log)
    await db.flush()

    # Queue background execution
    from lighthouse_api.services.executor import execute_pipeline_run
    background_tasks.add_task(execute_pipeline_run, str(run.id))

    return PipelineRunResponse(**{c.name: getattr(run, c.name) for c in run.__table__.columns})


@router.get("/{pipeline_id}/runs", response_model=list[PipelineRunResponse])
async def list_runs(
    pipeline_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[PipelineRunResponse]:
    result = await db.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline_id)
        .order_by(PipelineRun.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return [
        PipelineRunResponse(**{c.name: getattr(r, c.name) for c in r.__table__.columns})
        for r in result.scalars().all()
    ]


@router.get("/runs/{run_id}", response_model=PipelineRunDetailResponse)
async def get_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> PipelineRunDetailResponse:
    result = await db.execute(
        select(PipelineRun)
        .options(selectinload(PipelineRun.step_logs))
        .where(PipelineRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    step_logs = [
        PipelineRunStepLogResponse(**{c.name: getattr(sl, c.name) for c in sl.__table__.columns})
        for sl in run.step_logs
    ]

    return PipelineRunDetailResponse(
        **{c.name: getattr(run, c.name) for c in run.__table__.columns},
        step_logs=step_logs,
    )


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    run = (await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Run is not cancellable")
    run.status = "cancelled"
    run.completed_at = datetime.now(UTC)
    return {"status": "cancelled"}
