#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频平台独立应用
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

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
    app.register_blueprint(video_bp)
    app.register_blueprint(auth_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)  # 使用不同的端口 