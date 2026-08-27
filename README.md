# tzzb-mcp

同花顺投资账本 MCP 服务（Tonghuashun Investment Ledger MCP Server）

通过 [MCP（Model Context Protocol）](https://modelcontextprotocol.io) 查询个人多账户的**持仓明细、资产趋势、交易记录、实时行情和自选列表**。供 AI 助手（如 WorkBuddy）接入后，直接以自然语言查询你的投资账本数据。

## 功能特性

- **13 个 MCP 工具**，覆盖登录认证、账户、持仓、趋势、交易、行情、汇率、交易日、自选查询
- **多账户支持**：券商账户、手工账户、融资融券账户（按 `fund_key` / `manual_id` / `rzrq_fund_key` 区分）
- **CDP 浏览器代理**：所有 API 请求通过 Chrome DevTools Protocol 在浏览器内执行，复用浏览器原生网络栈，规避 Python 直连的 401 反爬拦截
- **独立 Chrome Profile**（`~/.tzzb_chrome_profile`），不影响日常浏览器使用
- **Cookie 持久化**（`~/.tzzb_cookies.json`），登录一次约 7 天内免重复登录
- **断线自动重连**：CDP 连接断开时自动重连重试一次

## 环境要求

- Python ≥ 3.10
- 已安装 Chrome 浏览器

## 安装

```bash
cd tzzb-mcp
pip install .
```

依赖：`mcp>=1.0.0`、`websocket-client>=1.8.0`、`pydantic>=2.0.0`。

安装后可通过命令 `tzzb-mcp` 启动服务（入口定义于 `pyproject.toml` 的 `[project.scripts]`）。

## MCP 配置

在 MCP 客户端（如 WorkBuddy 的 `mcp.json`）中通过 stdio 方式接入：

```json
{
  "mcpServers": {
    "tzzb-mcp": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/tzzb-mcp"
    }
  }
}
```

`cwd` 需指向项目目录（含 `src/` 的目录）。

## 快速开始

**首次使用必须先调用 `tzzb_login`**：该工具会启动一个 Chrome 调试实例，你需要在浏览器中登录投资账本（tzzb.10jqka.com.cn），登录成功后 Cookie 会被自动提取并持久化。

```
1. tzzb_login          → 弹出 Chrome，手动登录投资账本
2. tzzb_account_list   → 获取所有账户的 fund_key / manual_id
3. tzzb_positions      → 查看持仓明细
```

日常查询：

```
1. tzzb_account_list   → 获取账户列表
2. tzzb_positions      → 查看具体持仓
3. tzzb_asset_trend    → 查看收益走势（可选）
```

## 工具列表

| 工具名 | 用途 |
|--------|------|
| `tzzb_login` | 登录投资账本，提取并持久化 Cookie（首次必调） |
| `tzzb_login_status` | 检查当前登录状态 |
| `tzzb_account_list` | 获取所有账户列表（含 `fund_key`、`manual_id`）⭐ |
| `tzzb_account_summary` | 账户总览（接口不可用时自动回退） |
| `tzzb_portfolio` | 投资组合总览（同 account_summary，含回退） |
| `tzzb_positions` | 获取持仓明细（股票 + 基金）⭐ |
| `tzzb_asset_trend` | 获取资产 / 收益趋势数据 |
| `tzzb_time_share` | 获取当日分时收益数据 |
| `tzzb_trade_records` | 获取当日交易记录 |
| `tzzb_stock_quotes` | 获取股票实时行情 |
| `tzzb_exchange_rate` | 获取港元兑人民币汇率 |
| `tzzb_trade_day` | 获取最近交易日信息 |
| `tzzb_watchlist` | 获取自选股票和基金列表 |

⭐ 标记为最常用工具。

## 使用规则与注意事项

- **禁止并行调用**：所有工具共享同一个 Chrome CDP 连接（底层有全局锁），一次只能调用一个工具，请串行调用。
- **查询持仓先取账户列表**：`tzzb_positions` 的 `fund_key` / `manual_id` 参数来自 `tzzb_account_list`；不传参数时返回所有账户的聚合数据（可能为空）。
- **行情格式为 `市场:代码`**：上证用 `33`（如 `33:600519`），深证用 `47`（如 `47:000001`）。持仓数据中的 `market` 字段 `"2"` 对应上海（33）、`"1"` 对应深圳（47）。
- **基金持仓接口不可用**：`tzzb_positions` 返回的 `fund` 字段始终为 `{"error": "基金持仓接口不可用"}`（底层接口返回 HTTP 400，已内置保护），请忽略 `fund` 字段，只使用 `stock` 数据。
- **字段名为拼音缩写**：行情返回 `xianjia`（现价）、`zuoshou`（昨收）、`zqdm`（代码）、`scdm`（市场）；展示时需映射为中文。
- **数值字段可能是字符串**：持仓/行情中的数值（如 `"300"`、`"18.09"`）为字符串类型，使用时注意转换。
- **日期格式 `YYYYMMDD`**：资产趋势返回的 `date` 为 `YYYYMMDD`（如 `20260827`），展示时转为 `YYYY-MM-DD`。
- **断线自动重试**：工具调用失败（CDP 连接断开）时重试一次即可，底层会自动重连；连续两次失败需调用 `tzzb_login` 重新认证。

## 技术架构

```
AI 助手（MCP Client）
      │  stdio
      ▼
tzzb-mcp（MCP Server, Python）
      │  Chrome DevTools Protocol :9222
      ▼
Chrome 浏览器（独立 Profile）
      │  浏览器原生 fetch（携带 Cookie）
      ▼
同花顺投资账本 API（tzzb.10jqka.com.cn）
```

- CDP 调试端口：`9222`
- 独立 Chrome Profile：`~/.tzzb_chrome_profile`
- Cookie 持久化：`~/.tzzb_cookies.json`（有效期约 7 天）
- 全局锁保证串行调用，CDP 断开自动重连

### 目录结构

```
tzzb-mcp/
├── pyproject.toml        # 项目配置与依赖
├── src/
│   ├── server.py         # MCP 服务入口（工具注册）
│   ├── auth.py           # 登录、Cookie 提取与持久化
│   ├── client.py         # Chrome CDP 连接与请求代理
│   ├── models.py         # 数据模型
│   └── api/              # 各业务接口封装
│       ├── account.py    # 账户列表 / 总览
│       ├── position.py   # 持仓明细
│       ├── market.py     # 行情 / 汇率 / 交易日
│       ├── trade.py      # 交易记录 / 分时收益 / 资产趋势
│       └── watchlist.py  # 自选列表
└── SKILL.md              # AI 助手使用技能文档（工具详细说明）
```

## 排错指南

| 现象 | 原因 | 解决 |
|------|------|------|
| 报「未登录」错误 | Cookie 不存在或已过期 | 调用 `tzzb_login` 重新登录 |
| CDP 请求失败 | Chrome 未运行或连接断开 | 底层自动重连，重试一次即可；仍失败则调用 `tzzb_login` |
| 基金持仓返回空 / 报错 | `merge_fund` 接口已失效（HTTP 400） | 已内置保护，忽略 `fund` 字段即可 |
| `tzzb_portfolio` 返回空数据 | `get_account_init` 接口不可用 | 已内置回退到 `get_account_list`，不影响使用 |
| Chrome 无法自动启动 | — | 手动启动：`chrome --remote-debugging-port=9222 --remote-allow-origins=*` |

## License

[Apache License 2.0](LICENSE)
