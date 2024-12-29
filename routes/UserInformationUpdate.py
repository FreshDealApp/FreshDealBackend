from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, CustomerAddress

@user_bp.route("/user/update", methods=["PUT"])
@jwt_required()
def update_user_data():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"message": "User not found"}), 404
        user_data = request.json.get("user_data", {})
        if "name" in user_data:
            user.name = user_data["name"]
        if "email" in user_data:
            user.email = user_data["email"]
        if "phone_number" in user_data:
            user.phone_number = user_data["phone_number"]
        if "role" in user_data:
            user.role = user_data["role"]
        addresses_data = request.json.get("user_address_list", [])
        for addr_data in addresses_data:
            address_id = addr_data.get("id")
            if address_id:
                address = CustomerAddress.query.filter_by(id=address_id, user_id=user_id).first()
                if not address:
                    return jsonify({"message": f"Address with id {address_id} not found"}), 404

                address.title = addr_data.get("title", address.title)
                address.longitude = addr_data.get("longitude", address.longitude)
                address.latitude = addr_data.get("latitude", address.latitude)
                address.street = addr_data.get("street", address.street)
                address.neighborhood = addr_data.get("neighborhood", address.neighborhood)
                address.district = addr_data.get("district", address.district)
                address.province = addr_data.get("province", address.province)
                address.country = addr_data.get("country", address.country)
                address.postalCode = addr_data.get("postalCode", address.postalCode)
                address.apartmentNo = addr_data.get("apartmentNo", address.apartmentNo)
                address.doorNo = addr_data.get("doorNo", address.doorNo)
            else:
                new_address = CustomerAddress(
                    user_id=user_id,
                    title=addr_data.get("title"),
                    longitude=addr_data.get("longitude"),
                    latitude=addr_data.get("latitude"),
                    street=addr_data.get("street"),
                    neighborhood=addr_data.get("neighborhood"),
                    district=addr_data.get("district"),
                    province=addr_data.get("province"),
                    country=addr_data.get("country"),
                    postalCode=addr_data.get("postalCode"),
                    apartmentNo=addr_data.get("apartmentNo"),
                    doorNo=addr_data.get("doorNo"),
                )
                db.session.add(new_address)
        db.session.commit()

        return jsonify({"success": True, "message": "User information updated successfully"}), 200

    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500
