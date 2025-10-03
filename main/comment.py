from flask import Blueprint, request, jsonify
from datetime import datetime
from .models import Comments, Users
from . import db, socketio
from flask_jwt_extended import jwt_required,get_jwt_identity


comment = Blueprint('comment', __name__)

def can_manage_comment(user_id, comment_id=None, comment=None):
    """
    Check if user can manage a comment based on their role
    - Admin: can manage any comment
    - User: can only manage their own comments
    """
    user = Users.query.filter_by(user_id=user_id).first()
    if not user:
        return False
    
    # Admin can manage any comment
    if user.is_admin():
        return True
    
    # User can only manage their own comments
    if user.is_user():
        if comment:
            return comment.user_id == user_id
        elif comment_id:
            comment_obj = Comments.query.filter_by(comment_id=comment_id).first()
            return comment_obj and comment_obj.user_id == user_id
    
    return False

@comment.route('/post/<uuid:pid>/add/', methods = ['GET', 'POST'], endpoint='add_comment')
@jwt_required()
def add_comment(pid):

        if request.method == 'POST':
            content = request.form.get('content')
            parent_comment_id = request.form.get('parent_comment_id')

            if not content:
                 return jsonify({"message":"Content is missing","status":"error"}), 401
            
            current_user_id = get_jwt_identity()

            # Validate parent comment if provided
            if parent_comment_id:
                parent = Comments.query.filter_by(comment_id=str(parent_comment_id), post_id=str(pid)).first()
                if not parent:
                    return jsonify({"message": "Parent comment not found","status":"error"}), 404

            add_comment = Comments(
                    post_id = str(pid),
                    user_id = current_user_id,
                    content = content,
                    parent_comment_id = str(parent_comment_id) if parent_comment_id else None,
                    created_at = datetime.now() 
            )

            db.session.add(add_comment)
            db.session.commit()
            
            # Emit socket event so other clients update without refresh
            try:
                socketio.emit('comment_broadcast', {
                    'post_id': str(pid),
                    'comment_id': add_comment.comment_id,
                    'author_id': current_user_id,
                    'content': content,
                    'created_at': add_comment.created_at.isoformat() if add_comment.created_at else None
                }, room=f'post_{str(pid)}')
            except Exception:
                pass
            return jsonify({"message": "Comment is added successfully", "status": "success"}), 200

                
        if request.method == 'GET':
            return jsonify({"message":"Add Comment","status":"pending"}), 202


@comment.route('/post/<uuid:pid>/edit/<uuid:cid>/', methods = ['GET', 'POST'] ,endpoint = 'edit_comment')
@jwt_required()
def edit_comment(pid,cid):

    if request.method == 'POST':
            content = request.form.get('content')

            if not content:
                 return jsonify({"message":"Content is missing","status":"error"}), 401
            
            current_user_id = get_jwt_identity()

            # Find the comment first
            comment = Comments.query.filter_by(comment_id=str(cid), post_id=str(pid)).first()
            
            if not comment:
                return jsonify({"message": "Comment not found", "status": "error"}), 404
            
            # Check if user can edit this comment
            if not can_manage_comment(current_user_id, comment=comment):
                return jsonify({"message": "Unauthorized to edit this comment", "status": "error"}), 403
        
            comment.content = content
            comment.updated_at = datetime.now()
            db.session.commit()
            return jsonify({"message": "Comment is edited successfully", "status": "success"}), 200
            
    if request.method == 'GET':
        return jsonify({"message":"Edit Comment","status":"pending"}), 202


@comment.route('/post/<uuid:post_id>/comments/', methods=['GET'])
@jwt_required()
def get_comments(post_id):
    current_user_id = get_jwt_identity()
    comments = Comments.query.filter_by(post_id=str(post_id)).order_by(Comments.created_at.asc()).all()

    # Build parent -> children mapping
    children_map = {}
    for c in comments:
        key = c.parent_comment_id or None
        children_map.setdefault(key, []).append(c)

    def serialize_comment(c):
        return {
            'cid': c.comment_id,
            'content': c.content,
            'username': c.author.username,
            'user_id': c.user_id,
            'is_owner': c.user_id == current_user_id,
            'can_edit': can_manage_comment(current_user_id, comment=c),
            'can_delete': can_manage_comment(current_user_id, comment=c),
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'replies': [serialize_comment(child) for child in children_map.get(c.comment_id, [])]
        }

    # Root-level comments have parent_comment_id == None
    tree = [serialize_comment(c) for c in children_map.get(None, [])]
    return jsonify(tree)



@comment.route('/post/<uuid:pid>/delete/<uuid:cid>/', methods = ['GET', 'POST'] ,endpoint = 'delete_comment')
@jwt_required()
def delete_comment(pid,cid):

    if request.method == 'POST':
        current_user_id = get_jwt_identity()

        # Find the comment first
        comment = Comments.query.filter_by(comment_id=str(cid), post_id=str(pid)).first()
    
        if not comment:
            return jsonify({"message": "Comment not found", "status": "error"}), 404
        
        # Check if user can delete this comment
        if not can_manage_comment(current_user_id, comment=comment):
            return jsonify({"message": "Unauthorized to delete this comment", "status": "error"}), 403
    
        # Recursively delete replies
        deleted_ids = []
        def delete_with_replies(cmt):
            deleted_ids.append(cmt.comment_id)
            for child in list(cmt.replies):
                delete_with_replies(child)
            db.session.delete(cmt)

        delete_with_replies(comment)
        db.session.commit()


        try:
            socketio.emit('comment_deleted', {
                'post_id': str(pid),
                'deleted_comment_ids': deleted_ids
            }, room=f'post_{str(pid)}')
        except Exception:
            pass


        return jsonify({"message": "Comment is deleted successfully", "status": "success"}), 200


        
    if request.method == 'GET':
        return jsonify({"message":"Delete Comment","status":"pending"}), 202
