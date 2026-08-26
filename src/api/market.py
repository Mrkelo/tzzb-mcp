"""行情相关 API"""

from ..client import request


def get_stock_quotes(codes: list[str] | str, date: str = "") -> dict:
    """获取股票行情"""
    if isinstance(codes, list):
        code_str = ",".join(codes)
    else:
        code_str = codes
    params = {"code": code_str}
    if date:
        params["date"] = date.replace("-", "")
    return request("/caishen_fund/invest/getQuotes", params)


def get_exchange_rate(date: str = "") -> dict:
    """获取港股汇率"""
    params = {}
    if date:
        params["date"] = date.replace("-", "")
    return request("/caishen_fund/stock_common/v1/hk_rate", params)


def get_last_trade_day() -> dict:
    """获取最近交易日"""
    return request("/caishen_fund/stock_common/v1/last_trading_day")


def get_user_config() -> dict:
    """获取用户自定义配置"""
    return request("/caishen_fund/cloud/get_user_customConfig")