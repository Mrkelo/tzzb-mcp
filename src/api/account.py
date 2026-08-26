"""账户相关 API"""

from ..client import request


async def get_account_list() -> dict:
    """获取账户列表"""
    return await request("/caishen_fund/pc/account/v1/account_list")


async def get_account_init() -> dict:
    """获取账户初始化数据"""
    return await request("/caishen_fund/pc/account/v1/init")


async def get_account_status() -> dict:
    """获取账户状态"""
    return await request("/caishen_fund/pc/account/v1/status")


async def get_account_status_fund() -> dict:
    """获取基金账户状态"""
    return await request("/caishen_fund/pc/account/v1/status_fund")


async def get_account_init_fund() -> dict:
    """获取基金账户初始化数据"""
    return await request("/caishen_fund/pc/account/v1/init_fund")


async def create_account(name: str, account_type: str = "manual") -> dict:
    """创建账户"""
    return await request(
        "/caishen_fund/pc/account/v1/add_account",
        {"name": name, "type": account_type},
    )


async def rename_account(account_id: str, name: str) -> dict:
    """重命名账户"""
    return await request(
        "/caishen_fund/pc/account/v1/edit_account",
        {"id": account_id, "name": name},
    )


async def delete_account(account_id: str) -> dict:
    """删除账户"""
    return await request(
        "/caishen_fund/pc/account/v1/del_account",
        {"id": account_id},
    )
