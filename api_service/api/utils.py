import uuid
from typing import Optional, Union

import api.models as models

from django.conf import settings

import jwt


def user_from_refresh_token(
    token: Union[str, uuid.UUID],
) -> Optional[models.CustomUser]:
    """Returns user instance on valid token
    (meaning existing) or None instead"""
    if type(token) is uuid.UUID:
        token = models.RefreshToken.objects.filter(token=token).first()
    else:
        token = models.RefreshToken.get_token(token)
    if token is None:
        return None
    return token.user


def user_from_access_token(token: str) -> Optional[models.CustomUser]:
    """Returns user instance on valid token or None instead"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = models.CustomUser.objects.filter(email=payload["sub"]).first()
        return user
    except jwt.exceptions.InvalidTokenError:
        return None
