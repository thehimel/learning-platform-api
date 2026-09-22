from fastapi import APIRouter
from pydantic import BaseModel

from app.index.constants import RouteName
from app.index.service import get_hello

router = APIRouter()


class RootResponse(BaseModel):
    message: str


@router.get("/", name=RouteName.root, response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(message=get_hello())
