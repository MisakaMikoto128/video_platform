import os
import re
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.video import Video, VideoComment, VideoLike
from models.db import db
import os
from datetime import datetime


video_upload_bp = Blueprint('video_upload', __name__)

@video_upload_bp.route('/batch_import', methods=['GET', 'POST'])
@login_required
def batch_import():
    if request.method == 'POST':
        if 'video_folder' not in request.files:
            flash('没有选择文件夹', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('video_folder')
        results = []
        
        for file in files:
            if file.filename.endswith('.mp4'):
                try:
                    # 解析文件名
                    filename = file.filename
                    # 使用正则表达式匹配文件名格式
                    # 匹配格式：YYYY-MM-DD HH.MM.SS-视频-作者-标题.mp4
                    pattern = r'(\d{4}-\d{2}-\d{2}\s\d{2}\.\d{2}\.\d{2})-视频-(.+?)-(.+?)\.mp4'
                    match = re.match(pattern, filename)
                    
                    if match:
                        upload_time, author, title = match.groups()
                        # 转换上传时间格式
                        upload_time = datetime.strptime(upload_time, '%Y-%m-%d %H.%M.%S')
                        
                        # 保存文件
                        filename = secure_filename(filename)
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        
                        # 创建视频记录
                        video = Video(
                            title=title,
                            description=f"作者: {author}",
                            file_path=filename,
                            created_at=upload_time,
                            user_id=current_user.id
                        )
                        db.session.add(video)
                        results.append({
                            'filename': filename,
                            'success': True
                        })
                    else:
                        # 如果文件名不匹配标准格式，尝试从完整路径中提取
                        path_parts = filename.split('/')
                        if len(path_parts) > 1:
                            actual_filename = path_parts[-1]  # 获取实际文件名
                            pattern = r'(\d{4}-\d{2}-\d{2}\s\d{2}\.\d{2}\.\d{2})-视频-(.+?)-(.+?)\.mp4'
                            match = re.match(pattern, actual_filename)
                            
                            if match:
                                upload_time, author, title = match.groups()
                                upload_time = datetime.strptime(upload_time, '%Y-%m-%d %H.%M.%S')
                                
                                # 保存文件
                                filename = secure_filename(actual_filename)
                                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                                file.save(file_path)
                                
                                # 创建视频记录
                                video = Video(
                                    title=title,
                                    description=f"作者: {author}",
                                    file_path=filename,
                                    created_at=upload_time,
                                    user_id=current_user.id
                                )
                                db.session.add(video)
                                results.append({
                                    'filename': filename,
                                    'success': True
                                })
                            else:
                                results.append({
                                    'filename': filename,
                                    'success': False,
                                    'error': '文件名格式不正确'
                                })
                        else:
                            results.append({
                                'filename': filename,
                                'success': False,
                                'error': '文件名格式不正确'
                            })
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    })
        
        try:
            db.session.commit()
            flash('批量导入完成', 'success')
        except Exception as e:
            db.session.rollback()
            flash('导入过程中发生错误', 'error')
            results.append({
                'filename': '数据库操作',
                'success': False,
                'error': str(e)
            })
        
        return render_template('video/batch_import.html', results=results)
    
    return render_template('video/batch_import.html')

# ... 保留其他现有代码 ... 