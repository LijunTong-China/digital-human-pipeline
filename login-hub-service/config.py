"""全局配置：多平台登录中心

新增一个网站只需在 PLATFORMS 里加一条注册项：
  - home:                 站点首页（Cookie 检测 / 保活访问）
  - login_url:            登录页（人工登录入口）
  - session_cookie_names: 登录态判定 Cookie（全部存在才算已登录）
  - login_hint:           给人工登录的提示文案
"""
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class PlatformConfig:
    name: str
    home: str
    login_url: str
    session_cookie_names: list[str] = field(default_factory=list)
    login_hint: str = "请在打开的浏览器中完成登录（扫码/账号均可）"


PLATFORMS: dict[str, PlatformConfig] = {
    "douyin": PlatformConfig(
        name="douyin",
        home="https://www.douyin.com",
        login_url="https://www.douyin.com/?recommend=1",
        # 抖音登录后必带 sessionid
        session_cookie_names=["sessionid", "sessionid_ss"],
        login_hint="未登录时抖音会自动弹出扫码弹窗，请扫码登录",
    ),
    "bilibili": PlatformConfig(
        name="bilibili",
        home="https://www.bilibili.com",
        login_url="https://passport.bilibili.com/login",
        session_cookie_names=["SESSDATA"],
        login_hint="请在B站登录页扫码或账密登录",
    ),
    "xiaohongshu": PlatformConfig(
        name="xiaohongshu",
        home="https://www.xiaohongshu.com",
        login_url="https://www.xiaohongshu.com",
        session_cookie_names=["web_session"],
        login_hint="未登录时小红书会弹出登录框，请扫码登录",
    ),
    "zhihu": PlatformConfig(
        name="zhihu",
        home="https://www.zhihu.com",
        login_url="https://www.zhihu.com/signin",
        session_cookie_names=["z_c0"],
        login_hint="请在知乎登录页扫码登录",
    ),
    "weibo": PlatformConfig(
        name="weibo",
        home="https://weibo.com",
        login_url="https://weibo.com/login.php",
        session_cookie_names=["SUB"],
        login_hint="请在微博登录页扫码或账密登录",
    ),
    "toutiao": PlatformConfig(
        name="toutiao",
        home="https://www.toutiao.com",
        login_url="https://www.toutiao.com",
        session_cookie_names=["sid_tt", "sessionid"],
        login_hint="未登录时头条会弹出登录框，请扫码登录",
    ),
}


def get_platform(name: str) -> PlatformConfig:
    if name not in PLATFORMS:
        raise KeyError(f"平台 {name} 尚未接入（已接入: {', '.join(PLATFORMS)}）")
    return PLATFORMS[name]


# 单窗口多标签：所有平台共用一个浏览器 profile（Cookie 按域名隔离，互不干扰）
USER_DATA_DIR = BASE_DIR / "browser_data" / "shared"

# CDP 调试端口：hub 浏览器带上此端口启动,发布模块(publish/)可接管同一浏览器实例,
# 共享登录态且不会与 hub 互抢 user_data_dir(0 = 不开)
CDP_PORT = 9340

# 保活间隔（秒）：定期访问各平台首页刷新会话，避免 token 过期
KEEPALIVE_INTERVAL_SECONDS = 30 * 60

# 扫码/人工登录等待（秒）：最长轮询时间
QR_WAIT_TIMEOUT_SECONDS = 300

# 登录状态检测轮询间隔（秒）
POLL_INTERVAL_SECONDS = 3

# L3媒体捕获目录（拦截CDN分段的临时存放，与热点监控服务同机可直读）
MEDIA_DIR = BASE_DIR / "data" / "media"

# 登录状态缓存（浏览器未运行时读这里，避免检测状态时弹窗）
STATUS_CACHE = BASE_DIR / "data" / "status_cache.json"

# 状态缓存有效期(秒):超过此时长的缓存只代表"上次检查时已登录",
# 不能当作当前登录态返回(cookie 可能已过期/被风控踢下线),必须降级为未验证
STATUS_CACHE_TTL_SECONDS = 12 * 3600
