#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频平台独立应用
"""

import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from models.db import db
from models.user import User

# 初始化扩展
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # 确保上传目录存在
    config[config_name].init_app(app)
    
    # 注册蓝图
    from routes.video_routes import video_bp
    from routes.auth import auth_bp
    from routes.video import video_upload_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(video_upload_bp)
    
    # 创建应用上下文
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5005, debug=True)  # 使用不同的端口 