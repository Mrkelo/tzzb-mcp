"""行情相关 API"""

from ..client import request


async def get_stock_quotes(codes: list[str], date: str = "") -> dict:
    """获取股票行情

    Args:
        codes: 股票代码列表，格式 ["market:code", ...]，如 ["33:600519"]
        date: 日期，格式 YYYYMMDD
    """
    params = {"code": ",".join(codes)}
    if date:
        params["date"] = date.replace("-", "")
    return await request("/caishen_fund/invest/getQuotes", params)


async def get_exchange_rate(date: str = "") -> dict:
    """获取港股汇率

    Args:
        date: 日期，格式 YYYYMMDD
    """
    params = {}
    if date:
        params["date"] = date.replace("-", "")
    return await request("/caishen_fund/stock_common/v1/hk_rate", params)


async def get_last_trade_day() -> dict:
    """获取最近交易日"""
    return await request("/caishen_fund/stock_common/v1/last_trading_day")


async def get_user_config() -> dict:
    """获取用户自定义配置"""
    return await request("/caishen_fund/cloud/get_user_customConfig")
