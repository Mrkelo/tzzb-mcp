"""持仓相关 API"""

from ..client import request


async def get_stock_position(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取股票持仓"""
    params = {"manual_id": manual_id, "fund_key": fund_key, "rzrq_fund_key": rzrq_fund_key}
    return await request("/caishen_fund/pc/asset/v1/stock_position", params)


async def get_fund_position(manual_id: str = "", fund_key: str = "") -> dict:
    """获取基金持仓"""
    params = {"manual_id": manual_id, "fund_key": fund_key}
    return await request("/caishen_fund/fund/v1/merge_fund", params)


async def get_asset_trend(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    """获取资产趋势"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await request("/caishen_fund/pc/asset/v1/asset_trend", params)


async def get_time_share(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取分时收益"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    return await request("/caishen_fund/pc/asset/v1/time_share", params)


async def get_stock_card(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取股票卡片"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    return await request("/caishen_fund/pc/account/v1/stock_card", params)


async def get_fund_card(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取基金卡片"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    return await request("/caishen_fund/pc/account/v1/fund_card", params)


async def get_fund_quota(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取基金指标"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    return await request("/caishen_fund/pc/asset/v1/fund_quota", params)


async def get_merge_compare(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取合并比较"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    return await request("/caishen_fund/pc/asset/v1/merge_compare", params)


async def get_link_stock(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict:
    """获取关联股票"""
    params = {
        "manual_id": manual_id,
        "fund_key": fund_key,
        "rzrq_fund_key": rzrq_fund_key,
    }
    return await request("/caishen_fund/pc/account/v2/get_link_stock", params)
