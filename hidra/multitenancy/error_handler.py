try:
    from fastapi import Request, HTTPException
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    import json
    import logging
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Configurar logging
logger = logging.getLogger(__name__)

if FASTAPI_AVAILABLE:
    class ErrorHandlerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            try:
                response = await call_next(request)
                return response
                
            except HTTPException as e:
                # Manejar HTTPExceptions
                error_detail = e.detail
                
                # Si el detail es un string que parece JSON, intentar parsearlo
                if isinstance(error_detail, str):
                    try:
                        # Intentar parsear como JSON
                        parsed_detail = json.loads(error_detail)
                        if isinstance(parsed_detail, dict):
                            error_detail = parsed_detail
                    except (json.JSONDecodeError, TypeError):
                        # Si no es JSON válido, mantener como string
                        error_detail = {"error": error_detail}
                
                logger.warning(f"HTTPException: {e.status_code} - {error_detail}")
                
                return JSONResponse(
                    status_code=e.status_code,
                    content=error_detail if isinstance(error_detail, dict) else {"error": error_detail}
                )
                
            except Exception as e:
                # Manejar otros errores inesperados
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "message": "An unexpected error occurred",
                        "type": type(e).__name__
                    }
                )