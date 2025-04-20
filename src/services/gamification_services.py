from flask import jsonify
from src.models import db, DiscountEarned, User, Purchase, Listing
from sqlalchemy import func
from datetime import datetime

def add_discount_point(purchase_id):
    """
    Adds a discount point record for a given purchase.
    """
    purchase = Purchase.query.filter_by(id=purchase_id).first()
    if not purchase:
        print(f"[DEBUG] Purchase with id {purchase_id} not found.")
        return

    user_id = purchase.user_id
    listing = Listing.query.filter_by(id=purchase.listing_id).first()
    if not listing:
        print(f"[DEBUG] Listing with id {purchase.listing_id} not found.")
        return

    discount = (purchase.quantity * float(listing.original_price)) - float(purchase.total_price)

    new_discount_point = DiscountEarned(
        user_id=user_id,
        discount=discount,
        earned_at=datetime.now()
    )

    db.session.add(new_discount_point)
    db.session.commit()

def get_user_rankings():
    """
    Retrieves a JSON response with user rankings based on the total discount earned.
    """
    results = db.session.query(
                DiscountEarned.user_id.label('user_id'),
                User.name.label('user_name'),
                func.sum(DiscountEarned.discount).label('total_discount')
            ) \
            .join(User, User.id == DiscountEarned.user_id) \
            .group_by(DiscountEarned.user_id, User.name) \
            .order_by(func.sum(DiscountEarned.discount).desc()) \
            .all()

    user_rankings = []
    rank = 1
    for user_id, user_name, total_discount in results:
        total_discount = float(total_discount or 0.0)
        user_rankings.append({
            'rank': rank,
            'user_id': user_id,
            'user_name': user_name,
            'total_discount': total_discount
        })
        rank += 1

    return jsonify(user_rankings)

def get_monthly_user_rankings():
    """
    Retrieves a JSON response with user rankings based on the total discount earned
    in the last 30 days.
    """
    from datetime import datetime, timedelta

    thirty_days_ago = datetime.now() - timedelta(days=30)

    results = db.session.query(
                DiscountEarned.user_id.label('user_id'),
                User.name.label('user_name'),
                func.sum(DiscountEarned.discount).label('total_discount')
            ) \
            .join(User, User.id == DiscountEarned.user_id) \
            .filter(DiscountEarned.earned_at >= thirty_days_ago) \
            .group_by(DiscountEarned.user_id) \
            .order_by(func.sum(DiscountEarned.discount).desc()) \
            .all()

    user_rankings = []
    rank = 1
    for user_id, user_name, total_discount in results:
        total_discount = float(total_discount or 0.0)
        user_rankings.append({
            'rank': rank,
            'user_id': user_id,
            'user_name': user_name,
            'total_discount': total_discount
        })
        rank += 1

    return jsonify(user_rankings)


def get_single_user_rank(user_id):
    """
    Retrieves the ranking information for a single user.
    """
    # Check if the user exists
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Calculate the user's total discount earned
    user_discount = db.session.query(
        func.sum(DiscountEarned.discount).label('total_discount')
    ).filter(DiscountEarned.user_id == user_id).scalar()

    user_discount = float(user_discount or 0.0)

    # Count the number of users with a higher total discount
    higher_ranked_count = db.session.query(func.count()) \
        .select_from(
            db.session.query(
                DiscountEarned.user_id,
                func.sum(DiscountEarned.discount).label('total_disc')
            ).group_by(DiscountEarned.user_id)
             .having(func.sum(DiscountEarned.discount) > user_discount)
             .subquery()
        ).scalar()

    rank = higher_ranked_count + 1

    return jsonify({
        'user_id': user_id,
        'user_name': user.name,
        'rank': rank,
        'total_discount': user_discount
    })

def get_single_user_monthly_rank(user_id):
    """
    Retrieves the ranking information for a single user based on the total discount
    earned in the last 30 days.
    """
    from datetime import datetime, timedelta

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    thirty_days_ago = datetime.now() - timedelta(days=30)

    # User's discount in the last 30 days
    user_discount = db.session.query(
        func.sum(DiscountEarned.discount).label('total_discount')
    ).filter(
        DiscountEarned.user_id == user_id,
        DiscountEarned.earned_at >= thirty_days_ago
    ).scalar()

    user_discount = float(user_discount or 0.0)

    # Count how many users have higher total discount in last 30 days
    higher_ranked_count = db.session.query(func.count()) \
        .select_from(
            db.session.query(
                DiscountEarned.user_id,
                func.sum(DiscountEarned.discount).label('total_disc')
            )
            .filter(DiscountEarned.earned_at >= thirty_days_ago)
            .group_by(DiscountEarned.user_id)
            .having(func.sum(DiscountEarned.discount) > user_discount)
            .subquery()
        ).scalar()

    rank = higher_ranked_count + 1

    return jsonify({
        'user_id': user_id,
        'user_name': user.name,
        'rank': rank,
        'total_discount': user_discount
    })
