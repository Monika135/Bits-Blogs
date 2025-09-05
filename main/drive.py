import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import os
from dotenv import load_dotenv

load_dotenv()

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

def upload_image_to_drive(image_file, filename):
    """
    Upload image to Cloudinary
    Returns the public_id which can be used to construct URLs
    """
    try:
        # Upload image to Cloudinary
        result = cloudinary.uploader.upload(
            image_file,
            folder="blog_images",  # Optional: organize images in a folder
            public_id=filename.split('.')[0],  # Use filename without extension as public_id
            overwrite=True,  # Overwrite if file with same name exists
            resource_type="auto"  # Automatically detect file type
        )
        
        return result['public_id']
    
    except Exception as e:
        raise Exception(f"Failed to upload image to Cloudinary: {str(e)}")

def get_image_url(public_id):
    """
    Get optimized image URL from Cloudinary
    You can add transformations here for different sizes, formats, etc.
    """
    if not public_id:
        return None
    
    # Basic URL
    base_url = cloudinary.utils.cloudinary_url(public_id)[0]
    
    return base_url


def delete_image(public_id):
    """
    Delete image from Cloudinary
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result['result'] == 'ok'
    except Exception as e:
        print(f"Error deleting image: {str(e)}")
        return False
