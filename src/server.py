"""同花顺投资账本 MCP 服务"""

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from . import auth
from .api import account, market, position, trade, watchlist
from .client import TzzbError

mcp = MCPServer(
    name="tzzb-mcp",
    title="同花顺投资账本",
    description="同花顺投资账本 MCP 服务，提供多账户持仓、交易记录、资产趋势等数据查询",
    version="0.1.0",
)


# ============================================================
# 认证相关工具
# ============================================================


@mcp.tool(name="tzzb_login", description="登录投资账本：自动连接 Chrome 浏览器提取 Cookie")
def tzzb_login() -> dict[str, Any]:
    """提取浏览器 Cookie 完成认证"""
    result = auth.login()
    return result


@mcp.tool(name="tzzb_login_status", description="检查当前登录状态")
def tzzb_login_status() -> dict[str, Any]:
    """查看登录状态"""
    status = auth.get_login_status()
    return status.model_dump()


# ============================================================
# 账户相关工具
# ============================================================


@mcp.tool(name="tzzb_account_list", description="获取所有账户列表")
async def tzzb_account_list() -> dict[str, Any]:
    """获取账户列表"""
    return await account.get_account_list()


@mcp.tool(name="tzzb_account_summary", description="获取账户总览：总资产、总收益、持仓统计")
async def tzzb_account_summary() -> dict[str, Any]:
    """获取账户总览"""
    try:
        result = await account.get_account_init()
        return result
    except TzzbError:
        return await account.get_account_list()


# ============================================================
# 持仓相关工具
# ============================================================


@mcp.tool(
    name="tzzb_positions",
    description="获取持仓明细（股票+基金），可指定账户ID",
)
async def tzzb_positions(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict[str, Any]:
    """获取持仓详情"""
    stock_data = await position.get_stock_position(
        manual_id=manual_id,
        fund_key=fund_key,
        rzrq_fund_key=rzrq_fund_key,
    )
    fund_data = await position.get_fund_position(
        manual_id=manual_id,
        fund_key=fund_key,
    )
    return {"stock": stock_data, "fund": fund_data}


@mcp.tool(
    name="tzzb_portfolio",
    description="投资组合总览：一键获取账户列表、总资产、持仓汇总、收益率、今日盈亏",
)
async def tzzb_portfolio() -> dict[str, Any]:
    """投资组合总览（合并多个API）"""
    init = await account.get_account_init()
    return init


@mcp.tool(
    name="tzzb_asset_trend",
    description="获取资产/收益趋势数据",
)
async def tzzb_asset_trend(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict[str, Any]:
    """获取资产趋势"""
    return await position.get_asset_trend(
        manual_id=manual_id,
        fund_key=fund_key,
        rzrq_fund_key=rzrq_fund_key,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool(
    name="tzzb_time_share",
    description="获取分时收益数据",
)
async def tzzb_time_share(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict[str, Any]:
    """获取分时收益"""
    return await position.get_time_share(
        manual_id=manual_id,
        fund_key=fund_key,
        rzrq_fund_key=rzrq_fund_key,
    )


# ============================================================
# 交易记录工具
# ============================================================


@mcp.tool(
    name="tzzb_trade_records",
    description="获取当日交易记录",
)
async def tzzb_trade_records(
    manual_id: str = "",
    fund_key: str = "",
    rzrq_fund_key: str = "",
) -> dict[str, Any]:
    """获取当日交易记录"""
    return await trade.get_today_trades(
        manual_id=manual_id,
        fund_key=fund_key,
        rzrq_fund_key=rzrq_fund_key,
    )


# ============================================================
# 行情相关工具
# ============================================================


@mcp.tool(
    name="tzzb_stock_quotes",
    description="获取股票实时行情，codes 格式如 ['33:600519', '33:000001']",
)
async def tzzb_stock_quotes(codes: list[str], date: str = "") -> dict[str, Any]:
    """获取股票行情"""
    return await market.get_stock_quotes(codes, date)


@mcp.tool(
    name="tzzb_exchange_rate",
    description="获取港元兑人民币汇率",
)
async def tzzb_exchange_rate(date: str = "") -> dict[str, Any]:
    """获取港股汇率"""
    return await market.get_exchange_rate(date)


@mcp.tool(
    name="tzzb_trade_day",
    description="获取最近交易日信息",
)
async def tzzb_trade_day() -> dict[str, Any]:
    """获取最近交易日"""
    return await market.get_last_trade_day()


# ============================================================
# 自选列表工具
# ============================================================


@mcp.tool(
    name="tzzb_watchlist",
    description="获取自选股票和基金列表",
)
async def tzzb_watchlist(sort_rule: str = "", sort_order: str = "") -> dict[str, Any]:
    """获取自选列表"""
    return await watchlist.get_watchlist(sort_rule, sort_order)


# ============================================================
# 服务入口
# ============================================================


def main():
    """MCP 服务入口"""
    import asyncio

    from mcp.server.stdio import stdio_server

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(
                read_stream,
                write_stream,
                mcp.create_initialization_options(),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()