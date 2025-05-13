from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.address_service import (
    create_address as create_address_service,
    list_addresses as list_addresses_service,
    get_address as get_address_service,
    update_address as update_address_service,
    delete_address as delete_address_service,
)
import json
import traceback
import sys

addresses_bp = Blueprint("addresses", __name__)


@addresses_bp.route("/addresses", methods=["POST"])
@jwt_required()
def create_address():
    """
      Create New Address
      ---
      tags:
        - Addresses
      summary: Create a new address for the authenticated user
      description: |
        Creates a new delivery address for the current user.
        The first address created will automatically be set as the primary address.

        Note: Coordinates (latitude/longitude) are required and cannot be modified after creation.
        Current time (UTC): 2025-01-15 15:14:10
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - title
                - longitude
                - latitude
                - street
                - district
                - province
                - country
                - postalCode
              properties:
                title:
                  type: string
                  description: Name/label for this address
                  example: "Home"
                  minLength: 1
                  maxLength: 100
                longitude:
                  type: number
                  format: float
                  description: Longitude coordinate
                  example: 28.979530
                latitude:
                  type: number
                  format: float
                  description: Latitude coordinate
                  example: 41.015137
                street:
                  type: string
                  description: Street name
                  example: "Istiklal Avenue"
                neighborhood:
                  type: string
                  description: Neighborhood name
                  example: "Beyoglu"
                district:
                  type: string
                  description: District/county name
                  example: "Beyoglu"
                province:
                  type: string
                  description: Province/city name
                  example: "Istanbul"
                country:
                  type: string
                  description: Country name
                  example: "Turkey"
                postalCode:
                  type: string
                  description: Postal/ZIP code
                  example: "34435"
                apartmentNo:
                  type: string
                  description: Apartment number (optional)
                  example: "4"
                doorNo:
                  type: string
                  description: Door/unit number (optional)
                  example: "2"
      responses:
        201:
          description: Address created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  message:
                    type: string
                    example: "Address created successfully!"
                  address:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      title:
                        type: string
                        example: "Home"
                      is_primary:
                        type: boolean
                        example: true
                      # ... other address fields
        400:
          description: Validation error
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: false
                  message:
                    type: string
                    example: "Title is required"
        401:
          description: Unauthorized - Invalid or missing token
        500:
          description: Server error
      """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "data": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        data = request.get_json()
        user_id = get_jwt_identity()
        response, status = create_address_service(user_id, data)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "success": False,
            "message": "An error occurred while creating the address.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@addresses_bp.route("/addresses", methods=["GET"])
@jwt_required()
def list_addresses():
    """
       List User Addresses
       ---
       tags:
         - Addresses
       summary: Retrieve all addresses for the authenticated user
       description: |
         Returns a list of all delivery addresses associated with the current user.
         Addresses are sorted with the primary address first.

         Current time (UTC): 2025-01-15 15:14:10
       security:
         - BearerAuth: []
       responses:
         200:
           description: List of addresses retrieved successfully
           content:
             application/json:
               schema:
                 type: array
                 items:
                   type: object
                   properties:
                     id:
                       type: integer
                       example: 1
                     title:
                       type: string
                       example: "Home"
                     longitude:
                       type: number
                       format: float
                       example: 28.979530
                     latitude:
                       type: number
                       format: float
                       example: 41.015137
                     street:
                       type: string
                       example: "Istiklal Avenue"
                     is_primary:
                       type: boolean
                       example: true
                     # ... other address fields
         401:
           description: Unauthorized - Invalid or missing token
         404:
           description: No addresses found
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   message:
                     type: string
                     example: "No addresses found for the user"
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
        response, status = list_addresses_service(user_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "message": "An error occurred while fetching addresses.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@addresses_bp.route("/addresses/<int:address_id>", methods=["GET"])
@jwt_required()
def get_address(address_id):
    """
        Update Address
        ---
        tags:
          - Addresses
        summary: Update an existing address
        description: |
          Updates the details of an existing address.
          Latitude and longitude cannot be modified after creation.
          Setting an address as primary will automatically unset the primary status of other addresses.

          Current time (UTC): 2025-01-15 15:14:10
        security:
          - BearerAuth: []
        parameters:
          - name: address_id
            in: path
            description: ID of the address to update
            required: true
            schema:
              type: integer
              example: 1
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  title:
                    type: string
                    example: "Office"
                  street:
                    type: string
                    example: "Bagdat Avenue"
                  neighborhood:
                    type: string
                    example: "Kadikoy"
                  district:
                    type: string
                    example: "Kadikoy"
                  province:
                    type: string
                    example: "Istanbul"
                  country:
                    type: string
                    example: "Turkey"
                  postalCode:
                    type: string
                    example: "34710"
                  apartmentNo:
                    type: string
                    example: "12"
                  doorNo:
                    type: string
                    example: "5"
                  is_primary:
                    type: boolean
                    description: Set this address as primary
                    example: true
        responses:
          200:
            description: Address updated successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    success:
                      type: boolean
                      example: true
                    message:
                      type: string
                      example: "Address updated successfully!"
                    address:
                      type: object
                      # ... address fields
          401:
            description: Unauthorized - Invalid or missing token
          404:
            description: Address not found
          500:
            description: Server error
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
        response, status = get_address_service(user_id, address_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "message": "An error occurred while fetching the address.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@addresses_bp.route("/addresses/<int:address_id>", methods=["PUT"])
@jwt_required()
def update_address(address_id):
    """
    Update an existing address
    ---
    tags:
      - Addresses
    security:
      - jwt: []
    parameters:
      - name: address_id
        in: path
        description: ID of the address to update
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              title:
                type: string
              # Note: latitude and longitude will be ignored if provided.
              street:
                type: string
              neighborhood:
                type: string
              district:
                type: string
              province:
                type: string
              country:
                type: string
              postalCode:
                type: string
              apartmentNo:
                type: string
              doorNo:
                type: string
              is_primary:
                type: boolean
    responses:
      200:
        description: Address updated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                message:
                  type: string
                address:
                  type: object
      404:
        description: Address not found
    """
    try:
        request_log = {
            "endpoint": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "data": request.get_json()
        }
        print(json.dumps({"request": request_log}, indent=2))

        user_id = get_jwt_identity()
        data = request.get_json()
        response, status = update_address_service(user_id, address_id, data)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "message": "An error occurred while updating the address.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500


@addresses_bp.route("/addresses/<int:address_id>", methods=["DELETE"])
@jwt_required()
def delete_address(address_id):
    """
    Delete an address
    ---
    tags:
      - Addresses
    security:
      - jwt: []
    parameters:
      - name: address_id
        in: path
        description: ID of the address to delete
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Address successfully deleted
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
      404:
        description: Address not found
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
        response, status = delete_address_service(user_id, address_id)

        print(json.dumps({"response": response, "status": status}, indent=2))
        return jsonify(response), status
    except Exception as e:
        print("An error occurred:", str(e))
        # Print traceback to console separately
        traceback.print_exc(file=sys.stderr)

        error_response = {
            "message": "An error occurred while deleting the address.",
            "error": str(e)
        }
        print(json.dumps({"error_response": error_response}, indent=2))
        return jsonify(error_response), 500