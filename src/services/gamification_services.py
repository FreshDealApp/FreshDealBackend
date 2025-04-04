from flask import jsonify
from src.models import db, DiscountEarned, User, Purchase, Listing, RestaurantBadgePoints
from sqlalchemy import func
from datetime import datetime


def add_discount_point(purchase_id):
    purchase = Purchase.query.filter_by(id=purchase_id).first()
    if not purchase:
        print(f"[DEBUG] Purchase with id {purchase_id} not found.")
        return

    user_id = purchase.user_id

    # Fix: Add .first() to get the actual Listing object
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
    results = db.session.query(
                DiscountEarned.user_id.label('user_id'),
                User.name.label('user_name'),
                func.sum(DiscountEarned.discount).label('total_discount')
            ) \
            .join(User, User.id == DiscountEarned.user_id) \
            .group_by(DiscountEarned.user_id) \
            .order_by(func.sum(DiscountEarned.discount).desc()) \
            .all()


    user_rankings = []
    rank = 1
    for user_id, user_name, total_discount in results:
        if total_discount is None:
            total_discount = 0.0
        else:
            total_discount = float(total_discount)

        user_rankings.append({
            'rank': rank,
            'user_id': user_id,
            'user_name': user_name,
            'total_discount': float(total_discount)
        })
        rank += 1

    return jsonify(user_rankings)


def get_single_user_rank(user_id):
    """
    Get the rank of a specific user based on their total discount earned.

    Args:
        user_id: The ID of the user whose rank we want to find

    Returns:
        JSON response with the user's rank information or an error message
    """
    # First check if the user exists
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get the user's total discount
    user_discount = db.session.query(
        func.sum(DiscountEarned.discount).label('total_discount')
    ) \
        .filter(DiscountEarned.user_id == user_id) \
        .scalar()

    if user_discount is None:
        user_discount = 0.0
    else:
        user_discount = float(user_discount)

    # Get the count of users with higher total discount
    higher_ranked_count = db.session.query(func.count()) \
        .select_from(
        db.session.query(
            DiscountEarned.user_id,
            func.sum(DiscountEarned.discount).label('total_disc')
        ) \
            .group_by(DiscountEarned.user_id) \
            .having(func.sum(DiscountEarned.discount) > user_discount) \
            .subquery()
    ) \
        .scalar()

    # User's rank is the count of users with higher discount + 1
    rank = higher_ranked_count + 1

    return jsonify({
        'user_id': user_id,
        'user_name': user.name,
        'rank': rank,
        'total_discount': user_discount
    })


def add_restaurant_badge_point(restaurant_id, badge_name):
    valid_badges = ['fresh', 'fast_delivery', 'customer_friendly']
    if badge_name not in valid_badges:
        print(f"Error: '{badge_name}' is not a valid badge name.")
        return

    existing_badge = RestaurantBadgePoints.query.filter_by(restaurantID=restaurant_id).first()

    if existing_badge:
        if badge_name == 'fresh':
            existing_badge.freshPoint += 1
        elif badge_name == 'fast_delivery':
            existing_badge.fastDeliveryPoint += 1
        elif badge_name == 'customer_friendly':
            existing_badge.customerFriendlyPoint += 1

        db.session.commit()
    else:
        new_badge = RestaurantBadgePoints(
            restaurantID=restaurant_id,
            freshPoint=1 if badge_name == 'fresh' else 0,
            fastDeliveryPoint=1 if badge_name == 'fast_delivery' else 0,
            customerFriendlyPoint=1 if badge_name == 'customer_friendly' else 0
        )

        db.session.add(new_badge)
        db.session.commit()


def get_restaurant_badges(restaurant_id):
    badge_data = RestaurantBadgePoints.query.filter_by(restaurantID=restaurant_id).first()

    if not badge_data:
        return []

    badges = []

    if badge_data.freshPoint > 100:
        badges.append('super_fresh')
    elif badge_data.freshPoint > 10:
        badges.append('fresh')

    if badge_data.fastDeliveryPoint > 100:
        badges.append('super_fast_delivery')
    elif badge_data.fastDeliveryPoint > 10:
        badges.append('fast_delivery')

    if badge_data.customerFriendlyPoint > 100:
        badges.append('super_customer_friendly')
    elif badge_data.customerFriendlyPoint > 10:
        badges.append('customer_friendly')

    return badges