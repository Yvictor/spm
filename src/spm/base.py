from typing import TypedDict
from enum import Enum
import datetime

class Action(str, Enum):
    Buy = "B"
    Sell = "S"


class Deal(TypedDict):
    code: str
    action: Action
    quantity: int
    remain_quantity: int
    price: float
    date: datetime.date
    time: datetime.time

class PnL(TypedDict):
    entry: Deal
    cover: Deal
    quantity: int
    pnl: float
    # tax: float
    # fee: float

class Position(TypedDict):
    code: str
    action: Action
    quantity: int
    price: float

class Account(TypedDict):
    id: str
    name: str
