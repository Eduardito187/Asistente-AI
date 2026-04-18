from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ...domain.shared.errors import EntidadNoEncontrada, ReglaDeNegocioViolada, ValorInvalido


def registrar(app: FastAPI) -> None:

    @app.exception_handler(EntidadNoEncontrada)
    async def _not_found(_: Request, exc: EntidadNoEncontrada):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ReglaDeNegocioViolada)
    async def _conflict(_: Request, exc: ReglaDeNegocioViolada):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValorInvalido)
    async def _bad(_: Request, exc: ValorInvalido):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
