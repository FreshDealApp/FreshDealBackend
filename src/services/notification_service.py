import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from src.models import db, UserDevice, User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class for handling push notifications and device token management."""

    EXPO_PUSH_API = "https://exp.host/--/api/v2/push/send"

    @staticmethod
    def clean_token(token: str) -> str:
        """Remove Expo wrapper from token for storage."""
        if token.startswith('ExponentPushToken['):
            return token[17:-1]  # Remove 'ExponentPushToken[' and ']'
        return token

    @staticmethod
    def format_expo_token(token: str) -> str:
        """Add Expo wrapper to token for API calls."""
        if token.startswith('ExponentPushToken['):
            return token
        return f"ExponentPushToken[{token}]"

    @staticmethod
    def update_push_token(user_id: int, token: str, device_type: str, platform: str) -> Tuple[bool, str]:
        """
        Update or create a device push token for a user.

        Args:
            user_id (int): The ID of the user
            token (str): The push notification token
            device_type (str): The type of device (ios/android)
            platform (str): The platform version

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Clean the token before storing
            cleaned_token = NotificationService.clean_token(token)
            current_time = datetime.utcnow()

            # Check if token already exists for this user
            device = UserDevice.query.filter_by(
                user_id=user_id,
                push_token=cleaned_token
            ).first()

            if device:
                # Update existing device
                device.last_used = current_time
                device.device_type = device_type
                device.platform = platform
                device.is_active = True
                logger.info(f"Updated existing device token for user {user_id}")
            else:
                # Create new device
                device = UserDevice(
                    user_id=user_id,
                    push_token=cleaned_token,
                    device_type=device_type,
                    platform=platform,
                    created_at=current_time,
                    last_used=current_time,
                    is_active=True
                )
                db.session.add(device)
                logger.info(f"Created new device token for user {user_id}")

            db.session.commit()
            return True, "Push token updated successfully"

        except Exception as e:
            logger.error(f"Error updating push token for user {user_id}: {str(e)}")
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def send_push_notification(
            tokens: List[str],
            title: str,
            body: str,
            data: Dict[str, Any] = None
    ) -> bool:
        """
        Send push notifications to multiple devices.

        Args:
            tokens (List[str]): List of device tokens
            title (str): Notification title
            body (str): Notification body
            data (Dict[str, Any], optional): Additional data to send

        Returns:
            bool: Success status
        """
        try:
            if not tokens:
                logger.warning("No tokens provided for push notification")
                return False

            # Format tokens for Expo API
            formatted_tokens = [NotificationService.format_expo_token(token) for token in tokens]

            notifications = [
                {
                    "to": token,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "sound": "default",
                    "priority": "high",
                }
                for token in formatted_tokens
            ]

            logger.info(f"Sending push notification to {len(tokens)} devices")

            response = requests.post(
                NotificationService.EXPO_PUSH_API,
                json=notifications,
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                timeout=10  # Add timeout to prevent hanging
            )

            if response.status_code == 200:
                response_data = response.json()
                # Log any errors from Expo
                if 'errors' in response_data:
                    logger.error(f"Expo API returned errors: {response_data['errors']}")
                logger.info("Push notifications sent successfully")
                return True
            else:
                logger.error(f"Push notification failed with status {response.status_code}: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Timeout while sending push notification")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while sending push notification: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return False

    @staticmethod
    def send_notification_to_user(
            user_id: int,
            title: str,
            body: str,
            data: Dict[str, Any] = None
    ) -> bool:
        """
        Send a push notification to all active devices of a user.

        Args:
            user_id (int): The ID of the user
            title (str): Notification title
            body (str): Notification body
            data (Dict[str, Any], optional): Additional data to send

        Returns:
            bool: Success status
        """
        try:
            # Get active devices for the user
            devices = UserDevice.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            if not devices:
                logger.warning(f"No active devices found for user {user_id}")
                return False

            tokens = [device.push_token for device in devices]
            logger.info(f"Sending notification to user {user_id} ({len(tokens)} devices)")
            return NotificationService.send_push_notification(tokens, title, body, data)

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
            return False

    @staticmethod
    def deactivate_token(token: str) -> bool:
        """
        Deactivate a push token.

        Args:
            token (str): The token to deactivate

        Returns:
            bool: Success status
        """
        try:
            cleaned_token = NotificationService.clean_token(token)
            device = UserDevice.query.filter_by(push_token=cleaned_token).first()

            if device:
                device.is_active = False
                device.last_used = datetime.utcnow()
                db.session.commit()
                logger.info(f"Successfully deactivated token for device {device.id}")
                return True

            logger.warning(f"Token not found for deactivation: {cleaned_token}")
            return False

        except Exception as e:
            logger.error(f"Error deactivating token: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def clean_inactive_tokens(days_threshold: int = 30) -> int:
        """
        Clean up inactive tokens older than the specified threshold.

        Args:
            days_threshold (int): Number of days of inactivity before cleaning

        Returns:
            int: Number of tokens cleaned
        """
        try:
            threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

            # Find inactive tokens
            inactive_devices = UserDevice.query.filter(
                UserDevice.last_used < threshold_date,
                UserDevice.is_active == False
            ).all()

            count = len(inactive_devices)

            # Delete inactive tokens
            for device in inactive_devices:
                db.session.delete(device)

            db.session.commit()
            logger.info(f"Cleaned {count} inactive tokens")
            return count

        except Exception as e:
            logger.error(f"Error cleaning inactive tokens: {str(e)}")
            db.session.rollback()
            return 0

    @staticmethod
    def get_user_devices(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all devices registered for a user.

        Args:
            user_id (int): The ID of the user

        Returns:
            List[Dict[str, Any]]: List of device information
        """
        try:
            devices = UserDevice.query.filter_by(user_id=user_id).all()
            return [{
                'id': device.id,
                'device_type': device.device_type,
                'platform': device.platform,
                'created_at': device.created_at.isoformat(),
                'last_used': device.last_used.isoformat(),
                'is_active': device.is_active
            } for device in devices]

        except Exception as e:
            logger.error(f"Error getting devices for user {user_id}: {str(e)}")
            return []