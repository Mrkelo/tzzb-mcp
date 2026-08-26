"""自选列表相关 API"""

from ..client import request


def get_watchlist(sort_rule: str = "", sort_order: str = "") -> dict:
    """获取自选列表"""
    params = {}
    if sort_rule:
        params["sort_rule"] = sort_rule
    if sort_order:
        params["sort_order"] = sort_order
    return request("/caishen_fund/pc/optional/v1/sort_list", params)