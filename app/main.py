from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.config import settings
from app.routes.generate import router as generate_router
from app.routes.youtube import router as youtube_router
from app.routes.review import router as review_router
from app.routes.watchlist import router as watchlist_router
from app.routes.production import router as production_router
from app.routes.providers import router as providers_router
from app.routes.dev_fixtures import router as dev_fixtures_router
from app.routes.story_engine import router as story_engine_router
from app.routes.visual_plan import router as visual_plan_router
from app.routes.founder_dashboard import router as founder_dashboard_router
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    default_response_class=UTF8JSONResponse
)

# Include routers
app.include_router(generate_router)
app.include_router(youtube_router)
app.include_router(review_router)
app.include_router(watchlist_router)
app.include_router(production_router)
app.include_router(providers_router)
app.include_router(dev_fixtures_router)
app.include_router(story_engine_router)
app.include_router(visual_plan_router)
app.include_router(founder_dashboard_router)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting News to Video Pipeline")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down News to Video Pipeline")
