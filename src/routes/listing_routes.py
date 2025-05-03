import os
import json
import traceback
import sys
from flask import Blueprint, request, jsonify, url_for, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from src.services.listings_service import (
    create_listing_service,
    get_listings_service,
    search_service
)
from src.models import User
from flasgger import swag_from

from src.utils.cloud_storage import UPLOAD_FOLDER

listings_bp = Blueprint("listings", __name__)


# Common schema definitions for reuse
LISTING_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "Unique identifier for the listing"},
        "restaurant_id": {"type": "integer", "description": "ID of the restaurant this listing belongs to"},
        "title": {"type": "string", "description": "Title of the listing"},
        "description": {"type": "string", "description": "Detailed description of the listing"},
        "image_url": {"type": "string", "description": "URL to the listing's image"},
        "original_price": {"type": "number", "format": "float", "description": "Original price of the item"},
        "pick_up_price": {"type": "number", "format": "float", "description": "Price for pick-up orders"},
        "delivery_price": {"type": "number", "format": "float", "description": "Price for delivery orders"},
        "count": {"type": "integer", "description": "Number of items available"},
        "consume_within": {"type": "integer", "description": "Number of days within which the item should be consumed"},
        "available_for_pickup": {"type": "boolean", "description": "Whether the item is available for pickup"},
        "available_for_delivery": {"type": "boolean", "description": "Whether the item is available for delivery"}
    }
}

# First, define the JSON documentation for create_listing endpoint
create_listing_doc = {
    "tags": ["Listings"],
    "security": [{"BearerAuth": []}],
    "summary": "Create a new food listing for a restaurant",
    "description": "Creates a new food listing with details including prices, availability, and an image. Only restaurant owners can create listings.",
    "parameters": [
        {
            "in": "path",
            "name": "restaurant_id",
            "type": "integer",
            "required": True,
            "description": "ID of the restaurant"
        },
        {
            "in": "formData",
            "name": "title",
            "type": "string",
            "required": True,
            "description": "Title of the listing",
            "example": "Fresh Pizza Margherita"
        },
        {
            "in": "formData",
            "name": "description",
            "type": "string",
            "required": False,
            "description": "Detailed description of the listing",
            "example": "Traditional Italian pizza with fresh basil"
        },
        {
            "in": "formData",
            "name": "original_price",
            "type": "number",
            "required": True,
            "description": "Original price of the item",
            "example": 15.99
        },
        {
            "in": "formData",
            "name": "pick_up_price",
            "type": "number",
            "required": False,
            "description": "Price for pick-up orders",
            "example": 12.99
        },
        {
            "in": "formData",
            "name": "delivery_price",
            "type": "number",
            "required": False,
            "description": "Price for delivery orders",
            "example": 17.99
        },
        {
            "in": "formData",
            "name": "count",
            "type": "integer",
            "required": False,
            "default": 1,
            "description": "Number of items available",
            "example": 5
        },
        {
            "in": "formData",
            "name": "consume_within",
            "type": "integer",
            "required": True,
            "description": "Days within which the item should be consumed",
            "example": 2
        },
        {
            "in": "formData",
            "name": "image",
            "type": "file",
            "required": True,
            "description": "Image file for the listing"
        }
    ],
    "responses": {
        "201": {
            "description": "Listing created successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Listing created successfully!"
                    },
                    "listing": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "example": 1
                            },
                            "title": {
                                "type": "string",
                                "example": "Fresh Pizza Margherita"
                            },
                            "original_price": {
                                "type": "number",
                                "example": 15.99
                            }
                        }
                    }
                }
            }
        },
        "400": {
            "description": "Validation error",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Title and original price are required"
                    }
                }
            }
        }
    }
}

# Define get_uploaded_file documentation
get_uploaded_file_doc = {
    "tags": ["Listings"],
    "security": [{"BearerAuth": []}],
    "summary": "Retrieve a listing's image file",
    "description": "Returns the image file associated with a listing.",
    "parameters": [
        {
            "in": "path",
            "name": "filename",
            "type": "string",
            "required": True,
            "description": "Name of the image file to retrieve"
        }
    ],
    "responses": {
        "200": {
            "description": "Image file"
        },
        "404": {
            "description": "File not found",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "File not found"
                    }
                }
            }
        }
    }
}

# Define get_listings documentation
get_listings_doc = {
    "tags": ["Listings"],
    "security": [{"BearerAuth": []}],
    "summary": "Retrieve paginated list of food listings",
    "description": "Returns a paginated list of all food listings. Can be filtered by restaurant ID.",
    "parameters": [
        {
            "in": "query",
            "name": "restaurant_id",
            "type": "integer",
            "required": False,
            "description": "Filter listings by restaurant ID"
        },
        {
            "in": "query",
            "name": "page",
            "type": "integer",
            "required": False,
            "default": 1,
            "description": "Page number"
        },
        {
            "in": "query",
            "name": "per_page",
            "type": "integer",
            "required": False,
            "default": 10,
            "description": "Number of items per page (max 100)"
        }
    ],
    "responses": {
        "200": {
            "description": "List of listings",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "example": 1
                                },
                                "title": {
                                    "type": "string",
                                    "example": "Fresh Pizza Margherita"
                                },
                                "original_price": {
                                    "type": "number",
                                    "example": 15.99
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

search_doc = {
    "tags": ["Listings"],
    "security": [{"BearerAuth": []}],
    "summary": "Search for food listings or restaurants",
    "description": "Performs a search across listings or restaurants based on query text.",
    "parameters": [
        {
            "in": "query",
            "name": "type",
            "type": "string",
            "enum": ["restaurant", "listing"],
            "required": True,
            "description": "Type of search to perform"
        },
        {
            "in": "query",
            "name": "query",
            "type": "string",
            "required": True,
            "description": "Search text for partial matching"
        },
        {
            "in": "query",
            "name": "restaurant_id",
            "type": "integer",
            "required": False,
            "description": "Required for listing search - restaurant to search within"
        }
    ],
    "responses": {
        "200": {
            "description": "Search results",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "type": {
                        "type": "string",
                        "example": "listing"
                    },
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "example": 1
                                },
                                "title": {
                                    "type": "string",
                                    "example": "Fresh Pizza Margherita"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Edit listing documentation
edit_listing_doc = {
    "tags": ["Listings"],
    "security": [{"BearerAuth": []}],
    "summary": "Edit an existing food listing",
    "description": "Updates an existing food listing's details. Only the owner of the restaurant can edit their listings.",
    "parameters": [
        {
            "in": "path",
            "name": "listing_id",
            "type": "integer",
            "required": True,
            "description": "ID of the listing to edit"
        },
        {
            "in": "formData",
            "name": "title",
            "type": "string",
            "required": False,
            "description": "New title of the listing",
            "example": "Updated Pizza Margherita"
        },
        {
            "in": "formData",
            "name": "description",
            "type": "string",
            "required": False,
            "description": "New description of the listing",
            "example": "Updated Italian pizza with fresh basil"
        }
    ],
    "responses": {
        "200": {
            "description": "Listing updated successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Listing updated successfully"
                    }
                }
            }
        }
    }
}

# Delete listing documentation
delete_listing_doc = {
    "tags": ["Listings"],
    "security": [{"BearerAuth": []}],
    "summary": "Delete an existing food listing",
    "description": "Removes a food listing from the system. Only the owner of the restaurant can delete their listings.",
    "parameters": [
        {
            "in": "path",
            "name": "listing_id",
            "type": "integer",
            "required": True,
            "description": "ID of the listing to delete"
        }
    ],
    "responses": {
        "200": {
            "description": "Listing deleted successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Listing deleted successfully"
                    }
                }
            }
        }
    }
}


@listings_bp.route("/restaurants/<int:restaurant_id>/listings", methods=["POST"])
@jwt_required()
@swag_from(create_listing_doc)
def create_listing(restaurant_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        owner_id = get_jwt_identity()
        owner = User.query.get(owner_id)
        if not owner:
            error_response = {"success": False, "message": "Owner not found"}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        if owner.role != "owner":
            error_response = {"success": False, "message": "Only owners can add listings"}
            print(json.dumps({"error_response": error_response, "status": 403}, indent=2))
            return jsonify(error_response), 403

        form_data = request.form.to_dict()
        file_obj = request.files.get("image")

        response, status = create_listing_service(
            restaurant_id, owner_id, form_data, file_obj, url_for
        )
        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@listings_bp.route('/uploads/<filename>', methods=['GET'])
@swag_from(get_uploaded_file_doc)
def get_uploaded_file(filename):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        filename = secure_filename(filename)
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        error_response = {"success": False, "message": "File not found"}
        print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
        return jsonify(error_response), 404
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {"success": False, "message": "An error occurred", "error": str(e)}
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@listings_bp.route("/listings", methods=["GET"])
@swag_from(get_listings_doc)
def get_listings():
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        restaurant_id = request.args.get('restaurant_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        response, status = get_listings_service(restaurant_id, page, per_page, url_for)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching listings",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@listings_bp.route("/search", methods=["GET"])
@swag_from(search_doc)
def search():
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        search_type = request.args.get("type")
        query_text = request.args.get("query", "").strip()
        restaurant_id = request.args.get("restaurant_id", type=int)
        response, status = search_service(search_type, query_text, restaurant_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while performing search",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@listings_bp.route("/listings/<int:listing_id>", methods=["PUT"])
@jwt_required()
@swag_from(edit_listing_doc)
def edit_listing(listing_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        owner_id = get_jwt_identity()
        owner = User.query.get(owner_id)
        if not owner:
            error_response = {"success": False, "message": "Owner not found"}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        form_data = request.form.to_dict()
        file_obj = request.files.get("image")

        from src.services.listings_service import edit_listing_service
        response, status = edit_listing_service(
            listing_id=listing_id,
            owner_id=owner_id,
            form_data=form_data,
            file_obj=file_obj,
            url_for_func=url_for
        )

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while updating the listing",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@listings_bp.route("/listings/<int:listing_id>", methods=["DELETE"])
@jwt_required()
@swag_from(delete_listing_doc)
def delete_listing(listing_id):
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        owner_id = get_jwt_identity()
        owner = User.query.get(owner_id)
        if not owner:
            error_response = {"success": False, "message": "Owner not found"}
            print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
            return jsonify(error_response), 404

        from src.services.listings_service import delete_listing_service
        response, status = delete_listing_service(
            listing_id=listing_id
        )

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while deleting the listing",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500