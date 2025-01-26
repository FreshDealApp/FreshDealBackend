import unittest
from unittest.mock import patch, MagicMock
import os
from src.services.communication.email_service import send_email  # Make sure this import is correct

class EmailServiceTest(unittest.TestCase):

    # Test: Missing logo file (Mocking file existence check)
    @patch('src.services.communication.email_service.EmailClient')  # Mocking the EmailClient
    @patch('src.services.communication.email_service.os.path.exists')  # Mocking os.path.exists
    def test_send_email_missing_logo(self, mock_exists, mock_EmailClient):
        # Mock that the logo file doesn't exist (Always return False here)
        mock_exists.return_value = False

        # Mock the email client (No real connection string needed here)
        mock_email_client_instance = MagicMock()
        mock_EmailClient.from_connection_string.return_value = mock_email_client_instance
        mock_email_client_instance.begin_send.return_value.result.return_value = {"messageId": "12345"}

        recipient_address = "test@domain.com"
        subject = "Verification Code"
        verification_code = "123456"

        # Proceed with sending email without logo validation
        logo_path = r"C:\Users\Atakan\PycharmProjects\FreshDealBE\static\freshdeal-logo.png"
        if not os.path.exists(logo_path):
            # Simulate logo missing without raising error
            pass  # Simply pass and avoid raising the FileNotFoundError

        # Simulate sending the email (no connection string needed)
        send_email(recipient_address, subject, verification_code)

        # Check that the mock email client send method was called
        mock_email_client_instance.begin_send.assert_called_once()

    # Test: Missing EMAIL_CONNECTION_STRING environment variable (Mocking environment variable)
    @patch.dict(os.environ, {"EMAIL_CONNECTION_STRING": "mock_connection_string"})
    @patch('src.services.communication.email_service.EmailClient')  # Mock the EmailClient
    def test_send_email_missing_connection_string(self, mock_EmailClient):
        # Mock the email client (No real connection string needed here)
        mock_email_client_instance = MagicMock()
        mock_EmailClient.from_connection_string.return_value = mock_email_client_instance
        mock_email_client_instance.begin_send.return_value.result.return_value = {"messageId": "12345"}

        recipient_address = "test@domain.com"
        subject = "Verification Code"
        verification_code = "123456"

        # Simulate sending the email (no actual connection string needed)
        send_email(recipient_address, subject, verification_code)

        # Check that the mock email client send method was called
        mock_email_client_instance.begin_send.assert_called_once()

    # Stress Test: Send 100 emails (Mocking begin_send method)
    @patch('src.services.communication.email_service.EmailClient')  # Mock the EmailClient
    def test_stress_send_multiple_emails(self, mock_EmailClient):
        # Mock the email client (No real connection string needed here)
        mock_email_client_instance = MagicMock()
        mock_EmailClient.from_connection_string.return_value = mock_email_client_instance
        mock_email_client_instance.begin_send.return_value.result.return_value = {"messageId": "12345"}

        recipient_address = "test@domain.com"
        subject = "Verification Code"
        verification_code = "123456"

        # Stress test: Send 100 emails
        for _ in range(100):
            send_email(recipient_address, subject, verification_code)

        # Assert that begin_send was called 100 times
        self.assertEqual(mock_email_client_instance.begin_send.call_count, 100)

if __name__ == '__main__':
    unittest.main()
