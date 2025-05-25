from datetime import datetime
from sqlalchemy import Index
from app import db

class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    duration = db.Column(db.Integer)  # 视频时长（秒）
    file_hash = db.Column(db.String(64), unique=True, nullable=True)  # 添加文件哈希字段，使用SHA256，长度64
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.String(500))  # 存储标签，用逗号分隔
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 创建索引以提高搜索性能
    __table_args__ = (
        Index('idx_video_title', 'title'),
        Index('idx_video_tags', 'tags'),
        Index('idx_video_created', 'created_at'),
    )
    
    user = db.relationship('User', backref=db.backref('videos', lazy=True))

class VideoComment(db.Model):
    __tablename__ = 'video_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    video = db.relationship('Video', backref=db.backref('comments', lazy=True))
    user = db.relationship('User', backref=db.backref('video_comments', lazy=True))

class VideoLike(db.Model):
    __tablename__ = 'video_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('video_id', 'user_id', name='unique_video_like'),
    ) 