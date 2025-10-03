from flask_socketio import emit, join_room
from flask_jwt_extended import decode_token
from .models import Comments, Posts, db
from . import socketio

# Join post room
@socketio.on('join_post')
def handle_join_post(data):
    post_id = data['post_id']
    join_room(f'post_{post_id}')
    emit('status', {'msg': f'Joined post {post_id}'})

# Handle new comment
@socketio.on('new_comment')
def handle_new_comment(data):
    try:
        token = data.get('token')
        post_id = str(data.get('post_id'))
        content = (data.get('content') or '').strip()
        if not token or not post_id or not content:
            return

        user_id = decode_token(token)['sub']
        comment = Comments(post_id=post_id, user_id=user_id, content=content)
        db.session.add(comment)
        db.session.commit()

        emit('comment_broadcast', {
            'post_id': post_id,
            'comment_id': comment.comment_id,
            'author_id': user_id,
            'content': content,
            'created_at': comment.created_at.isoformat() if comment.created_at else None
        }, room=f'post_{post_id}')
    except Exception:
        db.session.rollback()
        # Avoid crashing the socket event on errors
        return

# Handle post likes
@socketio.on('like_post')
def handle_like_post(data):
    token = data['token']
    post_id = data['post_id']
    user_id = decode_token(token)['sub']

    post = Posts.query.get(post_id)
    if not post:
        return

    # Notify post owner
    owner_id = post.author_id
    emit('notification', {
        'msg': f'User {user_id} liked your post "{post.title}"'
    }, room=f'user_{owner_id}')

    # Broadcast updated like count to all viewers of this post
    try:
        like_count = post.get_like_count() if hasattr(post, 'get_like_count') else None
        if like_count is not None:
            emit('like_update', {
                'post_id': post_id,
                'like_count': like_count
            }, room=f'post_{post_id}')
    except Exception:
        # Silently ignore to avoid breaking notification flow
        pass
