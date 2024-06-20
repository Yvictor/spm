from typing import Dict, List
from collections import defaultdict, deque
from .base import Deal, PnL, Position, Account, Action, PositionManagerData
import pickle
from pathlib import Path

class PositionManager:
    def __init__(self, account: Account) -> None:
        self.positions: Dict[str, Position] = {}
        self.deals: Dict[str, deque[Deal]] = defaultdict(deque)
        self.pnls: Dict[str, List[PnL]] = defaultdict(list)
        self.account = account

    def handel_cover(self, code: str, deal: Deal, pos: Position):
        entry_deal = self.deals[code].popleft()
        cover_q = min(entry_deal["remain_quantity"], deal["remain_quantity"])
        pnl = PnL(
            entry=entry_deal,
            cover=deal,
            pnl=(
                (deal["price"] - entry_deal["price"])
                if pos["action"] == Action.Buy
                else (entry_deal["price"] - deal["price"])
            )
            * cover_q,
            quantity=cover_q,
        )
        self.pnls[code].append(pnl)
        pos["quantity"] -= cover_q
        if pos["quantity"]:
            pos["price"] = (
                pos["price"] * (pos["quantity"] + cover_q)
                - entry_deal["price"] * cover_q
            ) / pos["quantity"]
        if cover_q < entry_deal["remain_quantity"]:
            entry_deal["remain_quantity"] -= cover_q
            self.deals[code].appendleft(entry_deal)
        deal["remain_quantity"] -= cover_q
        if deal["remain_quantity"] == 0:
            self.deals[code].pop()
        return pos, deal

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
                pos, deal = self.handel_cover(code, deal, pos)
                while deal["remain_quantity"]:
                    if self.deals[code] and self.deals[code][0]["action"] != deal["action"]:
                        pos, deal = self.handel_cover(code, deal, pos)
                    else:
                        pos["quantity"] = deal["remain_quantity"]
                        pos["price"] = deal["price"]
                        pos["action"] = deal["action"]
                        break
            if pos["quantity"] == 0:
                del self.positions[code]
        else:
            self.positions[code] = Position(
                code=code,
                action=deal["action"],
                quantity=deal["quantity"],
                price=deal["price"],
            )
    
    def list_positions(self):
        return self.positions
    
    def list_positions_details(self):
        return self.deals

    def list_pnls_detail(self):
        return self.pnls
    
    def save(self, path: str = ""):
        data = PositionManagerData(
            deals=pickle.dumps(self.deals),
            positions=pickle.dumps(self.positions),
            pnls=pickle.dumps(self.pnls),
            account=pickle.dumps(self.account)
        )
        data_dump = pickle.dumps(data)
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        path = path.joinpath(self.account["id"]).with_suffix(".pkl")
        path.write_bytes(data_dump)

    @staticmethod
    def load(account_id: str, path: str = "") -> "PositionManager":
        path = Path(path).joinpath(account_id).with_suffix(".pkl")
        data_dump = path.read_bytes()
        data = pickle.loads(data_dump)
        account = pickle.loads(data["account"])
        pm = PositionManager(account=account)   
        pm.deals = pickle.loads(data["deals"])
        pm.positions = pickle.loads(data["positions"])
        pm.pnls = pickle.loads(data["pnls"])
        return pm

class AccountPositionManager:
    def __init__(self, accounts: List[Account]):
        self.managers = {account["id"]: PositionManager(account) for account in accounts}
        self.accounts = {account["id"]: account for account in accounts}

    def add_account(self, account: Account):
        self.managers[account["id"]] = PositionManager(account)
        self.accounts[account["id"]] = account
    
    def get_account_name(self, account_id: str):
        return self.accounts[account_id]["name"]

    def add_deal(self, account_id: str, deal: Deal):
        self.managers[account_id].add_deal(deal)
    
    def list_positions(self, account_id: str):
        return self.managers[account_id].list_positions()
    
    def list_positions_details(self, account_id: str):
        return self.managers[account_id].list_positions_details()
    
    def list_pnls_detail(self, account_id: str):
        return self.managers[account_id].list_pnls_detail()
    
    def save(self, path: str = "spm"):
        for manager in self.managers.values():
            manager.save(path)
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        path = path.joinpath(".spm_meta")
        path.write_bytes(pickle.dumps(self.accounts))
    
    def load(self, path: str = "spm"):
        path = Path(path)
        meta_fp = path.joinpath(".spm_meta")
        if meta_fp.exists():
            self.accounts = pickle.loads(meta_fp.read_bytes())
            for account_id in self.accounts:
                self.managers[account_id] = PositionManager.load(account_id, path)
    