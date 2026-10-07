# 热点监控服务

热点监控服务是一个用于监控抖音创作者内容、自动提取热点选题的FastAPI后端服务。

## 📋 功能特性

- **创作者管理**: 监控抖音创作者，管理创作者信息
- **视频管理**: 管理视频数据和统计信息
- **转写服务**: 视频音频转写为文本
- **选题管理**: 从视频内容提取热点选题
- **LLM集成**: 支持多LLM提供商（DeepSeek/通义千问/GPT-4）
- **向量去重**: 基于pgvector的相似度去重
- **定时调度**: APScheduler定时任务管理
- **RESTful API**: 完整的API接口

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 12+
- pgvector 扩展
- Redis (可选，用于缓存)

### 安装依赖

```bash
cd hotspot-monitor-service
pip install -r requirements.txt
```

### 数据库设置

1. 创建PostgreSQL数据库
2. 安装pgvector扩展
3. 运行数据库迁移

```bash
python -c "from models.database import init_db; init_db()"
```

### 运行服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问API

- 健康检查: `GET /api/health`
- 配置信息: `GET /api/config`
- 创作者管理: `GET /api/creators`, `POST /api/creators`
- 视频管理: `GET /api/videos`, `POST /api/videos`
- 转写服务: `POST /api/videos/{video_id}/transcribe`
- 选题管理: `GET /api/topics`, `POST /api/topics`
- 统计信息: `GET /api/stats/overview`

## 📁 项目结构

```
hotspot-monitor-service/
├── api/                 # API路由
│   ├── routes.py        # 统一API路由
│   └── dependencies.py  # API依赖项
├── config.py           # 服务配置
├── main.py            # FastAPI主入口
├── requirements.txt   # 依赖文件
├── services/          # 服务层
│   ├── creator_service.py    # 创作者管理
│   ├── video_service.py     # 视频管理
│   ├── transcribe_service.py # 转写服务
│   └── topic_service.py     # 选题管理
├── models/            # 数据模型
│   ├── schemas.py     # Pydantic数据模型
│   └── database.py    # 数据库模型和连接
├── crawlers/          # 爬虫模块
│   ├── douyin_crawler.py    # 抖音爬虫
│   └── backup_api.py       # 备用API
├── llm/               # LLM服务
│   ├── base_provider.py    # LLM基类
│   ├── deepseek_provider.py # DeepSeek提供者
│   ├── qwen_provider.py    # 通义千问提供者
│   ├── gpt4_provider.py    # GPT-4提供者
│   └── factory.py         # LLM工厂
├── dedup/             # 去重模块
│   └── vector_dedup.py     # 向量相似度去重
└── scheduler.py       # 任务调度器
```

## 🧪 测试

运行单元测试:

```bash
cd tests
python test_simple.py
```

## 📚 文档

- [实施进度记录](../Docs/00-实施进度记录.md)
- [阶段2完成总结](../Docs/06-阶段2完成总结.md)
- [抖音优先实施方案](../Docs/05-抖音优先实施方案与可行性评估.md)

## 🤝 贡献

欢迎提交Issue和Pull Request。

## 📄 许可证

本项目采用MIT许可证。