import uuid

from fastapi import APIRouter, Depends, status

from app.auth.backend import current_active_user, current_admin
from app.users.errors import CannotDeleteSelfError
from app.users.manager import UserManager, get_user_manager
from app.users.models import User
from app.users.routes import RouteName
from app.users.schemas import UserAdminUpdate, UserRead, UserUpdate

router = APIRouter()

# Sub-router for admin-only /{id} routes — current_admin applied to all at once.
admin_router = APIRouter(dependencies=[Depends(current_admin)])


@router.get("/me", response_model=UserRead, name=RouteName.users_get_me)
async def get_me(user: User = Depends(current_active_user)):
    return user


@router.patch("/me", response_model=UserRead, name=RouteName.users_update_me)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    return await user_manager.update(user_update, current_user, safe=True)


@admin_router.get("/{id}", response_model=UserRead, name=RouteName.users_get_by_id)
async def get_user(
    id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
):
    return await user_manager.get(id)


@admin_router.patch("/{id}", response_model=UserRead, name=RouteName.users_update_by_id)
async def update_user(
    id: uuid.UUID,
    user_update: UserAdminUpdate,
    user_manager: UserManager = Depends(get_user_manager),
):
    user = await user_manager.get(id)
    return await user_manager.update(user_update, user, safe=False)


@admin_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, name=RouteName.users_delete_by_id)
async def delete_user(
    id: uuid.UUID,
    requesting_user: User = Depends(current_admin),
    user_manager: UserManager = Depends(get_user_manager),
):
    if id == requesting_user.id:
        raise CannotDeleteSelfError()
    user = await user_manager.get(id)
    await user_manager.delete(user)


# Must stay at the bottom — include_router copies routes registered on admin_router at call time.
# Merged here so api/router.py only needs to import one object.
router.include_router(admin_router)
