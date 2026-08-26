"""数据模型定义"""

from pydantic import BaseModel


class Position(BaseModel):
    """持仓项"""

    code: str = ""
    name: str = ""
    market: str = ""
    count: float = 0.0
    cost: float = 0.0
    price: float = 0.0
    value: float = 0.0
    pos_profit: float = 0.0
    pos_rate: float = 0.0
    today_profit: float = 0.0
    today_rate: float = 0.0
    weight: float | None = None
    close_profit: float = 0.0
    close_rate: float = 0.0
    sum_profit: float = 0.0
    sum_rate: float = 0.0
    max_cost: float = 0.0
    w_profit: float = 0.0
    m_profit: float = 0.0
    y_profit: float = 0.0
    back_rate: float = 0.0
    stock_account: str | None = None


class Account(BaseModel):
    """账户"""

    account_id: str = ""
    account_type: str = ""  # manual | auto | margin
    account_name: str = ""
    balance: float = 0.0
    asset: float = 0.0
    value: float = 0.0
    debt: float = 0.0
    today_profit: float = 0.0
    today_rate: float = 0.0
    pos_profit: float = 0.0
    pos_rate: float = 0.0
    sum_profit: float = 0.0
    sum_rate: float = 0.0
    positions: list[Position] = []


class TradeRecord(BaseModel):
    """交易记录"""

    code: str = ""
    name: str = ""
    market: str = ""
    direction: str = ""  # 买入/卖出
    price: float = 0.0
    count: float = 0.0
    amount: float = 0.0
    fee: float = 0.0
    date: str = ""
    time: str = ""


class AssetTrendPoint(BaseModel):
    """资产趋势数据点"""

    date: str = ""
    asset: float = 0.0
    profit: float = 0.0
    rate: float = 0.0


class WatchlistItem(BaseModel):
    """自选项"""

    code: str = ""
    name: str = ""
    market: str = ""
    item_type: str = ""  # stock | fund
    price: float = 0.0
    change_pct: float = 0.0


class LoginStatus(BaseModel):
    """登录状态"""

    logged_in: bool = False
    userid: str = ""
    cookie_count: int = 0
    extracted_at: str = ""
    message: str = ""
