from flask import Blueprint, request, jsonify
from datetime import datetime
from .models import Comments, Users
from . import db
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

            if not content:
                 return jsonify({"message":"Content is missing","status":"error"}), 401
            
            current_user_id = get_jwt_identity()

            add_comment = Comments(
                    post_id = pid,
                    user_id = current_user_id,
                    content = content,
                    created_at = datetime.now() 
            )

            db.session.add(add_comment)
            db.session.commit()
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
    comments = Comments.query.filter_by(post_id=str(post_id)).all()
    
    return jsonify([{
        'cid': (comment.comment_id), 
        'content': comment.content,
        'username': comment.author.username,
        'user_id': comment.user_id,
        'is_owner': comment.user_id == current_user_id,
        'can_edit': can_manage_comment(current_user_id, comment=comment),
        'can_delete': can_manage_comment(current_user_id, comment=comment),
        'created_at': comment.created_at.isoformat() if comment.created_at else None
    } for comment in comments])



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
    
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"message": "Comment is deleted successfully", "status": "success"}), 200
        
    if request.method == 'GET':
        return jsonify({"message":"Delete Comment","status":"pending"}), 202

