from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def setup_exception_handlers(app: FastAPI) -> None:
    """Register standard application exception handlers."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Normalize error objects (e.g. ValueError in ctx) to JSON-serializable primitives
        safe_errors = []
        for err in exc.errors():
            item = {}
            for k, v in err.items():
                if k == "ctx" and isinstance(v, dict):
                    item[k] = {ctx_k: str(ctx_v) for ctx_k, ctx_v in v.items()}
                else:
                    item[k] = v
            safe_errors.append(item)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": 422,
                    "message": "Validation error in request parameters",
                    "details": safe_errors,
                },
            },
        )

