#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点监控服务单元测试程序
测试阶段2的所有服务功能
"""

import unittest
import logging
import json
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 日志输出目录: <项目根>/logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# 配置日志（同时输出到控制台和 logs/ 目录）
log_file = os.path.join(LOGS_DIR, f"test_hotspot_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"日志文件: {log_file}")

try:
    from models.database import init_db, test_connection, get_db
    from services import (
        get_creator_service, get_video_service, get_transcribe_service, get_topic_service
    )
    from scheduler import scheduler
    from api.routes import app
    from fastapi.testclient import TestClient
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error("请确保项目依赖已安装: pip install -r hotspot-monitor-service/requirements.txt")
    sys.exit(1)


class HotspotMonitorServiceTest(unittest.TestCase):
    """热点监控服务测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        logger.info("开始热点监控服务单元测试")

        # 初始化数据库
        if not test_connection():
            logger.error("数据库连接测试失败")
            sys.exit(1)

        init_db()
        logger.info("数据库初始化完成")

        # 创建测试客户端
        cls.client = TestClient(app)

        # 获取服务实例
        cls.creator_service = get_creator_service()
        cls.video_service = get_video_service()
        cls.transcribe_service = get_transcribe_service()
        cls.topic_service = get_topic_service()

    def setUp(self):
        """每个测试方法前的准备"""
        # 清空数据库（仅用于测试）
        self._clear_test_data()

    def tearDown(self):
        """每个测试方法后的清理"""
        self._clear_test_data()

    def _clear_test_data(self):
        """清空测试数据"""
        try:
            db = next(get_db())
            # 清空所有表
            db.query(Topic).delete()
            db.query(Video).delete()
            db.query(Creator).delete()
            db.commit()
        except Exception as e:
            logger.error(f"清空测试数据失败: {e}")

    def test_creator_service(self):
        """测试创作者管理服务"""
        logger.info("测试创作者管理服务")

        # 测试创建创作者
        creator_data = {
            "nickname": "测试创作者",
            "platform": "douyin",
            "creator_id": "test123",
            "is_active": True,
            "sync_interval_hours": 24
        }

        creator = self.creator_service.create_creator(creator_data)
        self.assertIsNotNone(creator)
        self.assertEqual(creator.nickname, "测试创作者")
        self.assertEqual(creator.platform, "douyin")

        # 测试获取创作者
        fetched_creator = self.creator_service.get_creator(creator.id)
        self.assertIsNotNone(fetched_creator)
        self.assertEqual(fetched_creator.id, creator.id)

        # 测试更新创作者
        update_data = {"nickname": "更新后的创作者"}
        updated_creator = self.creator_service.update_creator(creator.id, update_data)
        self.assertIsNotNone(updated_creator)
        self.assertEqual(updated_creator.nickname, "更新后的创作者")

        # 测试删除创作者
        success = self.creator_service.delete_creator(creator.id)
        self.assertTrue(success)

    def test_video_service(self):
        """测试视频管理服务"""
        logger.info("测试视频管理服务")

        # 先创建创作者
        creator_data = {
            "nickname": "测试创作者",
            "platform": "douyin",
            "creator_id": "test123",
            "is_active": True,
            "sync_interval_hours": 24
        }
        creator = self.creator_service.create_creator(creator_data)

        # 测试创建视频
        video_data = {
            "creator_id": creator.id,
            "video_id": "test_video_123",
            "title": "测试视频",
            "published_at": datetime.utcnow(),
            "duration": 120,
            "stats_views": 1000,
            "stats_likes": 50,
            "stats_comments": 10,
            "stats_shares": 5
        }

        video = self.video_service.create_video(video_data)
        self.assertIsNotNone(video)
        self.assertEqual(video.title, "测试视频")

        # 测试获取视频
        fetched_video = self.video_service.get_video(video.id)
        self.assertIsNotNone(fetched_video)
        self.assertEqual(fetched_video.id, video.id)

        # 测试更新视频
        update_data = {"title": "更新后的视频"}
        updated_video = self.video_service.update_video(video.id, update_data)
        self.assertIsNotNone(updated_video)
        self.assertEqual(updated_video.title, "更新后的视频")

        # 测试删除视频
        success = self.video_service.delete_video(video.id)
        self.assertTrue(success)

    def test_transcribe_service(self):
        """测试转写服务"""
        logger.info("测试转写服务")

        # 先创建创作者和视频
        creator_data = {
            "nickname": "测试创作者",
            "platform": "douyin",
            "creator_id": "test123",
            "is_active": True,
            "sync_interval_hours": 24
        }
        creator = self.creator_service.create_creator(creator_data)

        video_data = {
            "creator_id": creator.id,
            "video_id": "test_video_123",
            "title": "测试视频",
            "published_at": datetime.utcnow(),
            "duration": 120,
            "stats_views": 1000,
            "stats_likes": 50,
            "stats_comments": 10,
            "stats_shares": 5
        }
        video = self.video_service.create_video(video_data)

        # 测试转写视频（模拟）
        # 注意：实际转写需要视频URL，这里使用模拟数据
        result = self.transcribe_service.transcribe_video(video.id, "deepseek")
        self.assertIsNotNone(result)
        self.assertIn("success", result)

        if result.get("success"):
            # 验证转写状态更新
            updated_video = self.video_service.get_video(video.id)
            self.assertEqual(updated_video.transcript_status, "done")

    def test_topic_service(self):
        """测试选题服务"""
        logger.info("测试选题服务")

        # 先创建创作者和视频
        creator_data = {
            "nickname": "测试创作者",
            "platform": "douyin",
            "creator_id": "test123",
            "is_active": True,
            "sync_interval_hours": 24
        }
        creator = self.creator_service.create_creator(creator_data)

        video_data = {
            "creator_id": creator.id,
            "video_id": "test_video_123",
            "title": "测试视频",
            "published_at": datetime.utcnow(),
            "duration": 120,
            "stats_views": 1000,
            "stats_likes": 50,
            "stats_comments": 10,
            "stats_shares": 5
        }
        video = self.video_service.create_video(video_data)

        # 测试从视频提取选题
        result = self.topic_service.extract_topics_from_video(video.id, "deepseek")
        self.assertIsNotNone(result)
        self.assertIn("success", result)

        if result.get("success"):
            # 验证选题创建
            topics = self.topic_service.get_topics(video_id=video.id)
            self.assertGreater(len(topics), 0)

    def test_api_routes(self):
        """测试API路由"""
        logger.info("测试API路由")

        # 测试健康检查
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")

        # 测试配置信息
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("environment", data)

    def test_scheduler(self):
        """测试调度器"""
        logger.info("测试调度器")

        # 测试调度器启动
        scheduler.start()
        self.assertTrue(scheduler.is_running())

        # 测试调度器停止
        scheduler.stop()
        self.assertFalse(scheduler.is_running())

    def test_end_to_end_flow(self):
        """端到端流程测试"""
        logger.info("端到端流程测试")

        # 1. 创建创作者
        creator_data = {
            "nickname": "测试创作者",
            "platform": "douyin",
            "creator_id": "test123",
            "is_active": True,
            "sync_interval_hours": 24
        }
        creator = self.creator_service.create_creator(creator_data)

        # 2. 创建视频
        video_data = {
            "creator_id": creator.id,
            "video_id": "test_video_123",
            "title": "测试视频",
            "published_at": datetime.utcnow(),
            "duration": 120,
            "stats_views": 1000,
            "stats_likes": 50,
            "stats_comments": 10,
            "stats_shares": 5
        }
        video = self.video_service.create_video(video_data)

        # 3. 转写视频
        result = self.transcribe_service.transcribe_video(video.id, "deepseek")
        self.assertTrue(result.get("success", False))

        # 4. 提取选题
        result = self.topic_service.extract_topics_from_video(video.id, "deepseek")
        self.assertTrue(result.get("success", False))

        # 5. 验证结果
        video = self.video_service.get_video(video.id)
        self.assertEqual(video.transcript_status, "done")

        topics = self.topic_service.get_topics(video_id=video.id)
        self.assertGreater(len(topics), 0)


def run_tests():
    """运行所有测试"""
    logger.info("开始运行热点监控服务单元测试")

    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HotspotMonitorServiceTest))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试结果
    logger.info(f"测试结果: 总数={result.testsRun}, 失败={len(result.failures)}, 错误={len(result.errors)}")

    # 生成JSON结果
    test_results = {
        "test_time": datetime.utcnow().isoformat(),
        "total_tests": result.testsRun,
        "passed_tests": result.testsRun - len(result.failures) - len(result.errors),
        "failed_tests": len(result.failures),
        "error_tests": len(result.errors),
        "results": []
    }

    for failure in result.failures:
        test_results["results"].append({
            "测试项": failure[0]._testMethodName,
            "状态": "❌ 失败",
            "错误信息": str(failure[1])
        })

    for error in result.errors:
        test_results["results"].append({
            "测试项": error[0]._testMethodName,
            "状态": "❌ 错误",
            "错误信息": str(error[1])
        })

    # 保存测试结果到文件
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    logger.info("测试结果已保存到 test_results.json")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)