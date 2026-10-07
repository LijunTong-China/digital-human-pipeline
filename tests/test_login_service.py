#!/usr/bin/env python3
"""login-hub-service 单元验证程序

验证阶段1的所有功能点，确保服务正常运行。

运行方式：
    python test_login_service.py

依赖：requests, time, concurrent.futures
"""
import json
import sys
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ 缺少依赖：pip install requests")
    exit(1)


# 配置
BASE_URL = "http://localhost:3459"
TEST_RESULTS: List[Dict[str, Any]] = []


class TestResult:
    """测试结果记录器"""

    @staticmethod
    def record(
        test_name: str,
        passed: bool,
        result: str,
        method: str = "GET",
        url: str = "",
        error: str = "",
    ) -> None:
        """记录测试结果"""
        TEST_RESULTS.append({
            "测试项": test_name,
            "方法": method,
            "URL": url,
            "状态": "✅ 通过" if passed else "❌ 失败",
            "结果": result,
            "错误": error if error else "-",
            "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    @staticmethod
    def print_summary() -> None:
        """打印测试总结"""
        passed = sum(1 for r in TEST_RESULTS if r["状态"] == "✅ 通过")
        total = len(TEST_RESULTS)
        print(f"\n{'='*80}")
        print(f"测试总结：{passed}/{total} 通过 ({passed/total*100:.1f}%)")
        print(f"{'='*80}")

    @staticmethod
    def print_table() -> None:
        """打印测试结果表格"""
        print(f"\n{'='*100}")
        print(f"{'测试项':<30} {'状态':<10} {'结果'}")
        print(f"{'='*100}")
        for result in TEST_RESULTS:
            print(f"{result['测试项']:<30} {result['状态']:<10} {result['结果'][:50]}...")


class LoginServiceTester:
    """抖音登录服务测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        expected_status: int = 200,
    ) -> Tuple[bool, Dict[str, Any], str]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                return False, {}, f"不支持的HTTP方法: {method}"

            if response.status_code == expected_status:
                return True, response.json() if response.text else {}, ""
            else:
                return False, {}, f"HTTP状态码: {response.status_code}, 期望: {expected_status}"
        except Exception as e:
            return False, {}, f"请求异常: {str(e)}"

    def test_health_check(self) -> None:
        """测试健康检查接口"""
        success, data, error = self._request("GET", "/api/health")
        if success and data.get("browser_running") is not None:
            TestResult.record(
                test_name="健康检查接口",
                passed=True,
                result=f"browser_running={data.get('browser_running')}",
                url="/api/health"
            )
        else:
            TestResult.record(
                test_name="健康检查接口",
                passed=False,
                result="失败",
                error=error
            )

    def test_login_status(self) -> None:
        """测试抖音登录状态接口"""
        success, data, error = self._request("GET", "/api/quant/login_status/douyin")
        if success and "logged_in" in data:
            TestResult.record(
                test_name="抖音登录状态",
                passed=True,
                result=f"logged_in={data.get('logged_in')}",
                url="/api/quant/login_status/douyin"
            )
        else:
            TestResult.record(
                test_name="抖音登录状态",
                passed=False,
                result="失败",
                error=error
            )

    def test_login_status_all(self) -> None:
        """测试所有平台登录状态接口"""
        success, data, error = self._request("GET", "/api/quant/login_status_all")
        if success and "douyin" in data:
            TestResult.record(
                test_name="跨平台登录状态",
                passed=True,
                result=f"包含douyin平台信息",
                url="/api/quant/login_status_all"
            )
        else:
            TestResult.record(
                test_name="跨平台登录状态",
                passed=False,
                result="失败",
                error=error
            )

    def test_manual_keepalive(self) -> None:
        """测试手动保活接口"""
        success, data, error = self._request("POST", "/api/quant/keepalive/douyin")
        if success and "logged_in" in data:
            TestResult.record(
                test_name="手动保活接口",
                passed=True,
                result=f"保活完成，logged_in={data.get('logged_in')}",
                method="POST",
                url="/api/quant/keepalive/douyin"
            )
        else:
            TestResult.record(
                test_name="手动保活接口",
                passed=False,
                result="失败",
                method="POST",
                error=error
            )

    def test_open_login_tab(self) -> None:
        """测试打开登录页接口"""
        success, data, error = self._request("POST", "/api/quant/open-login-tab/douyin")
        if success:
            # 已登录时会返回 success=False, message="已登录"，这也是正确行为
            if data.get("message") in ["已登录", "已打开抖音页面，请在浏览器中扫码登录"]:
                TestResult.record(
                    test_name="打开登录页接口",
                    passed=True,
                    result=f"消息: {data.get('message')}",
                    method="POST",
                    url="/api/quant/open-login-tab/douyin"
                )
                return

        TestResult.record(
            test_name="打开登录页接口",
            passed=False,
            result="失败",
            method="POST",
            error=error
        )

    def test_error_handling(self) -> None:
        """测试错误处理（不存在的平台）"""
        success, data, error = self._request("GET", "/api/quant/login_status/xiaohongshu")
        if not success and "404" in error:
            TestResult.record(
                test_name="错误处理（不存在的平台）",
                passed=True,
                result=f"正确返回404: {error}",
                url="/api/quant/login_status/xiaohongshu"
            )
        else:
            TestResult.record(
                test_name="错误处理（不存在的平台）",
                passed=False,
                result="失败",
                error=f"应返回404，实际: {error}"
            )

    def test_performance(self) -> None:
        """测试性能（响应时间）"""
        times = []
        for _ in range(5):
            start = time.time()
            success, _, _ = self._request("GET", "/api/quant/login_status/douyin")
            if success:
                times.append(time.time() - start)

        if len(times) == 5:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            result = f"平均: {avg_time*1000:.1f}ms, 范围: {min_time*1000:.1f}-{max_time*1000:.1f}ms"
            TestResult.record(
                test_name="性能测试（响应时间）",
                passed=True,
                result=result
            )
        else:
            TestResult.record(
                test_name="性能测试（响应时间）",
                passed=False,
                result="失败",
                error="多次请求失败"
            )

    def test_concurrent(self) -> None:
        """测试并发能力"""
        def make_request():
            return self._request("GET", "/api/health")[0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(results)
        if success_count == 10:
            TestResult.record(
                test_name="并发测试（10个请求）",
                passed=True,
                result="所有10个并发请求成功"
            )
        else:
            TestResult.record(
                test_name="并发测试（10个请求）",
                passed=False,
                result=f"失败",
                error=f"{success_count}/10 成功"
            )

    def test_browser_data_persistence(self) -> None:
        """测试浏览器数据持久化"""
        browser_data_dir = Path("browser_data/douyin")
        if browser_data_dir.exists():
            size_mb = sum(f.stat().st_size for f in browser_data_dir.rglob('*') if f.is_file()) / (1024 * 1024)
            has_local_storage = (browser_data_dir / "Default" / "Local Storage").exists()

            if has_local_storage and size_mb > 0:
                TestResult.record(
                    test_name="浏览器数据持久化",
                    passed=True,
                    result=f"数据目录大小: {size_mb:.1f}MB, Local Storage存在"
                )
            else:
                TestResult.record(
                    test_name="浏览器数据持久化",
                    passed=False,
                    result="失败",
                    error=f"大小: {size_mb:.1f}MB, Local Storage: {has_local_storage}"
                )
        else:
            TestResult.record(
                test_name="浏览器数据持久化",
                passed=False,
                result="失败",
                error="browser_data目录不存在"
            )

    def test_frontend_page(self) -> None:
        """测试前端页面"""
        success, _, error = self._request("GET", "/")
        if success:
            # 检查是否是HTML页面
            response = requests.get(f"{self.base_url}/")
            if "html" in response.headers.get("content-type", "") and "账号登录中心" in response.text:
                TestResult.record(
                    test_name="前端页面展示",
                    passed=True,
                    result="HTML正常渲染，包含标题"
                )
            else:
                TestResult.record(
                    test_name="前端页面展示",
                    passed=False,
                    result="失败",
                    error="Content-Type或标题不正确"
                )
        else:
            TestResult.record(
                test_name="前端页面展示",
                passed=False,
                result="失败",
                error=error
            )

    def run_all_tests(self) -> None:
        """运行所有测试"""
        print(f"{'='*80}")
        print(f"login-hub-service 单元验证程序")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"服务地址: {self.base_url}")
        print(f"{'='*80}\n")

        # 检查服务是否运行
        success, _, error = self._request("GET", "/api/health")
        if not success:
            print(f"❌ 服务无法访问: {error}")
            print("请确保服务已启动: uvicorn main:app --host 0.0.0.0 --port 3459")
            return

        print("✅ 服务可访问，开始测试...\n")

        # 运行所有测试
        tests = [
            ("健康检查接口", self.test_health_check),
            ("抖音登录状态", self.test_login_status),
            ("跨平台登录状态", self.test_login_status_all),
            ("手动保活接口", self.test_manual_keepalive),
            ("打开登录页接口", self.test_open_login_tab),
            ("错误处理", self.test_error_handling),
            ("性能测试", self.test_performance),
            ("并发测试", self.test_concurrent),
            ("浏览器数据持久化", self.test_browser_data_persistence),
            ("前端页面展示", self.test_frontend_page),
        ]

        for test_name, test_func in tests:
            print(f"测试: {test_name}...", end=" ")
            test_func()
            result = TEST_RESULTS[-1]
            print(result["状态"])

        # 打印结果
        TestResult.print_table()
        TestResult.print_summary()

        # 保存结果到JSON文件
        self.save_results()

    def save_results(self) -> None:
        """保存测试结果到JSON文件（统一放在 logs/ 目录）"""
        logs_dir = Path(__file__).resolve().parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        output_file = logs_dir / f"test_login_service_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_tests": len(TEST_RESULTS),
                "passed_tests": sum(1 for r in TEST_RESULTS if r["状态"] == "✅ 通过"),
                "results": TEST_RESULTS,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: {output_file}")


class _Tee:
    """同时输出到控制台和日志文件"""
    def __init__(self, log_path: Path):
        self._console = sys.stdout
        log_path.parent.mkdir(exist_ok=True)
        self._file = open(log_path, 'w', encoding='utf-8')

    def write(self, msg: str) -> None:
        self._console.write(msg)
        self._file.write(msg)

    def flush(self) -> None:
        self._console.flush()
        self._file.flush()


def main():
    """主函数（控制台输出同时写入 logs/ 目录）"""
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    log_file = logs_dir / f"test_login_service_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    sys.stdout = _Tee(log_file)
    print(f"日志文件: {log_file}")
    tester = LoginServiceTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()