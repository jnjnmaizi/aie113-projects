import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.concurrency import run_in_threadpool
from bean_vision.adapters.images import InvalidImage, ImageTooLarge, decode_image
from bean_vision.service import VisionService
from bean_vision.settings import Settings

logger = logging.getLogger("bean_vision")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Prediction(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    scores: dict[str, float]
    not_sure: bool
    decision: str
    model_version: str
    notice: str = "Bean-leaf screening only; confidence is not proof. An agronomist must confirm."


def error(status: int, code: str, message: str):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


class BodyLimit:
    """Bound bytes before multipart parsing, including chunked requests."""

    def __init__(self, app, max_bytes: int):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.max_bytes:
                return await error(413, "file_too_large", "Upload exceeds the size limit")(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


def create_app(settings: Settings | None = None, model_factory=None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.service = None
        app.state.lock = asyncio.Lock()
        try:
            if model_factory is None:
                from bean_vision.adapters.model import HuggingFaceModel

                model = await run_in_threadpool(
                    HuggingFaceModel, settings.model_dir, settings.max_pixels, settings.torch_threads
                )
            else:
                model = model_factory()
            app.state.service = VisionService(model, settings.not_sure_below)
        except Exception:
            # Do not log exception values: a library exception can contain credentials or paths.
            logger.error("Model startup failed; readiness remains unavailable")
        yield
        app.state.service = None

    app = FastAPI(
        title="Bean Leaf Vision",
        version="1.0.0",
        lifespan=lifespan,
        responses={status: {"model": ErrorResponse} for status in (413, 415, 422, 429, 500, 503)},
    )
    app.add_middleware(BodyLimit, max_bytes=settings.max_upload_bytes + 65536)
    app.state.service = None

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def frontend():
        return FileResponse(static_dir / "index.html")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return error(422, "invalid_request", "Send one image in the multipart field 'file'")

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(exc.status_code, "request_error", "Request could not be accepted")

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        logger.error("Request failed")
        return error(500, "internal_error", "The request could not be processed")

    @app.get("/health")
    async def health():
        return {"status": "alive"}

    @app.get("/ready")
    async def ready():
        if app.state.service is None:
            return error(503, "not_ready", "The model is not ready")
        return {"status": "ready", "model_version": settings.model_version}

    async def execute(file: UploadFile, explain: bool):
        try:
            if app.state.service is None:
                return error(503, "not_ready", "The model is not ready")
            if file.content_type not in {"image/jpeg", "image/png"}:
                return error(415, "unsupported_type", "Use a JPEG or PNG image")
            data = await file.read(settings.max_upload_bytes + 1)
            if len(data) > settings.max_upload_bytes:
                return error(413, "file_too_large", "Upload exceeds the size limit")
            if app.state.lock.locked():
                return error(429, "busy", "The model is busy; retry shortly")
            async with app.state.lock:
                try:
                    await run_in_threadpool(decode_image, data, settings.max_pixels)
                    if explain:
                        png = await run_in_threadpool(app.state.service.explain, data)
                        return Response(
                            png,
                            media_type="image/png",
                            headers={"X-Explanation-Method": "occlusion-32-stride-16"},
                        )
                    answer = await run_in_threadpool(app.state.service.diagnose, data)
                    return Prediction(**asdict(answer), model_version=settings.model_version)
                except ImageTooLarge:
                    return error(413, "image_too_large", "Image dimensions exceed the limit")
                except InvalidImage:
                    return error(422, "invalid_image", "File must be a valid JPEG or PNG image")
                except Exception:
                    logger.error("Prediction failed")
                    return error(500, "internal_error", "The request could not be processed")
        finally:
            await file.close()

    @app.post("/v1/predict", response_model=Prediction)
    async def predict(file: UploadFile = File(...)):
        return await execute(file, False)

    @app.post(
        "/v1/explain",
        response_class=Response,
        responses={
            200: {
                "content": {"image/png": {}},
                "description": "Blue areas: hiding them lowers the predicted class score. Not a disease segmentation.",
            }
        },
    )
    async def explain(file: UploadFile = File(...)):
        return await execute(file, True)

    return app


app = create_app()
