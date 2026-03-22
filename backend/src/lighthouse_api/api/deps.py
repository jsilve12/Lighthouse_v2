from fastapi import Request


async def get_current_user(request: Request) -> dict:
    return {
        "email": getattr(request.state, "user_email", "anonymous"),
        "name": getattr(request.state, "user_name", ""),
        "sub": getattr(request.state, "user_sub", ""),
        "auth_method": getattr(request.state, "auth_method", "none"),
    }
