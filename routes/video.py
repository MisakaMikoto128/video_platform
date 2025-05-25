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
import subprocess

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
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        thumbnail_folder = current_app.config.get('THUMBNAIL_FOLDER')

        if not upload_folder or not thumbnail_folder:
            results.append({
                'filename': '配置错误',
                'success': False,
                'error': 'UPLOAD_FOLDER 或 THUMBNAIL_FOLDER 未配置'
            })
            return render_template('video/batch_import.html', results=results)

        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(thumbnail_folder, exist_ok=True)

        for file in files:
            original_filename = file.filename
            if original_filename.endswith('.mp4'):
                try:
                    filename_base = original_filename
                    path_parts = original_filename.split('/')
                    if len(path_parts) > 1:
                        filename_base = path_parts[-1]

                    pattern = r'(\d{4}-\d{2}-\d{2}\s\d{2}\.\d{2}\.\d{2})-视频-(.+?)-(.+?)\.mp4'
                    match = re.match(pattern, filename_base)
                    
                    if match:
                        upload_time_str, author, title = match.groups()
                        upload_time = datetime.strptime(upload_time_str, '%Y-%m-%d %H.%M.%S')
                        
                        secured_filename = secure_filename(filename_base)
                        video_file_path = os.path.join(upload_folder, secured_filename)
                        file.save(video_file_path)

                        thumbnail_name = os.path.splitext(secured_filename)[0] + '.jpg'
                        thumbnail_file_path = os.path.join(thumbnail_folder, thumbnail_name)

                        try:
                            pass
                        except Exception as e:
                            results.append({
                                'filename': original_filename,
                                'success': False,
                                'error': f'处理视频文件失败: {str(e)}'
                            })
                            continue

                        video = Video(
                            title=title,
                            description=f"作者: {author}",
                            file_path=secured_filename,
                            thumbnail_path=thumbnail_name,
                            created_at=upload_time,
                            user_id=current_user.id
                        )
                        db.session.add(video)
                        results.append({
                            'filename': original_filename,
                            'success': True
                        })
                    else:
                        results.append({
                            'filename': original_filename,
                            'success': False,
                            'error': '文件名格式不正确'
                        })
                except Exception as e:
                    results.append({
                        'filename': original_filename,
                        'success': False,
                        'error': str(e)
                    })
        
        try:
            db.session.commit()
            flash('批量导入完成', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'导入过程中发生数据库错误: {str(e)}', 'error')
            print(f"Database commit failed: {e}")
        
        return render_template('video/batch_import.html', results=results)
    
    return render_template('video/batch_import.html')

# ... 保留其他现有代码 ... 