# login-hub-service：多平台登录中心

> 原 `douyin-login-service`，已重构为多平台通用登录中心。
> 对标调研系统 `LoginCenter / LoginQrcode / 账号管理页` 与 `/api/quant/*` 接口。
> 技术方案：**Playwright 持久化浏览器 + 人工登录 + 定时保活（token 不过期）**，编排框架 **LangGraph**。

## 已接入平台

douyin / bilibili / xiaohongshu / zhihu / weibo / toutiao

**新增一个网站 = 在 `config.py` 的 `PLATFORMS` 加一条注册项**（home、login_url、判定 Cookie、提示文案），其余全自动：登录、检测、保活、Cookies 导出、登录态代抓页面。

## 目录结构

```
login-hub-service/
├── main.py              # FastAPI 服务（通用接口 + 抖音特有能力）+ 保活调度
├── agent/
│   ├── state.py         # LangGraph 工作流状态（含 platform 字段）
│   ├── nodes.py         # 工作流节点（检测/开登录页/等登录/保活）
│   └── graph.py         # LangGraph StateGraph 组装与编译
├── browser/manager.py   # Playwright 持久化浏览器管理（每平台独立 context）
├── services/
│   ├── core.py          # 通用登录检测 / 登录 / 保活（配置驱动）
│   └── douyin.py        # 抖音入口（委托 core，可放抖音特有逻辑）
├── static/index.html    # 登录中心页
├── config.py            # 平台注册表 PLATFORMS + 全局配置
└── browser_data/<platform>/  # 各平台浏览器用户数据（Cookie 持久化，自动生成）
```

## LangGraph 工作流（按 platform 参数执行）

```
check_login ──已登录──▶ finish
   │未登录
   ├─ action=login ───▶ open_login_page ─▶ wait_for_scan ─┬成功▶ finish
   │                                                      └超时▶ 重开登录页(1次)▶ finish
   └─ action=keepalive ─▶ keepalive_touch ─▶ finish
```

## 安装与运行

```bash
cd login-hub-service
pip install -r requirements.txt
python -m playwright install chromium
uvicorn main:app --host 0.0.0.0 --port 3459
```

打开 http://localhost:3459/ → 登录中心页 → 点击对应平台"登录"，在弹出的浏览器中扫码/登录。
注意：浏览器是**懒启动**的，服务启动后第一次保活或第一次请求触发时才会弹出窗口。

## 接口（多平台通用）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/quant/platforms` | 已接入平台列表 |
| GET | `/api/quant/login_status_all` | 所有平台登录状态 |
| GET | `/api/quant/login_status/{platform}` | 单平台登录状态 |
| POST | `/api/quant/open-login-tab/{platform}` | 打开登录页并等待人工登录（最长5分钟） |
| POST | `/api/quant/keepalive/{platform}` | 手动触发保活（调试） |
| GET | `/api/quant/cookies/{platform}` | 导出 Cookies |
| POST | `/api/quant/fetch/{platform}` | 登录态浏览器代抓页面 |
| POST | `/api/quant/xhr_capture/{platform}` | 通用 XHR 拦截抓取 |
| POST | `/api/quant/search/douyin` | 抖音特有：真人行为搜索 |
| POST | `/api/quant/video_detail/douyin` | 抖音特有：视频详情拦截 |
| POST | `/api/quant/capture_video/douyin` | 抖音特有：媒体分段捕获 |
| GET | `/api/health` | 服务健康 |

## token 不过期机制

1. **持久化**：每平台独立 Chromium `user_data_dir`（`browser_data/<platform>`），登录一次后 Cookie/指纹落盘，重启不丢。
2. **保活**：后台每 30 分钟（`config.KEEPALIVE_INTERVAL_SECONDS`）自动访问各平台首页并滚动，刷新会话 Cookie。
3. **自愈提示**：保活发现掉登录时标记 `logged_in=false`，前端红点提示，人工重新登录即可。
