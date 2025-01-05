# restaurant_manager.py

import uuid
from flask import Blueprint, request, jsonify, url_for, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

from models import db, Restaurant, User

restaurantManager_bp = Blueprint("restaurantManager", __name__)

# Define the absolute path for the upload folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webm'}

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@restaurantManager_bp.route("/add_restaurant", methods=["POST"])
@jwt_required()
def add_restaurant():
    try:
        # Since we're handling file uploads, use form data instead of JSON
        if 'application/json' in request.headers.get('Content-Type', ''):
            return jsonify({"success": False, "message": "Content-Type must be multipart/form-data"}), 400

        owner_id = get_jwt_identity()
        owner = User.query.get(owner_id)
        if not owner:
            print("Validation error: Owner not found.")
            return jsonify({"success": False, "message": "Owner not found"}), 404
        elif owner.role != "owner":
            print("Validation error: A restaurant was attempted to be added by someone who is not an owner.")
            return jsonify({"success": False, "message": "Only owners can add a restaurant"}), 403

        # Get form data
        restaurant_name = request.form.get('restaurantName')
        restaurant_description = request.form.get('restaurantDescription')
        longitude = request.form.get('longitude')
        latitude = request.form.get('latitude')
        category = request.form.get('category')
        working_days = request.form.getlist('workingDays')  # Expecting multiple workingDays fields
        working_hours_start = request.form.get('workingHoursStart')
        working_hours_end = request.form.get('workingHoursEnd')
        listings = request.form.get('listings')

        # Validate required fields
        if not restaurant_name:
            print("Validation error: Restaurant name is missing.")
            return jsonify({"success": False, "message": "Restaurant name is required"}), 400

        if not category:
            print("Validation error: Category name is missing.")
            return jsonify({"success": False, "message": "Category is required"}), 400

        if listings is None:
            print("Validation error: Listings is missing.")
            return jsonify({"success": False, "message": "Listings is required"}), 400

        if longitude is None or latitude is None:
            print("Validation error: Longitude or Latitude is missing.")
            return jsonify({"success": False, "message": "Longitude and latitude are required"}), 400

        try:
            longitude = float(longitude)
            latitude = float(latitude)
            listings = int(listings)
        except ValueError:
            print("Validation error: Longitude, Latitude, or Listings have invalid format.")
            return jsonify({"success": False, "message": "Longitude, latitude must be float and listings must be integer"}), 400

        # Handle file upload (optional)
        image_url = None
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            image_url = url_for('api_v1.restaurantManager.get_uploaded_file', filename=unique_filename, _external=True)
        elif file:
            # File was provided but has an invalid extension
            return jsonify({"success": False, "message": "Invalid image file type"}), 400

        # Prepare working days string
        working_days_str = ",".join(working_days) if working_days else ""

        # Create new restaurant instance
        new_restaurant = Restaurant(
            owner_id=owner_id,
            restaurantName=restaurant_name,
            restaurantDescription=restaurant_description,
            longitude=longitude,
            latitude=latitude,
            category=category,
            workingDays=working_days_str,
            workingHoursStart=working_hours_start,
            workingHoursEnd=working_hours_end,
            listings=listings,
            ratingCount=0,
            image_url=image_url
        )

        db.session.add(new_restaurant)
        db.session.commit()

        return jsonify({"success": True, "message": "New restaurant is successfully added!", "image_url": image_url}), 201

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

@restaurantManager_bp.route('/uploads/<filename>', methods=['GET'])
def get_uploaded_file(filename):
    """Serve the uploaded file securely."""
    try:
        # Secure the filename to prevent directory traversal
        filename = secure_filename(filename)
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"success": False, "message": "File not found"}), 404

@restaurantManager_bp.route("/get_restaurant/<int:restaurant_id>", methods=["GET"])
def get_restaurant(restaurant_id):
    try:
        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            print(f"Validation error: Restaurant with ID {restaurant_id} not found.")
            return jsonify({"success": False, "message": f"Restaurant with ID {restaurant_id} not found."}), 404

        restaurant_data = {
            "id": restaurant.id,
            "owner_id": restaurant.owner_id,
            "restaurantName": restaurant.restaurantName,
            "restaurantDescription": restaurant.restaurantDescription,
            "longitude": float(restaurant.longitude),
            "latitude": float(restaurant.latitude),
            "category": restaurant.category,
            "workingDays": restaurant.workingDays.split(",") if restaurant.workingDays else [],
            "workingHoursStart": restaurant.workingHoursStart,
            "workingHoursEnd": restaurant.workingHoursEnd,
            "listings": restaurant.listings,
            "rating": float(restaurant.rating) if restaurant.rating else None,
            "ratingCount": restaurant.ratingCount,
            "image_url": restaurant.image_url  # Include image_url
        }

        return jsonify(restaurant_data), 200

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

@restaurantManager_bp.route("/get_restaurants", methods=["GET"])
@jwt_required()
def get_restaurants():
    try:
        owner_id = get_jwt_identity()
        owner = User.query.get(owner_id)
        if not owner:
            print("Validation error: Owner not found.")
            return jsonify({"success": False, "message": "Owner not found"}), 404
        elif owner.role != "owner":
            print("Validation error: Only users with owner role can own a restaurant.")
            return jsonify({"success": False, "message": "Only users with owner role can own a restaurant"}), 403

        restaurants = Restaurant.query.filter_by(owner_id=owner_id).all()

        if not restaurants:
            return jsonify({"message": "No restaurant found for the owner"}), 404

        serialized_restaurants = []
        for restaurant in restaurants:
            serialized_restaurants.append({
                "id": restaurant.id,
                "owner_id": restaurant.owner_id,
                "restaurantName": restaurant.restaurantName,
                "restaurantDescription": restaurant.restaurantDescription,
                "longitude": float(restaurant.longitude),
                "latitude": float(restaurant.latitude),
                "category": restaurant.category,
                "workingDays": restaurant.workingDays.split(",") if restaurant.workingDays else [],
                "workingHoursStart": restaurant.workingHoursStart,
                "workingHoursEnd": restaurant.workingHoursEnd,
                "listings": restaurant.listings,
                "rating": float(restaurant.rating) if restaurant.rating else None,
                "ratingCount": restaurant.ratingCount,
                "image_url": restaurant.image_url  # Include image_url
            })
        return jsonify(serialized_restaurants), 200

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

@restaurantManager_bp.route("/delete_restaurant/<int:restaurant_id>", methods=["DELETE"])
@jwt_required()
def delete_restaurant(restaurant_id):
    try:
        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            print(f"Validation error: Restaurant with ID {restaurant_id} not found.")
            return jsonify({"success": False, "message": f"Restaurant with ID {restaurant_id} not found."}), 404

        owner_id = get_jwt_identity()
        if str(owner_id) != str(restaurant.owner_id):
            print(str(owner_id)+" "+str(restaurant.owner_id))
            print("A restaurant was attempted to be deleted by someone who is not the owner")
            return jsonify({"success": False, "message": "You are not the owner of this restaurant."}), 403

        # Optionally, delete the associated image file
        if restaurant.image_url:
            try:
                filename = restaurant.image_url.split('/')[-1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Failed to delete image file: {e}")

        db.session.delete(restaurant)
        db.session.commit()

        return jsonify({"success": True, "message": f"Restaurant with ID {restaurant_id} successfully deleted."}), 200

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

@restaurantManager_bp.route("/get_restaurants_proximity", methods=["POST"])
@jwt_required()  # Optional: Remove if not requiring authentication
def get_restaurants_proximity():
    try:
        data = request.get_json()
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        radius = data.get('radius', 10)  # Default radius is 10 km

        # Validate input
        if user_lat is None or user_lon is None:
            print("Validation error: Latitude or Longitude is missing.")
            return jsonify({"success": False, "message": "Latitude and longitude are required"}), 400

        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
            radius = float(radius)
        except ValueError:
            print("Validation error: Invalid latitude, longitude, or radius format.")
            return jsonify({"success": False, "message": "Invalid latitude, longitude, or radius format"}), 400

        # Haversine formula to calculate distance between two points on the Earth
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            # convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

            # haversine formula
            d_lon = lon2 - lon1
            d_lat = lat2 - lat1
            a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers
            return c * r

        # Fetch all restaurants (you can optimize this by fetching only those within a bounding box)
        restaurants = Restaurant.query.all()

        nearby_restaurants = []
        for restaurant in restaurants:
            distance = haversine(user_lat, user_lon, float(restaurant.latitude), float(restaurant.longitude))
            if distance <= radius:
                nearby_restaurants.append({
                    "id": restaurant.id,
                    "owner_id": restaurant.owner_id,
                    "restaurantName": restaurant.restaurantName,
                    "restaurantDescription": restaurant.restaurantDescription,
                    "longitude": float(restaurant.longitude),
                    "latitude": float(restaurant.latitude),
                    "category": restaurant.category,
                    "workingDays": restaurant.workingDays.split(",") if restaurant.workingDays else [],
                    "workingHoursStart": restaurant.workingHoursStart,
                    "workingHoursEnd": restaurant.workingHoursEnd,
                    "listings": restaurant.listings,
                    "rating": float(restaurant.rating) if restaurant.rating else None,
                    "ratingCount": restaurant.ratingCount,
                    "image_url": restaurant.image_url,  # Include image_url
                    "distance_km": round(distance, 2)
                })

        if not nearby_restaurants:
            return jsonify({"message": "No restaurants found within the specified radius"}), 404

        # Optionally, sort the restaurants by distance
        nearby_restaurants.sort(key=lambda x: x['distance_km'])

        return jsonify({"restaurants": nearby_restaurants}), 200

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500
