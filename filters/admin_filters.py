from os import getenv

from aiogram.filters import BaseFilter
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS = [int(ID) for ID in getenv('ADMIN_IDS', '').split(',')]


def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return is_admin(message.from_user.id)
