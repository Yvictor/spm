from typing import Dict, List
from collections import defaultdict, deque
from .base import Deal, PnL, Position, Account, Action


class PositionManager:
    def __init__(self, account: Account) -> None:
        self.positions: Dict[str, Position] = {}
        self.deals: Dict[str, deque[Deal]] = defaultdict(deque)
        self.pnls: Dict[str, List[PnL]] = defaultdict(list)
        self.account = account

    def add_deal(self, deal: Deal):
        code = deal["code"]
        self.deals[code].append(deal)
        if code in self.positions:
            pos = self.positions[code]
            if pos["action"] == deal["action"]:
                pos["price"] = (
                    pos["price"] * pos["quantity"] + deal["price"] * deal["quantity"]
                ) / (pos["quantity"] + deal["quantity"])
                pos["quantity"] += deal["quantity"]
            else:
                if pos["action"] == Action.Buy:
                    entry_deal = self.deals[code].popleft()
                    cover_q = min(entry_deal["remain_quantity"], deal["quantity"])
                    pnl = PnL(
                        entry=entry_deal,
                        cover=deal,
                        pnl=(deal["price"] - entry_deal["price"]) * cover_q,
                        quantity=cover_q,
                    )
                    self.pnls[code].append(pnl)
                    pos["quantity"] -= cover_q
                    pos["price"] = (pos["price"] * pos["quantity"] - entry_deal["price"] * cover_q) / (pos["quantity"] - cover_q)
                    if cover_q < entry_deal["remain_quantity"]:
                        entry_deal["remain_quantity"] -= cover_q
                        self.deals[code].appendleft(entry_deal)
                    deal["remain_quantity"] -= cover_q
                    if deal["remain_quantity"] == 0:
                        self.deals[code].pop()
                else:
                    entry_deal = self.deals[code].popleft()
                    cover_q = min(entry_deal["remain_quantity"], deal["quantity"])
                    pnl = PnL(
                        entry=entry_deal,
                        cover=deal,
                        pnl=(entry_deal["price"] - deal["price"]) * cover_q,
                        quantity=cover_q,
                    )
                    self.pnls[code].append(pnl)
                    pos["quantity"] -= cover_q
                    pos["price"] = (pos["price"] * pos["quantity"] - entry_deal["price"] * cover_q) / (pos["quantity"] - cover_q)
                    if cover_q < entry_deal["remain_quantity"]:
                        entry_deal["remain_quantity"] -= cover_q
                        self.deals[code].appendleft(entry_deal)
                    deal["remain_quantity"] -= cover_q
                    if deal["remain_quantity"] == 0:
                        self.deals[code].pop()

            # if deal["action"] == Action.Buy:
            #     # if pos["quantity"] < 0:
            #     #     entry_deal = self.deals[code].popleft()
            #     #     cover_q = min(entry_deal["remain_quantity"], deal["quantity"])
            #     #     pnl = PnL(entry=entry_deal, cover=deal, pnl=(deal["price"] - entry_deal["price"]) * cover_q, quantity=cover_q)
            #     #     if cover_q
            #     #     if cover_q < entry_deal["remain_quantity"]:
            #     #         entry_deal["remain_quantity"] -= cover_q
            #     #         self.deals[code].appendleft(entry_deal)
            #     #     self.pnls[code].append(pnl)
            #     #     pos["price"] = (pos["price"] * (-pos["quantity"]) - deal["price"] * cover_q) / (-pos["quantity"] + cover_q)
            #     #     pos["quantity"] += cover_q
            #     #     if
            #     # else:
            #     pos["price"] = (
            #         pos["price"] * pos["quantity"] + deal["price"] * deal["quantity"]
            #     ) / (pos["quantity"] + deal["quantity"])
            #     pos["quantity"] += deal["quantity"]
            # else:
            #     pos["price"] = (
            #         pos["price"] * pos["quantity"] + deal["price"] * deal["quantity"]
            #     ) / (pos["quantity"] + deal["quantity"])
            #     pos["quantity"] -= deal["quantity"]
            if pos["quantity"] == 0:
                del self.positions[code]
        else:
            self.positions[code] = Position(
                code=code,
                action=deal["action"],
                quantity=deal["quantity"],
                price=deal["price"],
            )
