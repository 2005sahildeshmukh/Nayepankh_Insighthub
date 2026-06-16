from fastapi import APIRouter
from app.api.routes import workspaces, datasets, standard_fields, health
from app.api.routes import data_profiling, data_cleaning, analytics, ml, intelligence

api_router = APIRouter()

api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(datasets.router)
api_router.include_router(standard_fields.router)
api_router.include_router(data_profiling.router, tags=["data-profiling"])
api_router.include_router(data_cleaning.router, tags=["data-cleaning"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(ml.router, tags=["ml"])
api_router.include_router(intelligence.router, tags=["intelligence"])

