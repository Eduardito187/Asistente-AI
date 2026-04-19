from __future__ import annotations

from fastapi import APIRouter, Depends

from ....application.services.reindexador_embeddings import ReindexadorEmbeddings
from ..deps import reindexador_embeddings

router = APIRouter(prefix="/admin/embeddings", tags=["embeddings-admin"])


@router.post("/reindexar")
def reindexar(
    reindexador: ReindexadorEmbeddings = Depends(reindexador_embeddings),
):
    total = reindexador.reindexar_faltantes()
    return {"reindexados": total}
