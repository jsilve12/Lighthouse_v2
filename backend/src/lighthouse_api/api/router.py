from fastapi import APIRouter

from lighthouse_api.api.v1.routes import (
    audit,
    auth,
    datasets,
    folders,
    health,
    monitoring,
    pipelines,
    schemas,
    transformations,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(datasets.router)
api_router.include_router(folders.router)
api_router.include_router(schemas.router)
api_router.include_router(transformations.router)
api_router.include_router(pipelines.router)
api_router.include_router(monitoring.router)
api_router.include_router(audit.router)
