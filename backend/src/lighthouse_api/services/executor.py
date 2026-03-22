import uuid
from datetime import UTC, datetime

import duckdb
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from lighthouse_api.core.database import async_session
from lighthouse_api.models.monitoring import AlarmEvent, AlarmRule, RunStatistic
from lighthouse_api.models.pipeline import PipelineRun, PipelineStep
from lighthouse_api.models.transformation import SQLScriptVersion

logger = structlog.get_logger()


async def execute_pipeline_run(run_id: str) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PipelineRun).options(selectinload(PipelineRun.step_logs)).where(PipelineRun.id == uuid.UUID(run_id))
        )
        run = result.scalar_one_or_none()
        if not run:
            logger.error("Pipeline run not found", run_id=run_id)
            return

        run.status = "running"
        run.started_at = datetime.now(UTC)
        await session.commit()

        # Get ordered steps
        steps_result = await session.execute(
            select(PipelineStep).where(PipelineStep.pipeline_id == run.pipeline_id).order_by(PipelineStep.step_order)
        )
        steps = list(steps_result.scalars().all())

        conn = duckdb.connect(":memory:")
        try:
            for step in steps:
                step_log = None
                for sl in run.step_logs:
                    if sl.step_id == step.id:
                        step_log = sl
                        break

                if not step_log:
                    continue

                # Check if run was cancelled
                await session.refresh(run)
                if run.status == "cancelled":
                    step_log.status = "skipped"
                    await session.commit()
                    continue

                step_log.status = "running"
                step_log.started_at = datetime.now(UTC)
                await session.commit()

                # Get SQL body
                sv = (
                    await session.execute(select(SQLScriptVersion).where(SQLScriptVersion.id == step.script_version_id))
                ).scalar_one_or_none()

                if not sv:
                    step_log.status = "failed"
                    step_log.error_message = "Script version not found"
                    step_log.completed_at = datetime.now(UTC)
                    await session.commit()
                    continue

                # Substitute environment variables
                sql = sv.sql_body
                for var_name, var_value in run.env_snapshot.items():
                    sql = sql.replace(f"${{{var_name}}}", str(var_value))
                    sql = sql.replace(f":{var_name}", str(var_value))

                try:
                    result_data = conn.execute(sql)
                    rows = result_data.fetchall() if result_data.description else []
                    rows_affected = len(rows)

                    step_log.status = "success"
                    step_log.rows_affected = rows_affected
                    step_log.log_output = f"Executed successfully. Rows: {rows_affected}"
                    step_log.completed_at = datetime.now(UTC)

                    # Record statistics
                    stat = RunStatistic(
                        pipeline_run_id=run.id,
                        step_id=step.id,
                        metric_name="row_count",
                        metric_value=float(rows_affected),
                    )
                    session.add(stat)
                    await session.commit()

                except duckdb.Error as e:
                    step_log.status = "failed"
                    step_log.error_message = str(e)
                    step_log.completed_at = datetime.now(UTC)
                    await session.commit()

                    run.status = "failed"
                    run.error_message = f"Step '{step.step_name}' failed: {e}"
                    run.completed_at = datetime.now(UTC)
                    await session.commit()

                    # Mark remaining steps as skipped
                    for remaining_sl in run.step_logs:
                        if remaining_sl.status == "pending":
                            remaining_sl.status = "skipped"
                    await session.commit()
                    break
            else:
                # All steps completed successfully
                run.status = "success"
                run.completed_at = datetime.now(UTC)
                await session.commit()

                # Evaluate alarms
                await _evaluate_alarms(session, run)

        except Exception as e:
            logger.error("Pipeline execution error", run_id=run_id, error=str(e))
            run.status = "failed"
            run.error_message = f"Execution error: {e}"
            run.completed_at = datetime.now(UTC)
            await session.commit()
        finally:
            conn.close()


async def _evaluate_alarms(session, run: PipelineRun) -> None:
    alarms_result = await session.execute(
        select(AlarmRule).where(
            AlarmRule.pipeline_id == run.pipeline_id,
            AlarmRule.is_active.is_(True),
        )
    )
    alarms = list(alarms_result.scalars().all())

    for alarm in alarms:
        stats_result = await session.execute(
            select(RunStatistic).where(
                RunStatistic.pipeline_run_id == run.id,
                RunStatistic.metric_name == alarm.metric_name,
            )
        )
        current_stats = list(stats_result.scalars().all())
        if not current_stats:
            continue

        current_value = current_stats[0].metric_value

        triggered = False
        if alarm.condition == "gt" and current_value > alarm.threshold:
            triggered = True
        elif alarm.condition == "lt" and current_value < alarm.threshold:
            triggered = True
        elif alarm.condition == "gte" and current_value >= alarm.threshold:
            triggered = True
        elif alarm.condition == "lte" and current_value <= alarm.threshold:
            triggered = True
        elif alarm.condition == "deviation_pct":
            # Compare against average of lookback runs
            history_result = await session.execute(
                select(RunStatistic)
                .join(PipelineRun)
                .where(
                    PipelineRun.pipeline_id == run.pipeline_id,
                    PipelineRun.id != run.id,
                    PipelineRun.status == "success",
                    RunStatistic.metric_name == alarm.metric_name,
                )
                .order_by(PipelineRun.created_at.desc())
                .limit(alarm.lookback_runs)
            )
            history = list(history_result.scalars().all())
            if history:
                avg = sum(h.metric_value for h in history) / len(history)
                if avg > 0:
                    deviation = abs(current_value - avg) / avg * 100
                    if deviation > alarm.threshold:
                        triggered = True

        if triggered:
            event = AlarmEvent(
                alarm_rule_id=alarm.id,
                pipeline_run_id=run.id,
                triggered_value=current_value,
                message=f"Alarm '{alarm.name}': {alarm.metric_name} = {current_value} (threshold: {alarm.condition} {alarm.threshold})",
            )
            session.add(event)

    await session.commit()
