"""数据库模型定义和连接"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import VECTOR
from datetime import datetime
import config

# 创建数据库引擎
engine = create_engine(
    config.DATABASE_URL,
    echo=config.DATABASE_ECHO,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()


class Creator(Base):
    """创作者表"""
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(255), nullable=False, index=True)
    note = Column(Text)
    platform = Column(String(50), default="douyin", index=True)
    creator_id = Column(String(255), index=True)
    is_active = Column(Boolean, default=True, index=True)
    sync_interval_hours = Column(Integer, default=24)
    last_sync_time = Column(DateTime)
    last_sync_status = Column(String(50))
    video_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    videos = relationship("Video", back_populates="creator", cascade="all, delete-orphan")


class Video(Base):
    """视频表"""
    __tablename__ = "creator_videos"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id", ondelete="CASCADE"), index=True)
    video_id = Column(String(255), nullable=False, index=True, unique=True)
    title = Column(String(1024), nullable=False)
    description = Column(Text)
    published_at = Column(DateTime, nullable=False, index=True)
    duration = Column(Integer)
    cover_url = Column(String(1024))
    video_url = Column(String(1024))
    transcript_status = Column(String(50), default="pending", index=True)
    transcript_text = Column(Text)
    transcript_language = Column(String(10), default="zh")
    transcribed_at = Column(DateTime)
    stats_views = Column(Integer, default=0)
    stats_likes = Column(Integer, default=0)
    stats_comments = Column(Integer, default=0)
    stats_shares = Column(Integer, default=0)
    stats_collected_at = Column(DateTime)
    source = Column(String(50), default="api")
    sync_batch_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = relationship("Creator", back_populates="videos")
    topics = relationship("Topic", back_populates="source_video", cascade="all, delete-orphan")


class Topic(Base):
    """选题表"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    source_video_id = Column(Integer, ForeignKey("creator_videos.id", ondelete="SET NULL"))
    title = Column(String(1024), nullable=False)
    summary = Column(Text)
    keywords = Column(JSON)
    category = Column(String(100))
    hot_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    status = Column(String(50), default="pending", index=True)
    embedding = Column(VECTOR(1024))  # pgvector 扩展（bge-m3 为1024维）
    llm_model = Column(String(50))
    extraction_method = Column(String(50))
    extracted_at = Column(DateTime)

    # 关系
    source_video = relationship("Video", back_populates="topics")


class ZhihuArticle(Base):
    """知乎文章表（热点采集）"""
    __tablename__ = "zhihu_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    url = Column(String(1024), unique=True, index=True)
    excerpt = Column(Text)                       # 摘要/回答片段
    author = Column(String(255))
    voteup_count = Column(Integer, default=0)    # 赞同数
    answer_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    keyword = Column(String(100), index=True)    # 采集关键词
    category = Column(String(50), index=True)    # LLM标签: AI/心理学/经济学等
    tag_status = Column(String(20), default="pending", index=True)  # pending/done/failed
    publish_window = Column(String(20))          # 发布时间窗口(如"3天内")
    is_selected = Column(Boolean, default=False) # 是否入选选题
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncTask(Base):
    """同步任务表"""
    __tablename__ = "sync_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    target_id = Column(Integer, index=True)
    status = Column(String(50), default="pending", index=True)
    result = Column(JSONB)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_sync_tasks_status', 'status'),
        Index('idx_sync_tasks_task_type', 'task_type'),
        Index('idx_sync_tasks_target_id', 'target_id'),
    )


# 创建数据库表
def create_tables():
    """创建所有数据库表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功")


# 删除数据库表（用于开发环境）
def drop_tables():
    """删除所有数据库表（谨慎使用）"""
    Base.metadata.drop_all(bind=engine)
    print("数据库表删除成功")


# 获取数据库会话
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 数据库连接测试
def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"数据库连接测试成功: {result.scalar()}")
            return True
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        return False


# 初始化数据库
def init_db():
    """初始化数据库"""
    if not test_connection():
        raise Exception("数据库连接失败")

    # 创建表
    create_tables()
    print("数据库初始化完成")


# 获取配置的向量相似度阈值
def get_vector_similarity_threshold():
    """获取向量相似度阈值"""
    return config.VECTOR_SIMILARITY_THRESHOLD


# 获取关键词相似度阈值
def get_keyword_similarity_threshold():
    """获取关键词相似度阈值"""
    return config.KEYWORD_SIMILARITY_THRESHOLD


# 数据库迁移工具（使用Alembic）
def get_alembic_config():
    """获取Alembic配置"""
    from alembic import context
    from sqlalchemy import engine_from_config, pool
    from logging.config import fileConfig

    config = context.config
    fileConfig(config.config_file_name)
    target_metadata = Base.metadata

    def run_migrations_offline():
        """离线迁移"""
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online():
        """在线迁移"""
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()