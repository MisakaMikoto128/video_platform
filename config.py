import os
from datetime import timedelta

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 数据库配置 - 使用独立的数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///video_platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 视频相关配置
    VIDEO_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'videos')
    VIDEO_MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    VIDEO_ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}
    
    # 缩略图配置
    THUMBNAIL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'thumbnails')
    THUMBNAIL_SIZE = (320, 180)  # 16:9 比例
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 确保上传目录存在
    @staticmethod
    def init_app(app):
        os.makedirs(Config.VIDEO_UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.THUMBNAIL_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 