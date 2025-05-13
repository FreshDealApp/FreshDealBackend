from datetime import datetime, timedelta
from pytz import UTC
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.models.listing_model import Listing
from src.models import db

def update_all_listings():
    try:
        listings = Listing.query.filter(Listing.expires_at > datetime.now(UTC)).all()
        for listing in listings:
            listing.update_expiry()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating listings: {str(e)}")

def init_listing_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=update_all_listings,
        trigger=IntervalTrigger(hours=2),
        id='update_listings_job',
        name='Update listings fresh score and consume within time',
        replace_existing=True
    )
    scheduler.start()
    return scheduler