from decimal import Decimal


def calculate_discount_amount(total_price):
    """
    Calculate discount amount based on the total purchase price.

    Discount rules:
    - $50 off for purchases of $150+
    - $75 off for purchases of $200+
    - $100 off for purchases of $250+
    - $150 off for purchases of $400+

    Returns: Discount amount as a Decimal
    """
    total_price = Decimal(total_price)

    if total_price >= Decimal('400'):
        return Decimal('150')
    elif total_price >= Decimal('250'):
        return Decimal('100')
    elif total_price >= Decimal('200'):
        return Decimal('75')
    elif total_price >= Decimal('150'):
        return Decimal('50')
    else:
        return Decimal('0')


def apply_discount(purchases):
    """
    Apply discounts based on the total price of all purchases in the cart.

    Args:
        purchases: List of Purchase objects to check for discount eligibility

    Returns:
        tuple: (total_before_discount, discount_amount, purchases_after_discount)
    """
    if not purchases:
        return Decimal('0'), Decimal('0'), []

    # Calculate total purchase amount before discount
    total_before_discount = sum(Decimal(purchase.total_price) for purchase in purchases)

    # Calculate discount based on total
    discount_amount = calculate_discount_amount(total_before_discount)

    # If no discount, return original values
    if discount_amount <= 0:
        return total_before_discount, Decimal('0'), purchases

    # Apply discount proportionally to each purchase
    purchases_after_discount = []

    # If there's only one purchase, apply the discount directly
    if len(purchases) == 1:
        purchase = purchases[0]
        new_total = max(Decimal(purchase.total_price) - discount_amount, Decimal('0'))
        purchase.total_price = new_total
        purchases_after_discount.append(purchase)
    else:
        # For multiple items, distribute discount proportionally
        remaining_discount = discount_amount

        # Sort purchases by price (highest first) to apply discount to most expensive items first
        sorted_purchases = sorted(purchases, key=lambda p: Decimal(p.total_price), reverse=True)

        for purchase in sorted_purchases:
            # Calculate proportion of this purchase to total
            purchase_ratio = Decimal(purchase.total_price) / total_before_discount

            # Calculate discount for this purchase
            purchase_discount = (discount_amount * purchase_ratio).quantize(Decimal('0.01'))

            # Make sure we don't exceed the total discount
            if purchase_discount > remaining_discount:
                purchase_discount = remaining_discount

            # Apply discount to purchase
            new_total = max(Decimal(purchase.total_price) - purchase_discount, Decimal('0'))
            purchase.total_price = new_total
            purchases_after_discount.append(purchase)

            # Update remaining discount
            remaining_discount -= purchase_discount

            # If no discount remains, exit loop
            if remaining_discount <= 0:
                break

    return total_before_discount, discount_amount, purchases_after_discount