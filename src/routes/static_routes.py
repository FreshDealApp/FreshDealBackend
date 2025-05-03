from flask import Blueprint, send_from_directory, request, jsonify
import os
import json
import traceback
import sys

static_bp = Blueprint("static", __name__)

# Path to the static directory
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))


@static_bp.route("/static/<path:filename>", methods=["GET"])
def serve_static(filename):
    """
    Serve static files like badge images
    ---
    tags:
      - Static
    parameters:
      - name: filename
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: The requested file
      404:
        description: File not found
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "filename": filename
        }
        print(json.dumps({"request": request_log}, indent=2))

        return send_from_directory(STATIC_DIR, filename)
    except FileNotFoundError:
        error_response = {
            "success": False,
            "message": f"File '{filename}' not found"
        }
        print(json.dumps({"error_response": error_response, "status": 404}, indent=2))
        return jsonify(error_response), 404
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while serving static file",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response, "status": 500}, indent=2))
        return jsonify(error_response), 500