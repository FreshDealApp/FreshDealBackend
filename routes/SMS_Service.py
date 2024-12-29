from twilio.rest import Client

# Twilio Informations will be gathered with github for students pack
TWILIO_SID = "your_twilio_sid"
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_PHONE_NUMBER = "your_twilio_phone_number"


def send_sms(phone_number, message):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )

    return {"status": "success", "message": f"SMS sent successfully, SID: {message.sid}"}
