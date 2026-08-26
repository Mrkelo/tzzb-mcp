"""账户相关 API"""

from ..client import request


def get_account_list() -> dict:
    """获取账户列表"""
    return request("/caishen_fund/pc/account/v1/account_list")


def get_account_init() -> dict:
    """获取账户初始化数据"""
    return request("/caishen_fund/pc/account/v1/init")


def get_account_status() -> dict:
    """获取账户状态"""
    return request("/caishen_fund/pc/account/v1/status")