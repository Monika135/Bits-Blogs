from . import db
from sqlalchemy.sql import func
import uuid


class Users(db.Model):
    __tablename__ = 'Users'

    user_id = db.Column(db.String(36) , primary_key= True, default=lambda: str(uuid.uuid4()), nullable=False)
    username = db.Column(db.String(30), nullable=False, unique = True)
    email = db.Column(db.String(50), unique=True,nullable=False)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(),nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(),onupdate=func.now(),nullable = True)
    posts = db.relationship('Posts', back_populates='author')
    comments = db.relationship('Comments', back_populates='author')
    likes = db.relationship('Likes', back_populates='user')

    def is_admin(self):
        return self.role == 'admin'

    def is_user(self):
        return self.role == 'user'


class Posts(db.Model):
    __tablename__ = 'Posts'

    post_id = db.Column(db.String(36), primary_key= True, default=lambda: str(uuid.uuid4()), nullable=False)
    author_id = db.Column(db.String(36), db.ForeignKey(Users.user_id), nullable=False)
    title = db.Column(db.String(80),nullable=False)
    content = db.Column(db.String(1500), nullable=False,unique = True)
    image = db.Column(db.String(255),nullable = True)  
    mimetype = db.Column(db.String(60), nullable = True)
    image_public_id = db.Column(db.String(255), nullable=True)  # Add this field
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now(),onupdate=func.now(),nullable = True)
    author = db.relationship('Users', back_populates='posts')
    comments = db.relationship('Comments', back_populates='post')
    likes = db.relationship('Likes', back_populates='post')

    def get_like_count(self):
        """Get total number of likes for this post"""
        return len(self.likes)
    
    def is_liked_by(self, user_id):
        """Check if a specific user has liked this post"""
        return any(like.user_id == user_id for like in self.likes)



class Comments(db.Model):
    __tablename__ = 'Comments'

    comment_id = db.Column(db.String(36), primary_key= True, default=lambda: str(uuid.uuid4()), nullable=False)
    post_id = db.Column(db.String(36), db.ForeignKey(Posts.post_id), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey(Users.user_id), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    parent_comment_id = db.Column(db.String(36), db.ForeignKey('Comments.comment_id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=func.now())
    post = db.relationship('Posts', back_populates='comments')
    author = db.relationship('Users', back_populates='comments')
    parent_comment = db.relationship('Comments', remote_side=[comment_id], backref='replies')


class Likes(db.Model):
    __tablename__ = 'Likes'

    like_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey(Users.user_id), nullable=False)
    post_id = db.Column(db.String(36), db.ForeignKey(Posts.post_id), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user = db.relationship('Users', back_populates='likes')
    post = db.relationship('Posts', back_populates='likes')
    
    # Prevent duplicate likes from same user on same post
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )
