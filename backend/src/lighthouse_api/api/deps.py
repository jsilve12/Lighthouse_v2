from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from lighthouse_api.core.database import get_db


async def get_current_user(request: Request) -> dict:
    return {
        "email": getattr(request.state, "user_email", "anonymous"),
        "name": getattr(request.state, "user_name", ""),
        "sub": getattr(request.state, "user_sub", ""),
        "auth_method": getattr(request.state, "auth_method", "none"),
    }
