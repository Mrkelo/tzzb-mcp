"""自选列表相关 API"""

from ..client import request


async def get_watchlist(sort_rule: str = "", sort_order: str = "") -> dict:
    """获取自选列表

    Args:
        sort_rule: 排序规则
        sort_order: 排序方向，0=降序 1=升序
    """
    params = {}
    if sort_rule:
        params["sort_rule"] = sort_rule
    if sort_order:
        params["sort_order"] = sort_order
    return await request("/caishen_fund/pc/optional/v1/sort_list", params)
