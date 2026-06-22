from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.router import router as auth_router
from app.modules.biometrics.router import router as biometrics_router
from app.modules.health.router import router as health_router
from app.modules.passengers.router import router as passengers_router
from app.modules.sync.router import admin_router as sync_admin_router
from app.modules.sync.router import router as sync_router
from app.modules.tickets.router import router as tickets_router
from app.modules.validations.router import router as validations_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    yield


def _iter_api_routes(routes):
    """
    Recursively flattens `app.routes` into the underlying `APIRoute`
    objects (the ones with `.dependant`/`.path`/`.methods`).

    Needed because newer FastAPI/Starlette versions wrap routes added via
    `include_router()` in an internal `_IncludedRouter` proxy for lazy
    matching — the real `APIRoute` list lives at
    `_IncludedRouter.original_router.routes`. Falling back to a generic
    `.routes` attribute keeps this working for plain `APIRouter`/`Mount`
    nesting on older FastAPI versions too.
    """
    for route in routes:
        if hasattr(route, "dependant"):
            yield route
        elif hasattr(route, "original_router"):
            yield from _iter_api_routes(route.original_router.routes)
        elif hasattr(route, "routes"):
            yield from _iter_api_routes(route.routes)


def _dependant_requires_bearer_auth(dependant) -> bool:
    """
    Walks a route's dependency tree looking for `get_current_user` /
    `require_admin` at any depth (the latter itself depends on the former).
    `auth/login`, `health/*` and `sync/*` (device-key, not JWT) don't use
    either, so they're correctly left unprotected in the schema.
    """
    if dependant is None:
        return False

    if dependant.call in (get_current_user, require_admin):
        return True

    return any(_dependant_requires_bearer_auth(sub) for sub in dependant.dependencies)


def configure_openapi_bearer_auth(app: FastAPI) -> None:
    """
    Keeps runtime auth unchanged, but fixes Swagger's "Authorize" UX: by
    default FastAPI's auto-detected `OAuth2PasswordBearer` scheme makes the
    Authorize dialog ask for client_id/client_secret/username/password,
    none of which this API uses (login is a plain JSON POST). This swaps
    the documented scheme for a plain HTTP Bearer — a single token field —
    and explicitly marks which operations require it, since
    `oauth2_scheme` is declared with `auto_error=False` (so we can raise
    our own 401s), which means FastAPI's own auto-detection leaves
    `security` unset on every operation.
    """

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        components = schema.setdefault("components", {})
        # Drop the auto-detected OAuth2 scheme entirely — only the simple
        # Bearer input should show up in "Authorize".
        components["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }

        protected_routes = {
            (route.path, method.lower())
            for route in _iter_api_routes(app.routes)
            if _dependant_requires_bearer_auth(route.dependant)
            for method in route.methods
        }

        for path, path_item in schema.get("paths", {}).items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                if (path, method) in protected_routes:
                    operation["security"] = [{"BearerAuth": []}]
                else:
                    operation.pop("security", None)

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Central API for offline-first facial boarding validation system.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    configure_openapi_bearer_auth(app)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(passengers_router)
    app.include_router(biometrics_router)
    app.include_router(tickets_router)
    app.include_router(validations_router)
    app.include_router(sync_router)
    app.include_router(sync_admin_router)

    return app


app = create_app()