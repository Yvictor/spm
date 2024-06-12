import pytest
from spm.manager import PositionManager
from spm.base import Deal, Action
import datetime


@pytest.mark.parametrize("action", ["B", "S"])
def test_add_deal_without_position(action: str):
    account = {"id": "0", "name": "test"}
    manager = PositionManager(account)
    deal = Deal(
        code="AAPL",
        action=action,
        quantity=100,
        remain_quantity=100,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal)
    assert len(manager.deals["AAPL"]) == 1
    assert manager.deals["AAPL"][0] == deal
    assert manager.positions["AAPL"]["quantity"] == 100
    assert manager.positions["AAPL"]["price"] == 100.0
    assert manager.positions["AAPL"]["action"] == Action(action)


@pytest.mark.parametrize("action", ["B", "S"])
def test_add_deal_with_exist_pos_same_side(action: str):
    account = {"id": "0", "name": "test"}
    manager = PositionManager(account)
    deal_init = Deal(
        code="AAPL",
        action=action,
        quantity=100,
        remain_quantity=100,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_init)

    deal_new = Deal(
        code="AAPL",
        action=action,
        quantity=100,
        remain_quantity=100,
        price=110.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_new)

    assert len(manager.deals["AAPL"]) == 2
    assert manager.deals["AAPL"][0] == deal_init
    assert manager.deals["AAPL"][1] == deal_new
    assert manager.positions["AAPL"]["quantity"] == 200
    assert manager.positions["AAPL"]["price"] == 105.0
    assert manager.positions["AAPL"]["action"] == Action(action)

@pytest.mark.parametrize("action", ["B", "S"])
def test_add_deal_simple_cover(action: str):
    account = {"id": "0", "name": "test"}
    manager = PositionManager(account)
    deal_init = Deal(
        code="AAPL",
        action=action,
        quantity=100,
        remain_quantity=100,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_init)

    deal_new = Deal(
        code="AAPL",
        action="S" if action == Action.Buy else "B",
        quantity=100,
        remain_quantity=100,
        price=110.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_new)

    assert len(manager.deals["AAPL"]) == 0
    # assert manager.positions["AAPL"]["quantity"] == 0
    assert "AAPL" not in manager.positions
    assert "AAPL" in manager.pnls
    assert len(manager.pnls["AAPL"]) == 1
    assert manager.pnls["AAPL"][0]["entry"] == deal_init
    assert manager.pnls["AAPL"][0]["cover"] == deal_new
    assert manager.pnls["AAPL"][0]["quantity"] == 100
    assert manager.pnls["AAPL"][0]["pnl"] == 1000.0 if action == Action.Buy else -1000.0

@pytest.mark.parametrize("action", ["B", "S"])
def test_add_deal_partial_cover(action: str):
    account = {"id": "0", "name": "test"}
    manager = PositionManager(account)
    deal_init = Deal(
        code="AAPL",
        action=action,
        quantity=100,
        remain_quantity=100,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_init)

    deal_new = Deal(
        code="AAPL",
        action="S" if action == Action.Buy else "B",
        quantity=20,
        remain_quantity=20,
        price=110.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 10, 0),
    )
    manager.add_deal(deal_new)

    assert len(manager.deals["AAPL"]) == 1
    assert manager.deals["AAPL"][0]["remain_quantity"] == 80
    assert manager.positions["AAPL"]["quantity"] == 80
    assert manager.positions["AAPL"]["price"] == 100.0
    assert manager.positions["AAPL"]["action"] == Action(action)
    assert "AAPL" in manager.pnls
    assert len(manager.pnls["AAPL"]) == 1
    assert manager.pnls["AAPL"][0]["entry"] == deal_init
    assert manager.pnls["AAPL"][0]["cover"] == deal_new
    assert manager.pnls["AAPL"][0]["quantity"] == 20
    assert manager.pnls["AAPL"][0]["pnl"] == 20 * 10.0 if action == Action.Buy else 20 * -10.0

@pytest.mark.parametrize("action", ["B", "S"])
def test_add_deal_over_cover(action: str):
    account = {"id": "0", "name": "test"}
    manager = PositionManager(account)
    deal_init = Deal(
        code="AAPL",
        action=action,
        quantity=100,
        remain_quantity=100,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_init)

    deal_new = Deal(
        code="AAPL",
        action="S" if action == Action.Buy else "B",
        quantity=120,
        remain_quantity=120,
        price=110.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 10, 0),
    )
    manager.add_deal(deal_new)

    assert len(manager.deals["AAPL"]) == 1
    assert manager.deals["AAPL"][0]["remain_quantity"] == 20
    assert manager.positions["AAPL"]["quantity"] == 20
    assert manager.positions["AAPL"]["price"] == 110.0
    assert manager.positions["AAPL"]["action"] == "S" if action == Action.Buy else "B"
    assert "AAPL" in manager.pnls
    assert len(manager.pnls["AAPL"]) == 1
    assert manager.pnls["AAPL"][0]["entry"] == deal_init
    assert manager.pnls["AAPL"][0]["cover"] == deal_new
    assert manager.pnls["AAPL"][0]["quantity"] == 100
    assert manager.pnls["AAPL"][0]["pnl"] == 1000.0 if action == Action.Buy else -1000.0



@pytest.mark.parametrize("action", ["B", "S"])
def test_add_deal_multi_deal_over_cover(action: str):
    account = {"id": "0", "name": "test"}
    manager = PositionManager(account)
    deal_0 = Deal(
        code="AAPL",
        action=action,
        quantity=40,
        remain_quantity=40,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    deal_1 = Deal(
        code="AAPL",
        action=action,
        quantity=60,
        remain_quantity=60,
        price=100.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 0, 0),
    )
    manager.add_deal(deal_0)
    manager.add_deal(deal_1)

    deal_cover = Deal(
        code="AAPL",
        action="S" if action == Action.Buy else "B",
        quantity=120,
        remain_quantity=120,
        price=110.0,
        date=datetime.date(2021, 1, 1),
        time=datetime.time(9, 10, 0),
    )
    manager.add_deal(deal_cover)

    assert len(manager.deals["AAPL"]) == 1
    assert manager.deals["AAPL"][0]["remain_quantity"] == 20
    assert manager.positions["AAPL"]["quantity"] == 20
    assert manager.positions["AAPL"]["price"] == 110.0
    assert manager.positions["AAPL"]["action"] == "S" if action == Action.Buy else "B"
    assert "AAPL" in manager.pnls
    assert len(manager.pnls["AAPL"]) == 2
    assert manager.pnls["AAPL"][0]["entry"] == deal_0
    assert manager.pnls["AAPL"][0]["cover"] == deal_cover
    assert manager.pnls["AAPL"][0]["quantity"] == 40
    assert manager.pnls["AAPL"][0]["pnl"] == 400.0 if action == Action.Buy else -400.0
    assert manager.pnls["AAPL"][1]["entry"] == deal_1
    assert manager.pnls["AAPL"][1]["cover"] == deal_cover
    assert manager.pnls["AAPL"][1]["quantity"] == 60
    assert manager.pnls["AAPL"][1]["pnl"] == 600.0 if action == Action.Buy else -600.0