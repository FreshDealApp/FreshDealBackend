# services/report_service.py
from src.models import db, PurchaseReport, Purchase
from src.utils.cloud_storage import upload_file, allowed_file

def create_purchase_report_service(user_id, purchase_id, file_obj, description, url_for_func):
    """
    Create a report about a specific purchase.
    Includes a user-uploaded image and a brief explanation.
    Enforces:
      - The purchase must exist and belong to the user.
      - The user can report a purchase only once.
    """
    try:
        # Debug logging
        print(f"Creating report for user {user_id}, purchase {purchase_id}")

        # Verify the purchase exists and belongs to this user
        purchase = Purchase.query.filter_by(id=purchase_id, user_id=user_id).first()
        if not purchase:
            print(f"Purchase {purchase_id} not found for user {user_id}")
            return {"message": "Purchase not found or does not belong to the user."}, 404

        # Check for existing report
        existing_report = PurchaseReport.query.filter_by(
            user_id=user_id,
            purchase_id=purchase_id
        ).first()
        if existing_report:
            print(f"Existing report found for purchase {purchase_id}")
            return {"message": "You have already reported this purchase."}, 400

        # Handle file upload
        if not file_obj:
            print("No file object provided")
            return {"message": "Invalid or missing image file"}, 400

        if not file_obj.filename:
            print("No filename in file object")
            return {"message": "Invalid image file"}, 400

        if not allowed_file(file_obj.filename):
            print(f"Invalid file type: {file_obj.filename}")
            return {"message": "Invalid file type"}, 400

        try:
            # Upload file to cloud or local storage
            success, result = upload_file(
                file_obj=file_obj,
                folder="reports",
                url_for_func=url_for_func,
                url_endpoint='api_v1.report.get_uploaded_file'
            )

            if not success:
                return {"message": result}, 400

            image_url = result
            print(f"Generated image URL: {image_url}")

        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return {"message": f"Error saving file: {str(e)}"}, 500

        try:
            # Create report
            report = PurchaseReport(
                user_id=user_id,
                purchase_id=purchase_id,
                restaurant_id=purchase.listing.restaurant_id if purchase.listing else None,
                listing_id=purchase.listing.id if purchase.listing else None,
                image_url=image_url,
                description=description
            )

            db.session.add(report)
            db.session.commit()

            print(f"Report created successfully with ID: {report.id}")
            return {
                "message": "Report created successfully",
                "report_id": report.id
            }, 201

        except Exception as e:
            print(f"Database error: {str(e)}")
            db.session.rollback()
            return {"message": f"Database error: {str(e)}"}, 500

    except Exception as e:
        import traceback
        print("Error in create_purchase_report_service:", str(e))
        print("Traceback:", traceback.format_exc())
        return {
            "message": "An error occurred while creating the report",
            "error": str(e)
        }, 500


def get_user_reports_service(user_id):
    """
    Return all reports made by a specific user.
    """
    try:
        reports = PurchaseReport.query.filter_by(user_id=user_id).all()
        if not reports:
            return {"message": "No reports found for this user"}, 200

        data = []
        for r in reports:
            data.append({
                "report_id": r.id,
                "purchase_id": r.purchase_id,
                "listing_id": r.listing_id,
                "restaurant_id": r.restaurant_id,
                "image_url": r.image_url,
                "description": r.description,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None
            })

        return {"reports": data}, 200

    except Exception as e:
        return {
            "message": "An error occurred while fetching user reports",
            "error": str(e)
        }, 500