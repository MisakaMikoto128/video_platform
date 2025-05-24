import os
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models.video import Video, VideoComment, VideoLike
from datetime import datetime
import moviepy.editor as mp
from PIL import Image
import io

video_bp = Blueprint('video', __name__, url_prefix='/video')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['VIDEO_ALLOWED_EXTENSIONS']

def generate_thumbnail(video_path, output_path):
    try:
        video = mp.VideoFileClip(video_path)
        # 获取视频的第一帧
        frame = video.get_frame(0)
        # 转换为PIL图像
        image = Image.fromarray(frame)
        # 调整大小
        image.thumbnail(current_app.config['THUMBNAIL_SIZE'])
        # 保存缩略图
        image.save(output_path)
        video.close()
        return True
    except Exception as e:
        print(f"生成缩略图失败: {str(e)}")
        return False

@video_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    videos = Video.query.order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('video/index.html', videos=videos)

@video_bp.route('/upload', methods=['POST'])
@login_required
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # 保存视频文件
        video_path = os.path.join(current_app.config['VIDEO_UPLOAD_FOLDER'], filename)
        file.save(video_path)
        
        # 生成缩略图
        thumbnail_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"
        thumbnail_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
        generate_thumbnail(video_path, thumbnail_path)
        
        # 获取视频时长
        try:
            video = mp.VideoFileClip(video_path)
            duration = int(video.duration)
            video.close()
        except:
            duration = 0
        
        # 创建视频记录
        video = Video(
            title=request.form.get('title', filename),
            description=request.form.get('description', ''),
            file_path=filename,
            thumbnail_path=thumbnail_filename,
            duration=duration,
            tags=request.form.get('tags', ''),
            user_id=current_user.id
        )
        
        db.session.add(video)
        db.session.commit()
        
        return jsonify({'message': '上传成功', 'video_id': video.id}), 200
    
    return jsonify({'error': '不支持的文件类型'}), 400

@video_bp.route('/<int:video_id>')
def watch_video(video_id):
    video = Video.query.get_or_404(video_id)
    video.views += 1
    db.session.commit()
    
    # 获取相关视频
    related_videos = Video.query.filter(
        Video.id != video_id,
        Video.tags.ilike(f'%{video.tags.split(",")[0]}%')
    ).order_by(Video.views.desc()).limit(5).all()
    
    return render_template('video/watch.html', video=video, related_videos=related_videos)

@video_bp.route('/<int:video_id>/like', methods=['POST'])
@login_required
def like_video(video_id):
    video = Video.query.get_or_404(video_id)
    
    existing_like = VideoLike.query.filter_by(video_id=video_id, user_id=current_user.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        video.likes -= 1
        action = 'unliked'
    else:
        new_like = VideoLike(video_id=video_id, user_id=current_user.id)
        db.session.add(new_like)
        video.likes += 1
        action = 'liked'
    
    db.session.commit()
    return jsonify({'action': action, 'likes': video.likes})

@video_bp.route('/<int:video_id>/comment', methods=['POST'])
@login_required
def add_comment(video_id):
    video = Video.query.get_or_404(video_id)
    content = request.json.get('content')
    
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400
    
    comment = VideoComment(
        video_id=video_id,
        user_id=current_user.id,
        content=content
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'username': current_user.username
    })

@video_bp.route('/search')
def search_videos():
    query = request.args.get('q', '')
    tag = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    videos_query = Video.query
    
    if query:
        videos_query = videos_query.filter(Video.title.ilike(f'%{query}%'))
    if tag:
        videos_query = videos_query.filter(Video.tags.ilike(f'%{tag}%'))
    
    videos = videos_query.order_by(Video.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('video/search.html', videos=videos, query=query, tag=tag) 