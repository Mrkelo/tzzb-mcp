---
name: tzzb-mcp
description: "通过同花顺投资账本 MCP 查询个人多账户持仓、资产趋势、交易记录、实时行情和自选列表。需要先登录。"
description_zh: "通过同花顺投资账本 MCP 查询个人多账户持仓、资产趋势、交易记录、实时行情和自选列表。需要先登录。"
description_en: "Query personal multi-account positions, asset trends, trade records, real-time quotes, and watchlists via Tonghuashun Investment Ledger MCP."
version: "1.0.0"
agent_created: true
---

# 同花顺投资账本 MCP

本 Skill 提供同花顺投资账本（tzzb.10jqka.com.cn）的完整数据查询能力，覆盖多账户持仓、资产趋势、交易记录、实时行情和自选列表。

## 使用规则（强制）

### 1. 禁止并行调用

所有工具共享同一个 Chrome CDP 连接，底层有全局锁保护。**一次只能调用一个工具，绝对不要并行调用多个 tzzb-mcp 工具**。并行调用会排队串行执行，但不必要的等待会浪费时间。

**错误**：同时调用 `tzzb_account_list` + `tzzb_positions` + `tzzb_stock_quotes`
**正确**：先调 `tzzb_account_list`，拿到结果后再调 `tzzb_positions`，最后调 `tzzb_stock_quotes`

### 2. 查询持仓必须先获取账户列表

位置数据的 `fund_key` 和 `manual_id` 来自 `tzzb_account_list`。**不要直接调用 `tzzb_positions` 不传参数**——不传参数返回的是所有账户的聚合数据（可能为空）。正确流程：

```
tzzb_account_list → 获取 fund_key → tzzb_positions(fund_key="xxx")
```

### 3. 行情查询需要市场前缀

`tzzb_stock_quotes` 的 codes 格式为 `市场:代码`，不是纯数字：
- 上证：`33:600519`
- 深证：`47:000001`
- 从持仓数据中获取的代码需要根据 market 字段判断加前缀。持仓中 `market: "2"` 通常对应上海（33），`market: "1"` 对应深圳（47）。

### 4. 基金持仓不可用

`tzzb_positions` 返回的 `fund` 字段始终为 `{"error": "基金持仓接口不可用"}`，**忽略 fund 字段，只使用 stock 数据**。不要尝试调基金相关参数。

### 5. 断线后自动重试

如果某个工具调用失败（CDP 连接断开），**重试一次即可**，底层会自动重连。如果连续两次失败，则需调用 `tzzb_login` 重新认证。

### 6. 数据展示注意事项

- 行情字段名为拼音缩写：`xianjia`=现价、`zuoshou`=昨收、`zqdm`=代码、`scdm`=市场
- 持仓数据中的数值字段可能是字符串类型（如 `"300"`、`"18.09"`），展示时需注意
- 资产趋势中的日期格式为 `YYYYMMDD`（如 `20260827`），展示时转为 `YYYY-MM-DD`

---

## 前置条件

**首次使用必须先调用 `tzzb_login`**。该工具会启动 Chrome 调试实例，用户需在浏览器中登录投资账本后 Cookie 自动提取。已登录的状态下后续调用无需重复登录。

## 可用工具总览

| 工具名 | 用途 | 优先级 |
|--------|------|:------:|
| `tzzb_login` | 登录投资账本，提取 Cookie | 🔴 首次必调 |
| `tzzb_login_status` | 检查当前登录状态 | 🟡 状态检查 |
| `tzzb_account_list` | 获取所有账户列表（含 fund_key、manual_id） | 🟢 最常用 |
| `tzzb_positions` | 获取持仓明细（股票+基金） | 🟢 最常用 |
| `tzzb_portfolio` | 投资组合总览（同 account_summary，含回退） | 🟢 常用 |
| `tzzb_account_summary` | 账户总览（同 portfolio，含回退） | 🟢 常用 |
| `tzzb_asset_trend` | 获取资产/收益趋势数据 | 🟡 趋势分析 |
| `tzzb_time_share` | 获取分时收益数据 | 🟡 盘中监控 |
| `tzzb_trade_records` | 获取当日交易记录 | 🟡 交易查询 |
| `tzzb_stock_quotes` | 获取股票实时行情 | 🟡 行情查询 |
| `tzzb_exchange_rate` | 获取港元兑人民币汇率 | 🟠 港股辅助 |
| `tzzb_trade_day` | 获取最近交易日信息 | 🟠 辅助 |
| `tzzb_watchlist` | 获取自选股票和基金列表 | 🟠 自选查询 |

> 用户问"我的持仓"、"账户情况"、"赚了多少" → 优先用 `tzzb_account_list` + `tzzb_positions`

---

## 工具详细说明

### tzzb_login — 登录投资账本

**首次使用必须调用**。启动 Chrome 调试实例，在浏览器中登录投资账本后自动提取 Cookie 并持久化。

**参数**：无

**返回**：
```json
{
  "status": "success",
  "message": "Cookie 有效，userid=612790***",
  "cookies": {"userid": "612790***", "ticket": "abc123***", "user": "xxx***"}
}
```

**调用时机**：
- 首次使用 tzzb-mcp 任何工具之前
- 其他工具报 "未登录" 错误时
- Cookie 过期（401 错误）时

**注意**：调用后会弹出 Chrome 窗口，用户需手动登录投资账本。如果已有有效 Cookie（独立 Profile 持久化），会直接返回成功无需手动登录。

---

### tzzb_login_status — 检查登录状态

**参数**：无

**返回**：
```json
{
  "logged_in": true,
  "userid": "612790",
  "cookie_count": 3,
  "extracted_at": "2026-08-27T08:30:00",
  "message": "已登录"
}
```

---

### tzzb_account_list — 账户列表 ⭐

获取所有账户的基本信息，是获取 `fund_key` 和 `manual_id` 的唯一入口。

**参数**：无

**返回结构**（按账户类型分组的列表）：
```json
{
  "rzrq": [],           // 融资融券账户列表
  "common": [           // 券商账户列表
    {
      "fund_key": "67091641",
      "brokername": "股票账户*4726",
      "manual_id": "",
      "manualname": "股票账户",
      "qsid": "83",
      "broker_type": "20"
    }
  ],
  "fund": [],           // 基金账户列表
  "manual": [           // 手工账户列表
    {
      "manual_id": 2238098,
      "manualname": "广发2021",
      "fund_key": 2238098,
      "brokername": "pc手工账户",
      "broker_type": "0"
    }
  ]
}
```

**关键字段**：
- `fund_key` — 券商账户标识，用于 tzzb_positions 等工具
- `manual_id` — 手工账户标识，用于 tzzb_positions 等工具
- `brokername` / `manualname` — 账户显示名称
- `broker_type` — `"20"` 为券商账户，`"0"` 为手工账户

**调用时机**：用户问"我有几个账户"、"各账户分别什么情况"、需要获取 fund_key/manual_id 时

---

### tzzb_account_summary / tzzb_portfolio — 账户总览

两者功能相同，都返回账户总览数据。优先尝试 `get_account_init()`，失败时回退到 `get_account_list()`。

**参数**：无

**调用时机**：用户问"我的账户情况"、"今天赚了多少"、"总资产多少"、"收益率怎么样"

**注意**：实际返回数据取决于底层 API 状态，可能返回账户列表而非汇总数据。如需精确数据，建议使用 `tzzb_account_list` + `tzzb_positions` 组合。

---

### tzzb_positions — 持仓明细 ⭐

获取股票和基金的持仓明细。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| manual_id | string | - | 手工账户 ID，从 tzzb_account_list 的 manual 列表中获取 |
| fund_key | string | - | 券商账户 key，从 tzzb_account_list 的 common 列表中获取 |
| rzrq_fund_key | string | - | 融资融券账户 key（仅用于股票持仓查询，基金不支持） |

**不传参数时**：返回所有账户的持仓数据

**返回**：
```json
{
  "stock": { ... },   // 股票持仓详情
  "fund": { ... }     // 基金持仓详情（如接口不可用，返回 {"error": "基金持仓接口不可用"}）
}
```

**股票持仓数据结构**（实测）：
```json
{
  "money_remain": 0,
  "position": [
    {
      "code": "601166",
      "name": "兴业银行",
      "count": "300",
      "price": "18.14",
      "value": "5442.00"
    }
  ],
  "position_rate": "",
  "total_asset": 0,
  "total_liability": 0,
  "total_value": 0,
  "upload_time": ""
}
```

**注意**：基金持仓接口（merge_fund）返回 HTTP 400，已内置异常保护，基金异常时不影响股票数据返回。

**调用时机**：用户问"持有哪些股票"、"某某股票持仓多少"、"仓位分布"

---

### tzzb_asset_trend — 资产趋势

获取资产/收益的历史趋势数据。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| manual_id | string | - | 手工账户 ID |
| fund_key | string | - | 券商账户 key |
| rzrq_fund_key | string | - | 融资融券账户 key |
| start_date | string | - | 起始日期，格式 YYYY-MM-DD |
| end_date | string | - | 结束日期，格式 YYYY-MM-DD |

**返回结构**：
```json
{
  "total_asset": [{"asset": 56557.27, "date": "20260827", "profit": 282.92, "zczs": 398.52}],
  "month_profit": [{"asset": 56557.27, "date": "20260827", "profit": -791.67, "zczs": 398.52}],
  "year_profit": [{"asset": 56557.27, "date": "20260827", "profit": 3156.18, "zczs": 398.52}],
  "month_init_zczs": 404.07,
  "year_init_zczs": 375.30
}
```

**关键字段**：`asset`（资产）、`date`（日期 YYYYMMDD）、`profit`（盈亏）、`zczs`（净值指数）

**调用时机**：用户问"最近收益走势"、"资产变化趋势"、"某段时间赚了多少"

---

### tzzb_time_share — 分时收益

获取当日分时收益数据。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| manual_id | string | - | 手工账户 ID |
| fund_key | string | - | 券商账户 key |
| rzrq_fund_key | string | - | 融资融券账户 key |

**返回**：`{"data": [...]}` 分时数据点数组

**调用时机**：用户问"今天盘中收益怎么样"、"实时盈亏"

---

### tzzb_trade_records — 交易记录

获取当日交易记录。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| manual_id | string | - | 手工账户 ID |
| fund_key | string | - | 券商账户 key |
| rzrq_fund_key | string | - | 融资融券账户 key |

**返回**：`{"data": [...], "fl": 0.0003, "userid": "..."}` — `data` 为交易记录数组（无交易时为空数组），`fl` 为费率

**调用时机**：用户问"今天有什么交易"、"今天买了什么"

---

### tzzb_stock_quotes — 股票行情

获取股票实时行情数据。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| codes | string | ✅ | 股票代码，格式 `市场:代码`，多个用逗号分隔 |
| date | string | - | 指定日期，格式 YYYY-MM-DD，不传则返回最新 |

**市场代码映射**：
- `33` — 上证（如 `33:600519` 贵州茅台）
- `47` — 深证（如 `47:000001` 平安银行）

**返回**：列表格式，每个元素为：
```json
[
  {"xianjia": "1440.00", "zqdm": "600519", "scdm": "33", "zuoshou": "1435.00"}
]
```

**字段说明**：`xianjia`（现价）、`zqdm`（证券代码）、`scdm`（市场代码）、`zuoshou`（昨收价）

**注意**：无效股票代码或错误市场代码不会报错，但 `xianjia` 会返回空字符串。

**调用时机**：用户问"当前股价多少"、"查一下某只股票行情"

---

### tzzb_exchange_rate — 汇率

获取港元兑人民币汇率。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | - | 指定日期，不传则返回最新 |

**返回**：
```json
{"before_date": "20260826", "date": "20260827", "before_rate": "0.857700", "rate": "0.857200"}
```

**调用时机**：用户问"港股汇率多少"、"港币汇率"

---

### tzzb_trade_day — 交易日

获取最近交易日信息。

**参数**：无

**返回**：
```json
{
  "last_hk_trading_day": "2026-08-27",
  "prev_trading_day": "2026-08-25",
  "next_trading_day": "2026-08-28"
}
```

**调用时机**：需要确认今天是否交易日

---

### tzzb_watchlist — 自选列表

获取自选股票和基金列表。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| sort_rule | string | - | 排序规则 |
| sort_order | string | - | 排序方向 |

**返回**：`{"self_version": 997, "list": [...]}` — `list` 为自选项数组，`self_version` 用于增量更新

**调用时机**：用户问"我的自选股有哪些"

---

## 典型使用流程

### 首次使用

```
1. tzzb_login           → 弹出 Chrome，用户登录
2. tzzb_account_list    → 获取所有账户的 fund_key / manual_id
3. tzzb_positions       → 查看持仓明细
```

### 日常查询

```
1. tzzb_account_list    → 获取账户列表
2. tzzb_positions       → 查看具体持仓
3. tzzb_asset_trend     → 查看收益走势（可选）
```

### 账户结构分析

```
1. tzzb_account_list            → 获取所有账户 ID
2. tzzb_positions fund_key="xxx" → 查特定券商账户持仓
3. tzzb_positions manual_id="xxx" → 查特定手工账户持仓
```

---

## 关键概念

### 账户 ID 体系

投资账本有两种账户标识，从 `tzzb_account_list` 返回中获取：

| 标识 | 说明 | 来源 |
|------|------|------|
| `fund_key` | 券商账户 key | `common` 列表中的 `fund_key` 字段 |
| `manual_id` | 手工账户 ID | `manual` 列表中的 `manual_id` 字段 |
| `rzrq_fund_key` | 融资融券账户 key | `rzrq` 列表中（如有） |

### 技术架构

- 所有 API 请求通过 Chrome CDP（端口 9222）在浏览器内执行 fetch
- Chrome 使用独立 Profile（`~/.tzzb_chrome_profile`），不影响用户日常 Chrome
- Cookie 持久化在 `~/.tzzb_cookies.json`
- 内置断线重连机制：CDP 连接断开时自动重连重试一次

---

## 排错指南

| 现象 | 原因 | 解决 |
|------|------|------|
| "未登录" 错误 | Cookie 不存在或已过期 | 调用 `tzzb_login` 重新登录 |
| CDP 请求失败 | Chrome 未运行或连接断开 | 自动重连，重试即可；仍失败则调用 `tzzb_login` |
| 基金持仓返回空/报错 | merge_fund 接口已失效（HTTP 400） | 已内置保护，基金异常不影响股票数据；忽略 fund 字段即可 |
| tzzb_portfolio 返回空数据 | get_account_init 接口不可用 | 已内置回退到 get_account_list，不影响使用 |

---

## 注意事项

- 首次使用需要手动在 Chrome 中登录投资账本
- 系统需安装 Chrome 浏览器
- Cookie 有效期约 7 天，过期后需重新登录
- 如果 Chrome 无法自动启动，手动启动：`chrome --remote-debugging-port=9222 --remote-allow-origins=*`
- 行情返回的字段名为拼音缩写（如 `xianjia`=现价、`zuoshou`=昨收），展示时需映射为中文
- 不传参数调用 `tzzb_positions` 时返回所有账户的持仓聚合数据，传 `fund_key` 可精确查询特定账户