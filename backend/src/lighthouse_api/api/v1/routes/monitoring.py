import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.database import get_db
from lighthouse_api.models.monitoring import AlarmEvent, AlarmRule, RunStatistic
from lighthouse_api.models.pipeline import Pipeline, PipelineRun
from lighthouse_api.schemas.monitoring import (
    AlarmEventResponse,
    AlarmRuleCreate,
    AlarmRuleResponse,
    AlarmRuleUpdate,
    DashboardResponse,
    RunStatisticResponse,
)

router = APIRouter(tags=["monitoring"])


@router.get("/monitoring/dashboard", response_model=DashboardResponse)
async def dashboard(db: AsyncSession = Depends(get_db)) -> DashboardResponse:
    total = (await db.execute(select(func.count(Pipeline.id)))).scalar() or 0
    active = (await db.execute(select(func.count(Pipeline.id)).where(Pipeline.is_active.is_(True)))).scalar() or 0

    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    recent_runs_result = await db.execute(
        select(PipelineRun).where(PipelineRun.created_at >= seven_days_ago).order_by(PipelineRun.created_at.desc()).limit(20)
    )
    recent_runs = [
        {
            "id": str(r.id),
            "pipeline_id": str(r.pipeline_id),
            "environment": r.environment,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_runs_result.scalars().all()
    ]

    total_7d = (await db.execute(select(func.count(PipelineRun.id)).where(PipelineRun.created_at >= seven_days_ago))).scalar() or 0
    success_7d = (
        await db.execute(
            select(func.count(PipelineRun.id)).where(
                PipelineRun.created_at >= seven_days_ago,
                PipelineRun.status == "success",
            )
        )
    ).scalar() or 0
    success_rate = (success_7d / total_7d * 100) if total_7d > 0 else 100.0

    active_alarms = (await db.execute(select(func.count(AlarmEvent.id)).where(AlarmEvent.acknowledged.is_(False)))).scalar() or 0

    return DashboardResponse(
        total_pipelines=total,
        active_pipelines=active,
        recent_runs=recent_runs,
        active_alarms=active_alarms,
        success_rate_7d=round(success_rate, 1),
    )


@router.get("/pipelines/{pipeline_id}/alarms", response_model=list[AlarmRuleResponse])
async def list_alarms(pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[AlarmRuleResponse]:
    result = await db.execute(select(AlarmRule).where(AlarmRule.pipeline_id == pipeline_id).order_by(AlarmRule.name))
    return [AlarmRuleResponse(**{c.name: getattr(a, c.name) for c in a.__table__.columns}) for a in result.scalars().all()]


@router.post("/pipelines/{pipeline_id}/alarms", response_model=AlarmRuleResponse, status_code=201)
async def create_alarm(
    pipeline_id: uuid.UUID,
    body: AlarmRuleCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> AlarmRuleResponse:
    alarm = AlarmRule(pipeline_id=pipeline_id, **body.model_dump())
    db.add(alarm)
    await db.flush()
    return AlarmRuleResponse(**{c.name: getattr(alarm, c.name) for c in alarm.__table__.columns})


@router.put("/alarm-rules/{rule_id}", response_model=AlarmRuleResponse)
async def update_alarm(
    rule_id: uuid.UUID,
    body: AlarmRuleUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> AlarmRuleResponse:
    alarm = (await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))).scalar_one_or_none()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm rule not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(alarm, key, value)
    await db.flush()
    return AlarmRuleResponse(**{c.name: getattr(alarm, c.name) for c in alarm.__table__.columns})


@router.delete("/alarm-rules/{rule_id}", status_code=204)
async def delete_alarm(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    alarm = (await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))).scalar_one_or_none()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm rule not found")
    await db.delete(alarm)


@router.get("/alarm-events", response_model=list[AlarmEventResponse])
async def list_alarm_events(
    acknowledged: bool | None = None,
    pipeline_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[AlarmEventResponse]:
    query = select(AlarmEvent)
    if acknowledged is not None:
        query = query.where(AlarmEvent.acknowledged == acknowledged)
    if pipeline_id:
        query = query.join(AlarmRule).where(AlarmRule.pipeline_id == pipeline_id)
    query = query.order_by(AlarmEvent.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return [AlarmEventResponse(**{c.name: getattr(e, c.name) for c in e.__table__.columns}) for e in result.scalars().all()]


@router.post("/alarm-events/{event_id}/acknowledge")
async def acknowledge_alarm(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    event = (await db.execute(select(AlarmEvent).where(AlarmEvent.id == event_id))).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Alarm event not found")
    event.acknowledged = True
    return {"status": "acknowledged"}


@router.get("/pipeline-runs/{run_id}/statistics", response_model=list[RunStatisticResponse])
async def get_run_statistics(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[RunStatisticResponse]:
    result = await db.execute(select(RunStatistic).where(RunStatistic.pipeline_run_id == run_id).order_by(RunStatistic.created_at))
    return [RunStatisticResponse(**{c.name: getattr(s, c.name) for c in s.__table__.columns}) for s in result.scalars().all()]
