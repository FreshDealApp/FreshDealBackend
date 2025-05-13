import json
import logging
from typing import Dict, Any, List, Optional, Union
import requests
from pywebpush import webpush, WebPushException
from datetime import datetime, UTC

from src.models import db, UserDevice

logger = logging.getLogger(__name__)


class WebPushNotificationService:
    @staticmethod
    def register_web_push_token(
            user_id: int,
            subscription_info: Dict[str, Any],
            user_agent: str = None
    ) -> tuple:
        try:
            subscription_json = json.dumps(subscription_info)

            existing_device = UserDevice.query.filter_by(
                user_id=user_id,
                web_push_token=subscription_json
            ).first()

            if existing_device:
                existing_device.last_used = datetime.now(UTC)
                existing_device.is_active = True
                existing_device.device_type = "web"
                existing_device.platform = user_agent or "browser"
                db.session.commit()
                logger.info(f"Updated web push subscription for user {user_id}")
                return True, "Web push subscription updated successfully"

            new_device = UserDevice(
                user_id=user_id,
                push_token=f"web_{user_id}_{datetime.now(UTC).timestamp()}",
                web_push_token=subscription_json,
                device_type="web",
                platform=user_agent or "browser",
                created_at=datetime.now(UTC),
                last_used=datetime.now(UTC),
                is_active=True
            )

            db.session.add(new_device)
            db.session.commit()
            logger.info(f"Registered new web push subscription for user {user_id}")
            return True, "Web push subscription registered successfully"

        except Exception as e:
            logger.error(f"Error registering web push subscription: {str(e)}")
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def send_web_push_notification(
            subscription_info: Dict[str, Any],
            title: str,
            body: str,
            icon: str = None,
            badge: str = None,
            image: str = None,
            data: Dict[str, Any] = None,
            actions: List[Dict[str, str]] = None,
            tag: str = None,
            require_interaction: bool = False
    ) -> bool:
        try:
            import os
            vapid_claims = {
                "sub": "mailto:contact@freshdeal.com",
            }

            payload_data = {
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": icon,
                    "badge": badge,
                    "image": image,
                    "data": data or {},
                    "requireInteraction": require_interaction
                }
            }

            if actions:
                payload_data["notification"]["actions"] = actions

            if tag:
                payload_data["notification"]["tag"] = tag

            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload_data),
                vapid_private_key=os.environ.get('VAPID_PRIVATE_KEY'),
                vapid_claims=vapid_claims
            )

            logger.info("Web push notification sent successfully")
            return True

        except WebPushException as e:
            logger.error(f"WebPushException: {str(e)}")
            if e.response and e.response.status_code == 410:
                logger.info("Subscription is no longer valid")
            return False
        except Exception as e:
            logger.error(f"Error sending web push notification: {str(e)}")
            return False

    @staticmethod
    def send_notification_to_user_web(
            user_id: int,
            title: str,
            body: str,
            data: Dict[str, Any] = None,
            icon: str = None,
            **kwargs
    ) -> bool:
        try:
            web_devices = UserDevice.query.filter_by(
                user_id=user_id,
                device_type="web",
                is_active=True
            ).all()

            if not web_devices:
                logger.warning(f"No active web devices found for user {user_id}")
                return False

            success_count = 0

            for device in web_devices:
                try:
                    if device.web_push_token:
                        subscription_info = json.loads(device.web_push_token)
                    else:
                        subscription_info = json.loads(device.push_token)

                    success = WebPushNotificationService.send_web_push_notification(
                        subscription_info=subscription_info,
                        title=title,
                        body=body,
                        icon=icon,
                        data=data,
                        **kwargs
                    )

                    if success:
                        success_count += 1

                except json.JSONDecodeError:
                    logger.error(f"Invalid subscription info for device {device.id}")
                    continue

            logger.info(
                f"Successfully sent web notifications to {success_count}/{len(web_devices)} devices for user {user_id}")
            return success_count > 0

        except Exception as e:
            logger.error(f"Error sending web notification to user {user_id}: {str(e)}")
            return False