"""抖音爬虫 - 通过阶段1登录态服务抓取真实数据

架构: 爬虫不直接对抗抖音风控，而是调用 login-hub-service (3459) 的
浏览器能力接口（fetch/search/video_detail），复用真实登录态。
取播放地址优先走 iesdouyin 分享链接（免签名）。
"""
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger("douyin_crawler")


class LoginServiceClient:
    """阶段1登录态服务的客户端"""

    def __init__(self, base_url: str = "http://localhost:3459"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/api/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def login_status(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/api/quant/login_status/douyin", timeout=10)
            return r.json().get("logged_in", False)
        except Exception:
            return False

    def cookies(self) -> Dict[str, str]:
        try:
            r = self.session.get(f"{self.base_url}/api/quant/cookies/douyin", timeout=30)
            return r.json().get("cookies", {})
        except Exception as e:
            logger.error(f"获取cookies失败: {e}")
            return {}

    def fetch_page(self, url: str, wait_ms: int = 5000, scroll_times: int = 0) -> Optional[Dict[str, Any]]:
        """用登录态浏览器打开URL，返回 {title, html, cookies, captcha}"""
        try:
            r = self.session.post(
                f"{self.base_url}/api/quant/fetch/douyin",
                json={"url": url, "wait_ms": wait_ms, "scroll_times": scroll_times},
                timeout=120,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"页面抓取失败: {e}")
            return None

    def search(self, keyword: str, wait_ms: int = 6000, scroll_times: int = 3) -> Optional[Dict[str, Any]]:
        """真实用户行为搜索（首页输入→回车），返回渲染后HTML"""
        try:
            r = self.session.post(
                f"{self.base_url}/api/quant/search/douyin",
                json={"keyword": keyword, "wait_ms": wait_ms, "scroll_times": scroll_times},
                timeout=180,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return None


class DouyinCrawler:
    """抖音爬虫: 创作者视频同步 + 分享链接取播放地址"""

    SHARE_PREFIX = "https://www.iesdouyin.com/share/video/"

    def __init__(self, login_service_url: str = "http://localhost:3459"):
        self.login = LoginServiceClient(login_service_url)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Referer": "https://www.douyin.com/",
        })

    # ---------- 创作者视频同步 ----------

    def get_creator_videos(self, sec_user_id: str, max_videos: int = 10) -> List[Dict[str, Any]]:
        """抓取创作者主页最新视频（真实登录态）

        sec_user_id: 抖音创作者的 sec_uid（形如 MS4wLjABAAAA...）
        """
        if not self.login.health():
            logger.error("登录态服务不可用")
            return []

        url = f"https://www.douyin.com/user/{sec_user_id}"
        result = self.login.fetch_page(url, wait_ms=6000, scroll_times=2)
        if not result:
            return []

        if result.get("captcha"):
            logger.warning("主页抓取触发验证码")
            return []

        html = result.get("html", "")
        return self._parse_video_list(html, max_videos)

    def _parse_video_list(self, html: str, max_videos: int) -> List[Dict[str, Any]]:
        """从主页HTML解析视频列表（按出现顺序=最新优先）

        标题优先取页面JSON里的 desc（主页SSR的JSON是 \\" 转义的，需先反转义）
        """
        videos: List[Dict[str, Any]] = []
        seen = set()

        # 反转义后建立 aweme_id → {desc, duration} 映射
        decoded = html.replace('\\"', '"')
        json_map: Dict[str, Dict[str, Any]] = {}
        for m in re.finditer(r'"aweme_id":"(\d{15,20})"', decoded):
            seg = decoded[m.start(): m.start() + 4000]
            desc_m = re.search(r'"desc":"(.{2,200}?)"', seg)
            dur_m = re.search(r'"duration":(\d{3,8})', seg)
            json_map[m.group(1)] = {
                "desc": desc_m.group(1).encode().decode("unicode_escape", errors="ignore").strip() if desc_m else "",
                "duration_sec": int(dur_m.group(1)) // 1000 if dur_m else 0,
            }

        # 主页SSR用 /video/<id> 链接
        for m in re.finditer(r'<a[^>]*?href="[^"]*?/video/(\d{15,20})[^"]*"[^>]*>', html):
            vid = m.group(1)
            if vid in seen:
                continue
            seen.add(vid)

            tag = m.group(0)
            title = ""
            for attr in ("title", "aria-label"):
                tm = re.search(rf'{attr}="([^"]{{2,150}})"', tag)
                if tm:
                    title = tm.group(1).strip()
                    break
            if not title:
                seg = html[m.end(): m.end() + 500]
                tm = re.search(r'<(?:p|span|div)[^>]*>([^<]{5,80})</', seg)
                if tm:
                    title = tm.group(1).strip()
            title = (title.replace("&quot;", '"').replace("&amp;", "&")
                          .replace("&#39;", "'").replace("&nbsp;", " "))

            meta = json_map.get(vid, {})
            if not title and meta.get("desc"):
                title = meta["desc"]

            videos.append({
                "aweme_id": vid,
                "title": title or "(无标题)",
                "duration_sec": meta.get("duration_sec") or 0,
                "share_url": f"{self.SHARE_PREFIX}{vid}",
            })
            if len(videos) >= max_videos:
                break

        logger.info(f"解析到 {len(videos)} 个视频 (JSON补全: {len(json_map)})")
        return videos

    # ---------- 播放地址（免签名分享链接） ----------

    def get_play_url(self, aweme_id: str) -> Optional[str]:
        """通过分享链接获取无水印播放地址（三级fallback）

        1. 直连share页（免签名，大多数视频可用）
        2. 登录态浏览器抓share页
        3. 登录态浏览器抓详情页（RENDER_DATA里的playApi）
        """
        share_url = f"{self.SHARE_PREFIX}{aweme_id}"

        # 1) 直连share页
        try:
            r = self.session.get(share_url, timeout=30, allow_redirects=True)
            r.raise_for_status()
            url = self._extract_play_from_html(r.text)
            if url:
                logger.info(f"获取播放地址成功(share直连): {aweme_id}")
                return url
        except Exception as e:
            logger.warning(f"share直连失败: {aweme_id} - {e}")

        # 2) 登录态浏览器抓share页
        if self.login.health():
            result = self.login.fetch_page(share_url, wait_ms=3000)
            if result and not result.get("captcha"):
                url = self._extract_play_from_html(result.get("html", ""))
                if url:
                    logger.info(f"获取播放地址成功(share+登录态): {aweme_id}")
                    return url

            # 3) 登录态浏览器抓详情页
            result = self.login.fetch_page(f"https://www.douyin.com/video/{aweme_id}", wait_ms=5000)
            if result and not result.get("captcha"):
                html = result.get("html", "")
                # RENDER_DATA 里的 playApi
                decoded = html.replace('\\u002F', '/').replace('\\u0026', '&').replace('\\"', '"')
                pm = re.search(r'"playApi":"(/[^"]+|https://[^"]+)"', decoded)
                if pm:
                    p = pm.group(1)
                    url = ("https://www.douyin.com" + p) if p.startswith("//") else p
                    logger.info(f"获取播放地址成功(详情页playApi): {aweme_id}")
                    return url
                url = self._extract_play_from_html(html)
                if url:
                    logger.info(f"获取播放地址成功(详情页): {aweme_id}")
                    return url

        logger.warning(f"三种方式均未获取播放地址: {aweme_id}")
        return None

    def _extract_play_from_html(self, html: str) -> Optional[str]:
        """从HTML的 _ROUTER_DATA JSON中深度查找 play_addr.url_list"""
        m = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>', html, re.DOTALL)
        if not m:
            return None

        try:
            data = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"_ROUTER_DATA解析失败: {e}")
            return None

        def find_play(obj) -> Optional[List[str]]:
            if isinstance(obj, dict):
                pa = obj.get("play_addr") or obj.get("playAddr")
                if isinstance(pa, dict) and pa.get("url_list"):
                    return pa["url_list"]
                for v in obj.values():
                    found = find_play(v)
                    if found:
                        return found
            elif isinstance(obj, list):
                for v in obj:
                    found = find_play(v)
                    if found:
                        return found
            return None

        urls = find_play(data)
        return urls[0].replace("http://", "https://") if urls else None

    def download_video(self, play_url: str, output_path: str, cookies: Optional[Dict[str, str]] = None) -> bool:
        """下载视频文件"""
        try:
            headers = {"User-Agent": self.session.headers["User-Agent"]}
            if cookies:
                headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
            with self.session.get(play_url, headers=headers, timeout=180, stream=True) as r:
                r.raise_for_status()
                total = 0
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=256 * 1024):
                        f.write(chunk)
                        total += len(chunk)
            logger.info(f"视频下载完成: {output_path} ({total // 1024}KB)")
            return total > 10000
        except Exception as e:
            logger.error(f"视频下载失败: {e}")
            return False

    # ---------- 综合流程 ----------

    def capture_video(self, aweme_id: str, max_wait_seconds: int = 90) -> List[str]:
        """L3: 通过登录态浏览器拦截MSE媒体分段（音/视频轨分开成多个文件）

        返回落盘文件路径列表（登录服务data/media目录，与本项目同机，按字节数降序）。
        """
        try:
            r = self.session.post(
                f"{self.login.base_url}/api/quant/capture_video/douyin",
                json={"video_id": aweme_id, "max_wait_seconds": max_wait_seconds},
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()
            files = [f["path"] for f in data.get("files", []) if f.get("bytes", 0) > 10_000]
            logger.info(f"L3媒体捕获成功: {aweme_id} ({len(files)}条流/{data.get('total_bytes', 0)//1024}KB)")
            return files
        except Exception as e:
            logger.error(f"L3媒体捕获失败: {aweme_id} - {e}")
            return []

    def get_video_detail(self, aweme_id: str) -> Optional[Dict[str, Any]]:
        """登录态浏览器打开详情页并拦截 /aweme/detail XHR —— 最可靠的数据通道

        返回 {desc, play_urls, duration_sec, author, digg_count...}
        """
        try:
            r = self.session.post(
                f"{self.login.base_url}/api/quant/video_detail/douyin",
                json={"video_id": aweme_id, "wait_ms": 7000},
                timeout=150,
            )
            r.raise_for_status()
            det = (r.json().get("detail") or {}).get("aweme_detail") or {}
            if not det:
                return None
            pa = det.get("video", {}).get("play_addr", {})
            stats = det.get("statistics", {})
            return {
                "desc": det.get("desc", ""),
                "play_urls": pa.get("url_list", []),
                "duration_sec": (det.get("duration") or 0) // 1000,
                "author": det.get("author", {}).get("nickname", ""),
                "digg_count": stats.get("digg_count", 0),
                "comment_count": stats.get("comment_count", 0),
                "share_count": stats.get("share_count", 0),
                "collect_count": stats.get("collect_count", 0),
            }
        except Exception as e:
            logger.error(f"详情拦截失败: {aweme_id} - {e}")
            return None

    def fetch_video_for_transcribe(self, aweme_id: str, output_path: str) -> Optional[List[str]]:
        """下载链: L2a XHR拦截取播放地址直下 → L2b share直连 → L3 MSE分段捕获

        返回候选本地文件路径列表（按优先级），全部由调用方用后删除。
        """
        cookies = self.login.cookies()

        # L2a: 详情页XHR拦截的播放地址（登录态，最可靠）
        detail = self.get_video_detail(aweme_id) or {}
        for play_url in detail.get("play_urls", []):
            if self.download_video(play_url, output_path, cookies):
                return [output_path]
            logger.warning(f"L2a下载失败, 尝试下一个地址: {aweme_id}")

        # L2b: share直连
        play_url = self.get_play_url(aweme_id)
        if play_url and self.download_video(play_url, output_path, cookies):
            return [output_path]

        # L3: 浏览器分段捕获（音轨/视频轨多文件，转写侧会自动挑能用的）
        captured = self.capture_video(aweme_id)
        return captured or None


# 爬虫工厂
def get_crawler(login_service_url: str = "http://localhost:3459") -> DouyinCrawler:
    return DouyinCrawler(login_service_url)
