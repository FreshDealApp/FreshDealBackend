from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, CustomerAddress

customerAddressManager_bp = Blueprint("customerAddressManager", __name__)


@customerAddressManager_bp.route("/add_customer_address", methods=["POST"])
@jwt_required()
def add_customer_address():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        title = data.get('title')
        longitude = data.get('longitude')
        latitude = data.get('latitude')
        street = data.get('street')
        neighborhood = data.get('neighborhood')
        district = data.get('district')
        province = data.get('province')
        country = data.get('country')
        postalCode = data.get('postalCode')
        apartmentNo = data.get('apartmentNo')
        doorNo = data.get('doorNo')
        if not title:
            print("Validation error: Title is missing.")
            return jsonify({"success": False, "message": "Title is required"}), 400

        if longitude is None or latitude is None:
            print("Validation error: Longitude or Latitude is missing.")
            return jsonify({"success": False, "message": "Longitude and latitude are required"}), 400

        # Create new address
        new_address = CustomerAddress(
            user_id=user_id,
            title=title,
            longitude=longitude,
            latitude=latitude,
            street=street,
            neighborhood=neighborhood,
            district=district,
            province=province,
            country=country,
            postalCode=postalCode,
            apartmentNo=apartmentNo,
            doorNo=doorNo
        )
        db.session.add(new_address)
        db.session.commit()
        return jsonify({"message": "New customer address is successfully added!"}), 201
    except Exception as e:
        # Log any unexpected exceptions
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500


@customerAddressManager_bp.route("/get_customer_address", methods=["GET"])
@jwt_required()
def get_customer_address():
    user_id = get_jwt_identity()
    addresses = CustomerAddress.query.filter_by(user_id=user_id).all()

    if not addresses:
        return jsonify({"message": "No address found for the user"}), 404

    serialized_address = []
    for address in addresses:
        serialized_address.append({
        "id": address.id,
        "title": address.title,
        "longitude": address.longitude,
        "latitude": address.latitude,
        "street": address.street,
        "neighborhood": address.neighborhood,
        "district": address.district,
        "province": address.province,
        "country": address.country,
        "postalCode": address.postalCode,
        "apartmentNo": address.apartmentNo,
        "doorNo": address.doorNo
        })
        return jsonify(serialized_address), 200

@customerAddressManager_bp.route("/delete_customer_address/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_customer_address(id):
    user_id = get_jwt_identity()
    
    address = CustomerAddress.query.filter_by(id=id, user_id=user_id).first()

    if not address:
        return jsonify({"message": "Address not found"}), 404

    db.session.delete(address)
    db.session.commit()

    return jsonify({"message": "Address successfully deleted!"}), 200