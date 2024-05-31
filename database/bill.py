from decimal import Decimal
from database.db import DB
from datetime import datetime, timezone

from utils import generate_unique_code


class BillStatus:
    NEW = 'new'
    PAYED = 'payed'


async def create_bill(user: dict, amount: Decimal, cryptocurrency: str) -> dict:
    unique_code = generate_unique_code()
    creation_date = datetime.now(timezone.utc)

    status = BillStatus.NEW

    bill = {
        "user_id": user.get('user_id'),
        "amount": str(amount),
        "cryptocurrency": cryptocurrency,
        "creation_date": creation_date,
        "status": status,
        "code": unique_code
    }

    await DB.bills.insert_one(bill)
    return bill

async def get_bill_by_code(code: str):
    return await DB.bills.find_one({"code": code})

async def get_bills_by_user(user_id: str):
    cursor = DB.bills.find({"user_id": user_id})
    return await cursor.to_list(length=None)

async def delete_bill_by_code(code: str):
    result = await DB.bills.delete_one({"code": code})
    return result.deleted_count