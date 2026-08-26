"""持仓相关 API"""

from ..client import request


def get_stock_position(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取股票持仓"""
    params = {}
    if manual_id:
        params["manual_id"] = manual_id
    if fund_key:
        params["fund_key"] = fund_key
    if rzrq_fund_key:
        params["rzrq_fund_key"] = rzrq_fund_key
    return request("/caishen_fund/pc/asset/v1/stock_position", params)


def get_fund_position(manual_id: str = "", fund_key: str = "") -> dict:
    """获取基金持仓"""
    params = {}
    if manual_id:
        params["manual_id"] = manual_id
    if fund_key:
        params["fund_key"] = fund_key
    return request("/caishen_fund/fund/v1/merge_fund", params)


def get_asset_trend(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    """获取资产趋势"""
    params = {}
    if manual_id:
        params["manual_id"] = manual_id
    if fund_key:
        params["fund_key"] = fund_key
    if rzrq_fund_key:
        params["rzrq_fund_key"] = rzrq_fund_key
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return request("/caishen_fund/pc/asset/v1/asset_trend", params)


def get_time_share(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取分时收益"""
    params = {}
    if manual_id:
        params["manual_id"] = manual_id
    if fund_key:
        params["fund_key"] = fund_key
    if rzrq_fund_key:
        params["rzrq_fund_key"] = rzrq_fund_key
    return request("/caishen_fund/pc/asset/v1/time_share", params)