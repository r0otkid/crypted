from decimal import Decimal
from database.db import DB
from datetime import datetime, timezone

from utils import generate_unique_code


class CheckStatus:
    NEW = 'new'
    WINNING = 'winning'
    CASHED = 'cashed'


async def create_check(user: dict, amount: Decimal, cryptocurrency: str) -> dict:
    unique_code = generate_unique_code()
    creation_date = datetime.now(timezone.utc)

    status = CheckStatus.NEW

    check = {
        "user_id": user.get('user_id'),
        "amount": str(amount),
        "cryptocurrency": cryptocurrency,
        "creation_date": creation_date,
        "status": status,
        "code": unique_code
    }

    await DB.checks.insert_one(check)
    return check

async def get_check_by_code(code: str):
    return await DB.checks.find_one({"code": code})

async def get_checks_by_user(user_id: str):
    cursor = DB.checks.find({"user_id": user_id})
    return await cursor.to_list(length=None)

async def delete_check_by_code(code: str):
    result = await DB.checks.delete_one({"code": code})
    return result.deleted_count