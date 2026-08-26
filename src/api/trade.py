"""交易相关 API"""

from ..client import request


def get_today_trades(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取今日交易记录"""
    params = {}
    if manual_id:
        params["manual_id"] = manual_id
    if fund_key:
        params["fund_key"] = fund_key
    if rzrq_fund_key:
        params["rzrq_fund_key"] = rzrq_fund_key
    return request("/caishen_fund/pc/account/v1/merge_day_trading", params)


def get_today_transfers(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取今日资金流水"""
    params = {}
    if manual_id:
        params["manual_id"] = manual_id
    if fund_key:
        params["fund_key"] = fund_key
    if rzrq_fund_key:
        params["rzrq_fund_key"] = rzrq_fund_key
    return request("/caishen_fund/pc/asset/v1/query_bank_history", params)