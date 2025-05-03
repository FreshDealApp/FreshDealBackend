import os
import json
import traceback
import sys

from flask import Blueprint, request, jsonify, send_from_directory, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from src.services.report_service import create_purchase_report_service, get_user_reports_service

report_bp = Blueprint("report", __name__)

# Define the absolute path for the upload folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@report_bp.route("/report", methods=["POST"])
@jwt_required()
def create_report():
    """
    Create a new purchase report with image upload.
    ---
    tags:
      - Reports
    summary: Create a new purchase report
    description: Create a new report for a purchase with an uploaded image and description.
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    produces:
      - application/json
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: JWT token in format - Bearer <token>
      - in: formData
        name: purchase_id
        type: integer
        required: true
        description: ID of the purchase being reported
      - in: formData
        name: description
        type: string
        required: true
        description: Description of the report
      - in: formData
        name: image
        type: file
        required: true
        description: Image file (allowed extensions - png, jpg, jpeg, webm)
    responses:
      201:
        description: Report created successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Report created successfully"
            report_id:
              type: integer
              example: 1
      400:
        description: Bad request - Invalid input or duplicate report
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Invalid or missing image file"
      401:
        description: Unauthorized - Invalid or missing token
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Missing Authorization Header"
      404:
        description: Purchase not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Purchase not found or does not belong to the user"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: "An error occurred"
            error:
              type: string
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "form_data": dict(request.form),
            "files": {k: f"{v.filename} ({v.content_type})" for k, v in request.files.items()} if request.files else {}
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()

        # Get form data and file
        purchase_id = request.form.get("purchase_id")
        description = request.form.get("description")
        file_obj = request.files.get("image")

        if not purchase_id or not description:
            error_response = {
                "message": "Missing required fields (purchase_id, description)."
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        if not file_obj:
            error_response = {
                "message": "Missing image file."
            }
            print(json.dumps({"error_response": error_response, "status": 400}, indent=2))
            return jsonify(error_response), 400

        response, status = create_purchase_report_service(
            user_id=user_id,
            purchase_id=int(purchase_id),
            file_obj=file_obj,
            description=description,
            url_for_func=url_for
        )

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status

    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@report_bp.route('/uploads/<filename>', methods=['GET'])
def get_uploaded_file(filename):
    """
    Retrieve an uploaded report image file.
    ---
    tags:
      - Reports
    summary: Get uploaded report image
    description: Serve an uploaded report image file by filename
    parameters:
      - in: path
        name: filename
        required: true
        type: string
        description: Name of the file to retrieve
    responses:
      200:
        description: Image file
        content:
          image/*:
            schema:
              type: string
              format: binary
      404:
        description: File not found
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "File not found"
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "filename": filename
        }
        print(json.dumps({"request": request_log}, indent=2))

        filename = secure_filename(filename)
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        error_response = {
            "success": False,
            "message": "File not found"
        }
        print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
        return jsonify(error_response), 404
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while fetching the file",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500


@report_bp.route("/report", methods=["GET"])
@jwt_required()
def get_user_reports():
    """
    Get all reports created by the authenticated user.
    ---
    tags:
      - Reports
    summary: Get user's reports
    description: Retrieve all reports created by the currently authenticated user
    security:
      - Bearer: []
    responses:
      200:
        description: List of user reports
        schema:
          type: object
          properties:
            reports:
              type: array
              items:
                type: object
                properties:
                  report_id:
                    type: integer
                    example: 1
                  purchase_id:
                    type: integer
                    example: 1
                  listing_id:
                    type: integer
                    example: 1
                  restaurant_id:
                    type: integer
                    example: 1
                  image_url:
                    type: string
                    example: "http://localhost:8000/uploads/image.jpg"
                  description:
                    type: string
                    example: "Report description"
                  reported_at:
                    type: string
                    format: date-time
                    example: "2025-01-26T19:37:44Z"
      401:
        description: Unauthorized - Invalid or missing token
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Missing Authorization Header"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            message:
              type: string
              example: "An error occurred"
            error:
              type: string
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args)
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        response, status = get_user_reports_service(user_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "message": "An error occurred",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500