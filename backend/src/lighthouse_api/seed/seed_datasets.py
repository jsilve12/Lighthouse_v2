"""Seed the Lighthouse database with initial dataset, folder, and schema definitions."""
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

from lighthouse_api.core.database import async_session
from lighthouse_api.models.dataset import Dataset
from lighthouse_api.models.folder import Folder
from lighthouse_api.models.schema import SchemaField, SchemaVersion


SEED_DATA_DIR = Path(__file__).parent / "seed_data"


def _covid_dataset() -> dict:
    return {
        "name": "COVID",
        "description": "CDC COVID-19 case surveillance data by state, collected daily",
        "source_type": "gcs_json_gz",
        "source_config": {
            "bucket": "lighthouse_data",
            "prefix_pattern": "covid/collection/{date}/{state}/data.json.gz",
        },
        "is_financial": False,
        "is_pii": False,
        "folders": [{
            "name": "Daily Reports",
            "description": "Daily state-level COVID-19 case and death counts",
            "schemas": [{
                "major_version": 1,
                "minor_version": 0,
                "description": "Initial schema from CDC data",
                "data_location_pattern": r"covid/collection/\d{4}-\d{2}-\d{2}/[A-Z]{2}/data\.json\.gz",
                "fields": [
                    {"name": "submission_date", "field_type": "timestamp", "nullable": False},
                    {"name": "state", "field_type": "string", "nullable": False},
                    {"name": "tot_cases", "field_type": "string", "nullable": True},
                    {"name": "conf_cases", "field_type": "string", "nullable": True},
                    {"name": "prob_cases", "field_type": "string", "nullable": True},
                    {"name": "new_case", "field_type": "string", "nullable": True},
                    {"name": "pnew_case", "field_type": "string", "nullable": True},
                    {"name": "tot_death", "field_type": "string", "nullable": True},
                    {"name": "conf_death", "field_type": "string", "nullable": True},
                    {"name": "prob_death", "field_type": "string", "nullable": True},
                    {"name": "new_death", "field_type": "string", "nullable": True},
                    {"name": "pnew_death", "field_type": "string", "nullable": True},
                    {"name": "created_at", "field_type": "timestamp", "nullable": True},
                    {"name": "consent_cases", "field_type": "string", "nullable": True},
                    {"name": "consent_deaths", "field_type": "string", "nullable": True},
                ],
            }],
        }],
    }


def _cta_dataset() -> dict:
    return {
        "name": "CTA Trains",
        "description": "Chicago Transit Authority real-time train position data",
        "source_type": "gcs_json_gz",
        "source_config": {
            "bucket": "lighthouse_data",
            "prefix_pattern": "cta/trains-collections/{Line}/{timestamp}/data.json.gz",
        },
        "is_financial": False,
        "is_pii": False,
        "folders": [{
            "name": "Train Positions",
            "description": "Real-time train position snapshots by line",
            "schemas": [{
                "major_version": 1,
                "minor_version": 0,
                "description": "CTA Train Tracker API response schema",
                "data_location_pattern": r"cta/trains-collections/\w+/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/data\.json\.gz",
                "fields": [
                    {"name": "ctatt", "field_type": "object", "nullable": False, "sort_order": 0, "_children": [
                        {"name": "tmst", "field_type": "timestamp", "nullable": True, "sort_order": 0},
                        {"name": "errCd", "field_type": "string", "nullable": True, "sort_order": 1},
                        {"name": "errNm", "field_type": "string", "nullable": True, "sort_order": 2},
                        {"name": "route", "field_type": "array", "nullable": True, "sort_order": 3, "_children": [
                            {"name": "route_element", "field_type": "object", "array_element": True, "sort_order": 0, "_children": [
                                {"name": "@name", "field_type": "string", "sort_order": 0},
                                {"name": "train", "field_type": "array", "sort_order": 1, "_children": [
                                    {"name": "train_element", "field_type": "object", "array_element": True, "sort_order": 0, "_children": [
                                        {"name": "rn", "field_type": "string", "sort_order": 0},
                                        {"name": "destSt", "field_type": "string", "sort_order": 1},
                                        {"name": "destNm", "field_type": "string", "sort_order": 2},
                                        {"name": "trDr", "field_type": "string", "sort_order": 3},
                                        {"name": "nextStaId", "field_type": "string", "sort_order": 4},
                                        {"name": "nextStpId", "field_type": "string", "sort_order": 5},
                                        {"name": "nextStaNm", "field_type": "string", "sort_order": 6},
                                        {"name": "prdt", "field_type": "timestamp", "sort_order": 7},
                                        {"name": "arrT", "field_type": "timestamp", "sort_order": 8},
                                        {"name": "isApp", "field_type": "string", "sort_order": 9},
                                        {"name": "isDly", "field_type": "string", "sort_order": 10},
                                        {"name": "flags", "field_type": "string", "nullable": True, "sort_order": 11},
                                        {"name": "lat", "field_type": "float", "sort_order": 12},
                                        {"name": "lon", "field_type": "float", "sort_order": 13},
                                        {"name": "heading", "field_type": "string", "sort_order": 14},
                                    ]},
                                ]},
                            ]},
                        ]},
                    ]},
                ],
            }],
        }],
    }


def _automation_logs_dataset() -> dict:
    event_types = [
        "positions_snapshot", "order_submission", "option_chain_snapshot",
        "portfolio_summary", "loop_result", "close_order_tracked",
        "close_order_released", "close_orders_snapshot", "open_positions_snapshot",
        "open_order_tracked", "recent_orders_snapshot", "portfolio_spread",
        "portfolio_mismatched_contracts", "corporate_calendar_snapshot",
        "corporate_calendar_tradingview_fallback", "close_attribution_filter_summary",
        "close_day_trade_symbol_inventory", "close_skip_existing_broker_order",
        "close_skip_existing_order", "close_skip_foreign_attribution",
        "close_skip_unattributed_spread",
    ]

    common_fields = [
        {"name": "account", "field_type": "string", "is_pii": True, "is_encrypted": True, "description": "Hashed account identifier"},
        {"name": "event", "field_type": "string", "nullable": False, "description": "Event type identifier"},
        {"name": "timestamp", "field_type": "timestamp", "nullable": False},
    ]

    folders = []
    for i, event_type in enumerate(event_types):
        folder_name = event_type.replace("_", " ").title()
        folders.append({
            "name": folder_name,
            "description": f"Schema for {event_type} events",
            "sort_order": i,
            "schemas": [{
                "major_version": 1,
                "minor_version": 0,
                "description": f"Initial schema for {event_type}",
                "data_location_pattern": r"automation-logs/\d{4}-\d{2}-\d{2}\.jsonl",
                "fields": [
                    {**f, "sort_order": j}
                    for j, f in enumerate(common_fields)
                ],
            }],
        })

    return {
        "name": "Automation Logs",
        "description": "Trading automation engine event logs with multiple event types",
        "source_type": "gcs_jsonl",
        "source_config": {
            "bucket": "trading-strategy-datasets-raw",
            "prefix_pattern": "automation-logs/{date}.jsonl",
        },
        "is_financial": True,
        "is_pii": True,
        "folders": folders,
    }


def _eia_dataset() -> dict:
    return {
        "name": "EIA",
        "description": "U.S. Energy Information Administration energy market data",
        "source_type": "gcs_csv",
        "source_config": {
            "bucket": "trading-strategy-datasets-raw",
            "prefix_pattern": "eia/{series_name}/",
        },
        "is_financial": False,
        "is_pii": False,
        "folders": [{
            "name": "Energy Series",
            "description": "EIA energy market time series (gasoline, refinery, rig counts)",
            "schemas": [{
                "major_version": 1,
                "minor_version": 0,
                "description": "Standard EIA observation format",
                "data_location_pattern": r"eia/[\w_]+/observations_\d{8}T\d{6}Z\.csv",
                "fields": [
                    {"name": "period", "field_type": "string", "nullable": False, "sort_order": 0},
                    {"name": "value", "field_type": "float", "nullable": True, "sort_order": 1},
                    {"name": "value_raw", "field_type": "string", "nullable": True, "sort_order": 2},
                    {"name": "series_id", "field_type": "string", "nullable": False, "sort_order": 3},
                    {"name": "series_slug", "field_type": "string", "nullable": False, "sort_order": 4},
                    {"name": "series_name", "field_type": "string", "nullable": True, "sort_order": 5},
                    {"name": "units", "field_type": "string", "nullable": True, "sort_order": 6},
                    {"name": "unit_short", "field_type": "string", "nullable": True, "sort_order": 7},
                    {"name": "updated_at_eia", "field_type": "timestamp", "nullable": True, "sort_order": 8},
                    {"name": "retrieved_at", "field_type": "timestamp", "nullable": False, "sort_order": 9},
                    {"name": "source", "field_type": "string", "nullable": False, "sort_order": 10},
                ],
                "custom_metadata_schema": {
                    "known_series": [
                        "gasoline_days_of_supply", "gasoline_inventories",
                        "gasoline_product_supplied", "refinery_utilization",
                        "shale_rig_count_proxy", "well_service_rig_proxy",
                    ],
                },
            }],
        }],
    }


def _fred_dataset() -> dict:
    return {
        "name": "FRED",
        "description": "Federal Reserve Economic Data - macroeconomic indicators",
        "source_type": "gcs_csv",
        "source_config": {
            "bucket": "trading-strategy-datasets-raw",
            "prefix_pattern": "fred/{series_name}/",
        },
        "is_financial": False,
        "is_pii": False,
        "folders": [{
            "name": "Economic Indicators",
            "description": "FRED macroeconomic time series",
            "schemas": [{
                "major_version": 1,
                "minor_version": 0,
                "description": "Standard FRED observation format",
                "data_location_pattern": r"fred/[\w_]+/observations_\d{8}T\d{6}Z\.csv",
                "fields": [
                    {"name": "date", "field_type": "date", "nullable": False, "sort_order": 0},
                    {"name": "value", "field_type": "float", "nullable": True, "sort_order": 1},
                    {"name": "realtime_start", "field_type": "date", "nullable": True, "sort_order": 2},
                    {"name": "realtime_end", "field_type": "date", "nullable": True, "sort_order": 3},
                    {"name": "series_id", "field_type": "string", "nullable": False, "sort_order": 4},
                ],
                "custom_metadata_schema": {
                    "known_series": [
                        "chicago_fed_national_activity", "consumer_sentiment",
                        "continuing_jobless_claims", "cpi_all_items", "cpi_energy",
                        "cpi_food_at_home", "initial_jobless_claims", "leading_index",
                        "treasury_bill_4w", "treasury_yield_10y", "treasury_yield_2y",
                    ],
                },
            }],
        }],
    }


def _delta_dataset() -> dict:
    return {
        "name": "Trading Strategy Delta",
        "description": "Automation logs converted to Delta format, partitioned by day",
        "source_type": "delta",
        "source_config": {
            "bucket": "trading-strategy-datasets-raw",
            "delta_table_path": "delta/automation_logs/",
            "partition_columns": ["date"],
        },
        "is_financial": True,
        "is_pii": True,
        "folders": [{
            "name": "Automation Logs Delta",
            "description": "Delta-formatted automation logs",
            "schemas": [{
                "major_version": 1,
                "minor_version": 0,
                "description": "Flattened schema for Delta table",
                "data_location_pattern": r"delta/automation_logs/",
                "fields": [
                    {"name": "event_type", "field_type": "string", "nullable": False, "sort_order": 0},
                    {"name": "timestamp", "field_type": "timestamp", "nullable": False, "sort_order": 1},
                    {"name": "date", "field_type": "date", "nullable": False, "description": "Partition key", "sort_order": 2},
                    {"name": "account", "field_type": "string", "is_pii": True, "is_encrypted": True, "sort_order": 3},
                    {"name": "payload", "field_type": "string", "description": "JSON string of event-specific data", "sort_order": 4},
                ],
            }],
        }],
    }


async def _create_fields(session, schema_version_id, fields, parent_id=None):
    for field_data in fields:
        children = field_data.pop("_children", [])
        field_data.pop("sort_order", None)
        sort_order = field_data.get("sort_order", 0)

        field = SchemaField(
            schema_version_id=schema_version_id,
            parent_field_id=parent_id,
            name=field_data.get("name", ""),
            field_type=field_data.get("field_type", "string"),
            nullable=field_data.get("nullable", True),
            description=field_data.get("description"),
            is_encrypted=field_data.get("is_encrypted", False),
            is_pii=field_data.get("is_pii", False),
            is_financial=field_data.get("is_financial", False),
            array_element=field_data.get("array_element", False),
            sort_order=sort_order,
            custom_metadata=field_data.get("custom_metadata", {}),
        )
        session.add(field)
        await session.flush()

        if children:
            await _create_fields(session, schema_version_id, children, parent_id=field.id)


async def seed() -> None:
    datasets_data = [
        _covid_dataset(),
        _cta_dataset(),
        _automation_logs_dataset(),
        _eia_dataset(),
        _fred_dataset(),
        _delta_dataset(),
    ]

    async with async_session() as session:
        for ds_data in datasets_data:
            # Check if already exists
            existing = (await session.execute(
                select(Dataset).where(Dataset.name == ds_data["name"])
            )).scalar_one_or_none()
            if existing:
                print(f"  Dataset '{ds_data['name']}' already exists, skipping")
                continue

            folders_data = ds_data.pop("folders", [])
            dataset = Dataset(
                name=ds_data["name"],
                description=ds_data.get("description"),
                source_type=ds_data["source_type"],
                source_config=ds_data.get("source_config", {}),
                is_financial=ds_data.get("is_financial", False),
                is_pii=ds_data.get("is_pii", False),
            )
            session.add(dataset)
            await session.flush()
            print(f"  Created dataset: {dataset.name}")

            for folder_data in folders_data:
                schemas_data = folder_data.pop("schemas", [])
                folder = Folder(
                    dataset_id=dataset.id,
                    name=folder_data["name"],
                    description=folder_data.get("description"),
                    sort_order=folder_data.get("sort_order", 0),
                )
                session.add(folder)
                await session.flush()
                print(f"    Created folder: {folder.name}")

                for schema_data in schemas_data:
                    fields_data = schema_data.pop("fields", [])
                    schema_version = SchemaVersion(
                        folder_id=folder.id,
                        major_version=schema_data["major_version"],
                        minor_version=schema_data["minor_version"],
                        description=schema_data.get("description"),
                        custom_metadata_schema=schema_data.get("custom_metadata_schema"),
                        data_location_pattern=schema_data.get("data_location_pattern"),
                    )
                    session.add(schema_version)
                    await session.flush()
                    print(f"      Created schema: v{schema_data['major_version']}.{schema_data['minor_version']}")

                    await _create_fields(session, schema_version.id, fields_data)

        await session.commit()
        print("Seed complete!")


def main() -> None:
    print("Seeding Lighthouse database...")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
