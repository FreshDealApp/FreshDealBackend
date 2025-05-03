import os
import uuid
import io
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, storage
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory path for local storage fallback
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'routes', 'uploads')

# Ensure the upload directory exists for fallback local storage
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webm'}

# Initialize Firebase (this should be done only once)
try:
    firebase_admin.get_app()
except ValueError:
    # Get Firebase credentials from environment variables
    firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')
    firebase_private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
    firebase_client_email = os.getenv('FIREBASE_CLIENT_EMAIL')

    if firebase_project_id and firebase_private_key and firebase_client_email:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": firebase_project_id,
            "private_key": firebase_private_key,
            "client_email": firebase_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        })
        firebase_admin.initialize_app(cred, {
            'storageBucket': f"{firebase_project_id}.appspot.com"
        })
    else:
        print("Warning: Firebase credentials not found in environment variables!")


def allowed_file(filename):
    """Return True if the filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(file_obj, max_size=(800, 800), quality=85, format='JPEG'):
    """Compress an image to reduce file size."""
    img = Image.open(file_obj)

    # Convert to RGB if needed (to handle RGBA images)
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    # Resize if larger than max_size while maintaining aspect ratio
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)

    # Save to BytesIO buffer
    buffer = io.BytesIO()
    img.save(buffer, format=format, quality=quality, optimize=True)
    buffer.seek(0)

    return buffer, f"{os.path.splitext(file_obj.filename)[0]}.jpg"


def upload_file(file_obj, folder="uploads", url_for_func=None, url_endpoint=None):
    """
    Upload a file to Firebase Storage with local fallback.

    Args:
        file_obj: The file object to upload
        folder: The folder to store in Firebase Storage
        url_for_func: Flask's url_for function for local fallback
        url_endpoint: The endpoint to use with url_for_func

    Returns:
        Tuple of (success, image_url or error message)
    """
    if not file_obj or not file_obj.filename:
        return False, "Invalid or missing file"

    if not allowed_file(file_obj.filename):
        return False, "Invalid file type"

    try:
        original_filename = secure_filename(file_obj.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"

        # Compress the image if it's a supported format
        if any(ext in original_filename.lower() for ext in ['.jpg', '.jpeg', '.png']):
            file_obj.seek(0)  # Reset file pointer to beginning
            compressed_file, _ = compress_image(file_obj)
            file_to_upload = compressed_file
        else:
            file_obj.seek(0)  # Reset file pointer to beginning
            file_to_upload = file_obj

        # Try Firebase Storage first
        try:
            if firebase_admin._apps:
                bucket = storage.bucket()

                # Create a blob and upload the file's contents
                blob = bucket.blob(f"{folder}/{unique_filename}")
                blob.upload_from_file(file_to_upload)

                # Make the blob publicly accessible
                blob.make_public()

                # Get the public URL
                image_url = blob.public_url
                print(f"Uploaded to Firebase Storage: {image_url}")
                return True, image_url
            else:
                raise ValueError("Firebase not initialized")

        except Exception as firebase_error:
            print(f"Firebase upload error, falling back to local storage: {str(firebase_error)}")

            # Fallback to local storage
            if url_for_func and url_endpoint:
                file_to_upload.seek(0)  # Reset file pointer to beginning
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

                # If it's a BytesIO object from compression
                if isinstance(file_to_upload, io.BytesIO):
                    with open(filepath, 'wb') as f:
                        f.write(file_to_upload.getvalue())
                else:
                    file_to_upload.save(filepath)

                image_url = url_for_func(url_endpoint, filename=unique_filename, _external=True)
                print(f"Uploaded to local storage: {image_url}")
                return True, image_url
            else:
                return False, "Cannot save to local storage - url_for function or endpoint not provided"

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False, f"Error uploading file: {str(e)}"


def delete_file(image_url, folder="uploads"):
    """
    Delete a file from Firebase Storage with local fallback.

    Args:
        image_url: The URL of the image to delete
        folder: The folder in Firebase Storage

    Returns:
        Tuple of (success, message)
    """
    if not image_url:
        return True, "No image to delete"

    try:
        # Check if it's a Firebase Storage URL
        if "firebasestorage.googleapis.com" in image_url:
            try:
                if firebase_admin._apps:
                    bucket = storage.bucket()
                    filename = os.path.basename(image_url.split('?')[0])
                    blob = bucket.blob(f"{folder}/{filename}")
                    blob.delete()
                    return True, f"Successfully deleted image from Firebase: {filename}"
                else:
                    return False, "Firebase not initialized"
            except Exception as e:
                print(f"Error deleting from Firebase: {str(e)}")
                return False, f"Error deleting from Firebase: {str(e)}"
        else:
            # Assume it's a local file
            try:
                filename = image_url.split('/')[-1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return True, f"Successfully deleted local image: {filename}"
                return True, f"Local image file not found: {filename}"
            except Exception as e:
                return False, f"Failed to delete local image file: {str(e)}"

    except Exception as e:
        return False, f"Error processing delete request: {str(e)}"