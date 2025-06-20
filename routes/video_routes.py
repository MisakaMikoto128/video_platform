from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.video import Video, VideoComment, VideoLike
from models.db import db
import os
from datetime import datetime
from moviepy.editor import VideoFileClip
from PIL import Image
import io
import hashlib
import uuid

video_bp = Blueprint('video', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'webm', 'mov'}

def generate_thumbnail(video_path, output_path):
    try:
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(1)  # 获取第1秒的帧
        image = Image.fromarray(frame)
        image.save(output_path)
        clip.close()
        return True
    except Exception as e:
        current_app.logger.error(f"生成缩略图失败: {str(e)}")
        return False

@video_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    videos = Video.query.order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('video/index.html', videos=videos)

@video_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        if 'video' not in request.files:
            return render_template('video/upload.html', error='没有选择文件')
        file = request.files['video']
        if file.filename == '':
            return render_template('video/upload.html', error='没有选择文件')
        if not allowed_file(file.filename):
            return render_template('video/upload.html', error='不支持的文件格式')

        try:
            # 计算文件哈希值
            # 注意：这里需要先读取文件内容来计算哈希，然后再将文件指针重置回开头以便保存
            file_content = file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            file.seek(0) # 将文件指针重置回文件开头

            # 检查数据库中是否已存在相同哈希值的视频
            existing_video = Video.query.filter_by(file_hash=file_hash).first()

            if existing_video:
                # 如果视频已存在，返回提示信息并跳过保存
                return render_template('video/upload.html', message='视频已存在，跳过上传')

            # 如果视频不存在，继续正常上传流程
            filename = secure_filename(file.filename)
            # 使用UUID生成唯一文件名，避免冲突
            file_uuid = uuid.uuid4().hex
            file_extension = os.path.splitext(filename)[1]
            video_filename = f"{file_uuid}{file_extension}"
            # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # video_filename = f"{timestamp}_{filename}" # 替换为UUID命名
            video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video_filename)
            file.save(video_path)
            
            # 缩略图也使用UUID命名
            thumbnail_filename = f"{file_uuid}_thumb.jpg"
            # thumbnail_filename = f"{timestamp}_thumb.jpg" # 替换为UUID命名
            thumbnail_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], thumbnail_filename)

            if not generate_thumbnail(video_path, thumbnail_path):
                os.remove(video_path) # 生成缩略图失败则删除已保存的视频文件
                return render_template('video/upload.html', error='生成缩略图失败')
            
            # 获取视频时长
            clip = VideoFileClip(video_path)
            duration = int(clip.duration) # moviepy duration是float，转换为int或保持float取决于模型定义
            clip.close()

            video = Video(
                title=request.form.get('title'),
                description=request.form.get('description'),
                file_path=video_filename,
                thumbnail_path=thumbnail_filename,
                duration=duration,
                user_id=current_user.id,
                tags=request.form.get('tags', ''),
                file_hash=file_hash # 保存文件哈希值
            )
            db.session.add(video)
            db.session.commit()
            return render_template('video/upload.html', message='上传成功')
        except Exception as e:
            current_app.logger.error(f"上传视频失败: {str(e)}")
            return render_template('video/upload.html', error='上传失败')
    return render_template('video/upload.html')

@video_bp.route('/watch/<int:video_id>')
def watch_video(video_id):
    video = Video.query.get_or_404(video_id)
    video.views += 1
    db.session.commit()
    
    # 获取相关视频（基于标签）
    related_videos = Video.query.filter(
        Video.id != video_id,
        Video.tags.ilike(f'%{video.tags}%')
    ).limit(5).all()
    
    # 检查当前用户是否已点赞
    is_liked = False
    if current_user.is_authenticated:
        is_liked = VideoLike.query.filter_by(
            video_id=video_id,
            user_id=current_user.id
        ).first() is not None
    
    return render_template('video/watch.html', 
                         video=video, 
                         related_videos=related_videos,
                         is_liked=is_liked)

@video_bp.route('/api/videos/<int:video_id>/like', methods=['POST'])
@login_required
def like_video(video_id):
    video = Video.query.get_or_404(video_id)
    like = VideoLike.query.filter_by(
        video_id=video_id,
        user_id=current_user.id
    ).first()
    
    if like:
        db.session.delete(like)
        video.likes -= 1
        is_liked = False
    else:
        like = VideoLike(video_id=video_id, user_id=current_user.id)
        db.session.add(like)
        video.likes += 1
        is_liked = True
    
    db.session.commit()
    return jsonify({
        'likes': video.likes,
        'is_liked': is_liked
    })

@video_bp.before_request
def require_login_for_api():
    if request.path.startswith('/api/') and request.method == 'POST' and not current_user.is_authenticated:
        # For API POST requests under /api/, return JSON error if not authenticated
        return jsonify({'error': '用户未登录，请先登录'}), 401

@video_bp.route('/comment/<int:video_id>', methods=['POST'])
def add_comment(video_id):
    # The login check is now handled by the before_request
    if not current_user.is_authenticated:
         return jsonify({'error': '用户未登录，请先登录'}), 401 # This check is redundant due to before_request but kept for clarity/safety
    video = Video.query.get_or_404(video_id)
    content = request.json.get('content')
    
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400
    
    comment = VideoComment(
        content=content,
        video_id=video_id,
        user_id=current_user.id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': '评论成功',
        'comment': {
            'content': comment.content,
            'username': current_user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

@video_bp.route('/search')
def search_videos():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if query:
        videos = Video.query.filter(
            (Video.title.ilike(f'%{query}%')) |
            (Video.tags.ilike(f'%{query}%'))
        ).order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)
    else:
        videos = Video.query.order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('video/search.html', videos=videos, query=query)

@video_bp.route('/video/<int:video_id>')
def get_video(video_id):
    video = Video.query.get_or_404(video_id)
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video.file_path)
    return send_file(video_path, mimetype='video/mp4')

@video_bp.route('/thumbnail/<int:video_id>')
def get_thumbnail(video_id):
    video = Video.query.get_or_404(video_id)
    thumbnail_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], video.thumbnail_path)
    return send_file(thumbnail_path, mimetype='image/jpeg')

@video_bp.route('/api/videos')
def api_videos():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    videos = Video.query.order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)
    from flask import url_for
    data = [{
        'id': v.id,
        'title': v.title,
        'file_path': url_for('video.get_video', video_id=v.id),
        'thumbnail': url_for('video.get_thumbnail', video_id=v.id),
        'description': v.description or '',
        'likes': v.likes or 0,
        'comment_count': VideoComment.query.filter_by(video_id=v.id).count()
    } for v in videos.items]
    return jsonify({'videos': data, 'has_next': videos.has_next})

@video_bp.route('/swipe')
def swipe():
    return render_template('video/swipe.html')

@video_bp.route('/api/videos/<int:video_id>/comments', methods=['GET'])
def get_comments(video_id):
    video = Video.query.get_or_404(video_id)
    comments = VideoComment.query.filter_by(video_id=video_id).order_by(VideoComment.created_at.asc()).all()
    comments_data = [{
        'content': comment.content,
        'username': comment.user.username, # 假设Comment模型关联了User模型
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
    } for comment in comments]
    return jsonify({'comments': comments_data})