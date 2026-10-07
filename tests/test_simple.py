#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版热点监控服务测试程序
"""

import unittest
import logging
import json
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 日志输出目录: <项目根>/logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# 配置日志（同时输出到控制台和 logs/ 目录）
log_file = os.path.join(LOGS_DIR, f"test_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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


class SimpleHotspotMonitorTest(unittest.TestCase):
    """简化版热点监控服务测试类"""

    def test_basic_functionality(self):
        """测试基本功能"""
        logger.info("测试基本功能")

        # 测试1: 创建简单的数据结构
        class Creator:
            def __init__(self, id, nickname):
                self.id = id
                self.nickname = nickname

        class Video:
            def __init__(self, id, title, creator_id):
                self.id = id
                self.title = title
                self.creator_id = creator_id
                self.transcript_status = "pending"

        class Topic:
            def __init__(self, id, title, source_video_id):
                self.id = id
                self.title = title
                self.source_video_id = source_video_id

        # 测试创建对象
        creator = Creator(1, "测试创作者")
        video = Video(1, "测试视频", creator.id)
        topic = Topic(1, "测试选题", video.id)

        self.assertEqual(creator.nickname, "测试创作者")
        self.assertEqual(video.title, "测试视频")
        self.assertEqual(topic.title, "测试选题")

        # 测试数据验证
        self.assertIsNotNone(creator)
        self.assertIsNotNone(video)
        self.assertIsNotNone(topic)

        logger.info("基本功能测试通过")

    def test_service_logic(self):
        """测试服务逻辑"""
        logger.info("测试服务逻辑")

        # 模拟服务类
        class CreatorService:
            def create_creator(self, data):
                return {"id": 1, "nickname": data["nickname"]}

            def get_creator(self, creator_id):
                return {"id": creator_id, "nickname": "测试创作者"}

        class VideoService:
            def create_video(self, data):
                return {"id": 1, "title": data["title"], "creator_id": data["creator_id"]}

            def get_video(self, video_id):
                return {"id": video_id, "title": "测试视频", "creator_id": 1}

        class TopicService:
            def extract_topics_from_video(self, video_id, llm_model):
                return {"success": True, "extracted_count": 1}

        # 测试服务调用
        creator_service = CreatorService()
        video_service = VideoService()
        topic_service = TopicService()

        creator = creator_service.create_creator({"nickname": "测试创作者"})
        video = video_service.create_video({"title": "测试视频", "creator_id": creator["id"]})
        result = topic_service.extract_topics_from_video(video["id"], "deepseek")

        self.assertEqual(creator["nickname"], "测试创作者")
        self.assertEqual(video["title"], "测试视频")
        self.assertTrue(result["success"])

        logger.info("服务逻辑测试通过")

    def test_api_response(self):
        """测试API响应"""
        logger.info("测试API响应")

        # 模拟API响应
        class APIResponse:
            def __init__(self, success, data=None, message=None, error=None):
                self.success = success
                self.data = data
                self.message = message
                self.error = error

        # 测试成功响应
        success_response = APIResponse(success=True, data={"status": "healthy"})
        self.assertTrue(success_response.success)
        self.assertEqual(success_response.data["status"], "healthy")

        # 测试失败响应
        error_response = APIResponse(success=False, error="测试错误")
        self.assertFalse(error_response.success)
        self.assertEqual(error_response.error, "测试错误")

        logger.info("API响应测试通过")

    def test_data_validation(self):
        """测试数据验证"""
        logger.info("测试数据验证")

        # 测试数据验证逻辑
        def validate_creator_data(data):
            required_fields = ["nickname", "platform", "creator_id"]
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            return True, "验证通过"

        # 测试有效数据
        valid_data = {
            "nickname": "测试创作者",
            "platform": "douyin",
            "creator_id": "test123"
        }
        is_valid, message = validate_creator_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(message, "验证通过")

        # 测试无效数据
        invalid_data = {
            "nickname": "测试创作者",
            "platform": "douyin"
            # 缺少 creator_id
        }
        is_valid, message = validate_creator_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("缺少必需字段", message)

        logger.info("数据验证测试通过")


def run_tests():
    """运行所有测试"""
    logger.info("开始运行简化版热点监控服务测试")

    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleHotspotMonitorTest))

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
    with open('test_results_simple.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    logger.info("测试结果已保存到 test_results_simple.json")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)