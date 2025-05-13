from flask import Blueprint

from src.routes.analytics_routes import analytics_bp
from src.routes.auth_routes import auth_bp
from src.routes.address_routes import addresses_bp
from src.routes.report_routes import report_bp
from src.routes.restaurant_routes import restaurant_bp
from src.routes.static_routes import static_bp
from src.routes.user_routes import user_bp
from src.routes.listing_routes import listings_bp
from src.routes.cart_routes import cart_bp
from src.routes.search_routes import search_bp
from src.routes.purchase_routes import purchase_bp
from src.routes.notification_routes import notification_bp
from src.routes.gamification_routes import gamification_bp
from src.routes.achievement_routes import achievement_bp
from src.routes.restaurant_badge_routes import restaurant_badge_bp
from src.routes.comment_analysis_routes import comment_analysis_bp
from src.routes.restaurant_punishment_routes import restaurant_punishment_bp
from src.routes.rec_routes import recommendation_bp
from src.routes.restaurant_rec_routes import restaurant_recommendation_bp
from src.routes.web_push_notification_routes import web_push_bp
from src.routes.flash_deals_routes import flash_deals_bp
from src.routes.environmental_routes import environmental_bp

def init_app(app):
    api_v1 = Blueprint('api_v1', __name__, url_prefix='/v1')
    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(addresses_bp)
    api_v1.register_blueprint(restaurant_bp)
    api_v1.register_blueprint(user_bp)
    api_v1.register_blueprint(listings_bp)
    api_v1.register_blueprint(cart_bp)
    api_v1.register_blueprint(search_bp)
    api_v1.register_blueprint(purchase_bp)
    api_v1.register_blueprint(report_bp)
    api_v1.register_blueprint(notification_bp)
    api_v1.register_blueprint(gamification_bp)
    api_v1.register_blueprint(achievement_bp)
    api_v1.register_blueprint(restaurant_badge_bp)
    api_v1.register_blueprint(static_bp)
    api_v1.register_blueprint(analytics_bp)
    api_v1.register_blueprint(comment_analysis_bp)
    api_v1.register_blueprint(restaurant_punishment_bp)
    api_v1.register_blueprint(recommendation_bp)
    api_v1.register_blueprint(restaurant_recommendation_bp)
    api_v1.register_blueprint(web_push_bp)
    api_v1.register_blueprint(flash_deals_bp)
    api_v1.register_blueprint(environmental_bp)
    app.register_blueprint(api_v1)