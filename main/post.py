from flask import Blueprint, request, jsonify, render_template
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from werkzeug.utils import secure_filename
from .models import Posts,Users, Comments, Likes
from . import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from .drive import upload_image_to_drive, get_image_url, delete_image

post = Blueprint('post', __name__)

def can_manage_post(user_id, post_id=None, post=None):
    """
    Check if user can manage a post based on their role
    - Admin: can manage any post
    - User: can only manage their own posts
    """
    user = Users.query.filter_by(user_id=user_id).first()
    if not user:
        return False
    
    # Admin can manage any post
    if user.is_admin():
        return True
    
    # User can only manage their own posts
    if user.is_user():
        if post:
            return post.author_id == user_id
        elif post_id:
            post_obj = Posts.query.filter_by(post_id=post_id).first()
            return post_obj and post_obj.author_id == user_id
    
    return False

@post.route('/create_post/', methods=['GET','POST'])
@jwt_required()
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')

        if not title:
            return jsonify({"message": "Title is missing", "status": "error"}), 400

        if not content:
            return jsonify({"message": "Content is missing", "status": "error"}), 400

        current_user_id = get_jwt_identity()

        image_url = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            file_id = upload_image_to_drive(image_file, filename)
            image_url = get_image_url(file_id)
           

        new_post = Posts(
            title=title,
            content=content,
            image=image_url,
            mimetype=image_file.mimetype if image_file else None,
            author_id=current_user_id
        )

        try:
            db.session.add(new_post)
            db.session.commit()
            return jsonify(
                {"message": "New post is added successfully",
                "status": "success",
                "post_id": new_post.post_id}
                ), 201
            
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Failed to add post", "status": "error"}), 500

    if request.method == 'GET':
            return jsonify({"message":"Add Post","status":"pending"}), 202



@post.route('/edit_post/<uuid:id>/', methods=['GET','POST'])
@jwt_required()
def edit_post(id):
    if request.method == 'POST':
        current_user_id = get_jwt_identity()
        editpost = Posts.query.filter_by(post_id=str(id)).first()

        if not editpost:
            return jsonify({"message": "Post not found", "status": "error"}), 404

        # Check if user can edit this post
        if not can_manage_post(current_user_id, post=editpost):
            return jsonify({"message": "Unauthorized to edit this post", "status": "error"}), 403

        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')

        if title:
            editpost.title = title
        if content:
            editpost.content = content

        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            file_id = upload_image_to_drive(image_file, filename)
            editpost.image = get_image_url(file_id)
            editpost.mimetype = image_file.mimetype

        editpost.updated_at = datetime.now()

        db.session.commit()
        return jsonify({"message": "Post is updated successfully", "status": "success"}), 200

    if request.method == 'GET':
            return jsonify({"message":"Edit Post","status":"pending"}), 202


@post.route('/delete_post/<uuid:pid>/', methods=['GET','POST'])
@jwt_required()
def delete_post(pid):
    if request.method == 'POST':
        current_user_id = get_jwt_identity()
        deletepost = Posts.query.filter_by(post_id=str(pid)).first()

        if not deletepost:
            return jsonify({"message": "Post not found", "status": "error"}), 404

        # Check if user can delete this post
        if not can_manage_post(current_user_id, post=deletepost):
            return jsonify({"message": "Unauthorized to delete this post", "status": "error"}), 403
        
        # Delete all comments associated with this post first
        Comments.query.filter_by(post_id=str(pid)).delete()
        
        # Delete all likes associated with this post
        Likes.query.filter_by(post_id=str(pid)).delete()
        
        if deletepost.image:
            try:
                public_id = deletepost.image.split('/')[-1].split('.')[0]
                delete_image(public_id)
            except Exception as e:
                print(f"Error deleting image from Cloudinary: {str(e)}")

        db.session.delete(deletepost)
        db.session.commit()
        return jsonify({"message": "Post is deleted successfully", "status": "success"}), 200
    
    if request.method == 'GET':
            return jsonify({"message":"Delete the post","status":"pending"}), 202


@post.route('/view_post/', methods=['GET'])
@jwt_required()
def all_post():
    current_user_id = get_jwt_identity()

    # --- Pagination & Search Params ---
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 3, type=int)
    search_query = request.args.get('search', '', type=str).strip()

    # --- Base Query ---
    query = Posts.query

    # --- Full-Text Search (PostgreSQL) ---
    if search_query:
        query = query.filter(
            (Posts.title.ilike(f'%{search_query}%')) |
            (Posts.content.ilike(f'%{search_query}%'))
        )
    # --- Paginate & Order ---
    pagination = query.order_by(Posts.created_at.desc()).paginate(page=page, per_page=per_page)
    posts_list = []

    for post in pagination.items:
        user = Users.query.get(post.author_id)
        posts_list.append({
            'post_id': post.post_id,
            'author_id': post.author_id,
            'author_username': user.username if user else "Unknown",
            'title': post.title,
            'content': post.content,
            'image_url': post.image,
            'mimetype': post.mimetype,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'is_owner': post.author_id == current_user_id,
            'can_edit': can_manage_post(current_user_id, post=post),
            'can_delete': can_manage_post(current_user_id, post=post),
            'like_count': post.get_like_count(),
            'is_liked': post.is_liked_by(current_user_id)
        })

    # --- Metadata for Pagination ---
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": pagination.pages,
        "total_items": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }

    return jsonify({"posts": posts_list, "meta": meta}), 200


@post.route('/like_post/<uuid:post_id>/', methods=['POST'])
@jwt_required()
def like_post(post_id):
    current_user_id = get_jwt_identity()
    
    # Check if post exists
    post = Posts.query.filter_by(post_id=str(post_id)).first()
    if not post:
        return jsonify({"message": "Post not found", "status": "error"}), 404
    
    # Check if user already liked this post
    existing_like = Likes.query.filter_by(
        user_id=current_user_id, 
        post_id=str(post_id)
    ).first()
    
    if existing_like:
        # Unlike the post
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({
            "message": "Post unliked successfully", 
            "status": "success",
            "liked": False,
            "like_count": post.get_like_count()
        }), 200
    else:
        # Like the post
        new_like = Likes(
            user_id=current_user_id,
            post_id=str(post_id)
        )
        db.session.add(new_like)
        db.session.commit()
        return jsonify({
            "message": "Post liked successfully", 
            "status": "success",
            "liked": True,
            "like_count": post.get_like_count()
        }), 201


# Add these routes to render templates
@post.route('/create/', methods=['GET'])
def create_post_page():
    return render_template('create_post.html')

@post.route('/edit/<uuid:id>/', methods=['GET'])
def edit_post_page(id):
    return render_template('edit_post.html')

@post.route('/view_posts/', methods=['GET'])
def all_posts_page():
    return render_template('all_posts.html')

@post.route('/detail/<uuid:id>/', methods=['GET'])
def post_detail_page(id):
    return render_template('post_detail.html')


# Add this new route at the top of your post.py
@post.route('/dashboard/', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')
