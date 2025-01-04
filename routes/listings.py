import uuid

from flask import Blueprint, request, jsonify, url_for, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

from models import db, Restaurant, Listing, User

listings_bp = Blueprint("listings", __name__)

# Define the absolute path for the upload folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webm'}

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@listings_bp.route("/listings/add_listing/<int:restaurant_id>", methods=["POST"])
@jwt_required()
def add_listing(restaurant_id):
    try:
        # Get the current user
        owner_id = get_jwt_identity()
        owner = User.query.get(owner_id)

        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        if owner.role != "owner":
            return jsonify({"success": False, "message": "Only owners can add listings"}), 403

        # Get the restaurant
        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            return jsonify({"success": False, "message": f"Restaurant with ID {restaurant_id} not found"}), 404

        if int(restaurant.owner_id) != int(owner_id):
            print("restaurants registered owner id = ", restaurant.owner_id)
            print("requesting owners id ", owner_id)
            return jsonify({"success": False, "message": "You do not own this restaurant"}), 403

        # Get form data
        title = request.form.get("title")
        description = request.form.get("description", "")
        price = request.form.get("price")

        # Validate required fields
        if not title or not price:
            return jsonify({"success": False, "message": "Title and price are required"}), 400

        # Handle file upload
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            image_url = url_for('api_v1.listings.get_uploaded_file', filename=unique_filename, _external=True)
        else:
            return jsonify({"success": False, "message": "Invalid or missing image file"}), 400

        # Add new listing
        new_listing = Listing(
            restaurant_id=restaurant_id,
            title=title,
            description=description,
            image_url=image_url,
            price=float(price)
        )

        db.session.add(new_listing)
        db.session.commit()

        return jsonify({"success": True, "message": "Listing added successfully!", "image_url": image_url}), 201

    except Exception as e:
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

@listings_bp.route('/uploads/<filename>', methods=['GET'])
def get_uploaded_file(filename):
    """Serve the uploaded file securely."""
    try:
        # Secure the filename to prevent directory traversal
        filename = secure_filename(filename)
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"success": False, "message": "File not found"}), 404
