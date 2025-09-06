# 📝 Bits&Blogs  

A **full-featured blog application** built with **Flask**, featuring authentication, post management, comments, likes, and image uploads via **Cloudinary**.  
Designed with **security, scalability, and modern web practices** in mind.  

---

## 🚀 Features  

### 🔐 Authentication & Authorization  
✔️ User registration & login with **JWT tokens**  
✔️ **Role-based access control** (Admin/User)  
✔️ Secure password hashing with **bcrypt**  
✔️ Strong password validation  

### 📝 Post Management  
✔️ CRUD blog posts  
✔️ Rich-text content support  
✔️ Upload images via **Cloudinary**  
✔️ Post ownership validation  
✔️ Admins manage all posts, users manage their own  

### 💬 Commenting System  
✔️ Add comments on posts  
✔️ Edit & delete comments  
✔️ Role-based permissions  

### ❤️ Social Features  
✔️ Like / Unlike posts  
✔️ Like count tracking  
✔️ Prevent duplicate likes from same user  

### 📸 Media Management  
✔️ Upload images securely to **Cloudinary**  
✔️ Automatic image optimization  
✔️ Support for image deletion  

### 🎨 User Interface  
✔️ Responsive HTML templates (**Jinja2**)  
✔️ User dashboard (posts & comments)  
✔️ Admin panel for content management  
✔️ Post detail views  

---

## 🛠️ Tech Stack  

| Category            | Technology            |
|---------------------|-----------------------|
| **Backend**         | Flask 3.0.3           |
| **Database**        | PostgreSQL + SQLAlchemy ORM |
| **Authentication**  | Flask-JWT-Extended    |
| **Password Hashing**| Flask-Bcrypt          |
| **Image Storage**   | Cloudinary            |
| **Migrations**      | Flask-Migrate (Alembic) |
| **Templates**       | Jinja2                |

---

## 📂 Project Structure  


</details>  

---

## 🗄️ Database Models  

<details>
<summary>👤 Users</summary>  

- `user_id` (UUID, PK)  
- `username` (unique)  
- `email` (unique)  
- `password` (hashed)  
- `first_name`, `last_name`  
- `role` (admin/user)  
- `created_at`, `updated_at`  

</details>  

<details>
<summary>📝 Posts</summary>  

- `post_id` (UUID, PK)  
- `author_id` (FK → Users)  
- `title`, `content`  
- `image`, `mimetype`, `image_public_id`  
- `created_at`, `updated_at`  

</details>  

<details>
<summary>💬 Comments</summary>  

- `comment_id` (UUID, PK)  
- `post_id`, `user_id` (FKs)  
- `content`    
- `created_at`, `updated_at`  

</details>  

<details>
<summary>❤️ Likes</summary>  

- `like_id` (UUID, PK)  
- `user_id`, `post_id` (FKs)  
- `created_at`  
- Unique constraint on (`user_id`, `post_id`)  

</details>  

---

## ⚙️ Installation  

### ✅ Prerequisites  
- Python 3.9+  
- PostgreSQL  
- Cloudinary account  

### 🔧 Setup  

```bash
# Clone the repository
git clone <repository-url>
cd Blog\ Project/blogs

# Create & activate a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```
# 📌 API Endpoints

## 🔐 Authentication
- **POST** `/auth/sign_up/` → Register new user  
- **POST** `/auth/login/` → Login user  
- **POST** `/auth/logout/` → Logout user  

---

## 📝 Posts
- **GET** `/post/all_posts/` → Fetch all posts  
- **POST** `/post/create_post/` → Create post  
- **GET** `/post/<post_id>/` → Get single post  
- **PUT** `/post/<post_id>/edit/` → Edit post  
- **DELETE** `/post/<post_id>/delete/` → Delete post  

---

## 💬 Comments
- **POST** `/comment/post/<post_id>/add/` → Add comment  
- **PUT** `/comment/<comment_id>/edit/` → Edit comment  
- **DELETE** `/comment/<comment_id>/delete/` → Delete comment  

---

## ❤️ Likes
- **POST** `/post/<post_id>/like/` → Like / Unlike post  




