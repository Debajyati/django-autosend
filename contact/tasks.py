from celery import shared_task
import logging
import requests
from typing import Dict, Optional, Tuple, TypedDict, Union
from django.conf import settings
logger = logging.getLogger(__name__)


@shared_task
def send_confirmation_email(name, email, from_name, from_email, message) -> None:
    email_content = _generate_confirmation_email_html(name, message)
    email_text_content = _generate_confirmation_email_text(name, message)
    payload = {
        "to": {
            "email": email,
            "name": name,
        },
        "from": {
            "email": from_email,
            "name": from_name,
        },
        "subject": "Thank you for contacting us",
        "html": email_content,
        "text": email_text_content,
    }
    success, data = send_email(payload)
    if not success:
        logger.error(data["error"])


def _generate_confirmation_email_html(name: str, message: str) -> str:
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #a0a00a 50%, #0a0a0a 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Message Received!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd; border-top: none;">
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Hi <strong>{name}</strong>,
                </p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Thank you for reaching out! We've received your message and will get back to you as soon as possible.
                </p>
                
                <div style="background: #a0a00add; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #ffffff;">
                        <b>✓ Your message has been successfully delivered to our site administrator.</b>
                    </p>
                </div>
                
                <h3 style="color: black; margin-top: 30px; margin-bottom: 15px;">Your Message:</h3>
                <div style="background: white; padding: 20px; border-left: 4px solid black; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; white-space: pre-wrap; word-wrap: break-word; color: #555;">{message}</p>
                </div>
                
                <p style="font-size: 14px; color: black; margin-top: 30px;">
                    We typically respond within 24-48 hours. In the meantime, feel free to explore our website for more information.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>This is a system generated email.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

def _generate_confirmation_email_text(name: str, message: str) -> str:
    return f"""
    Hi {name},

    Thank you for reaching out! We've received your message and will get back to you as soon as possible.

    ✓ Your message has been successfully delivered to our site administrator.

    Your Message:
    --------------------
    {message}
    --------------------

    We typically respond within 24-48 hours. In the meantime, feel free to explore our website for more information.

    This is a system generated email.
    Please do not reply to this email.
    """

class AutosendErrorResponseData(TypedDict):
    message: str
    code: str
    details: Optional[Dict[str, str]]
    retryAfter: Optional[int]

class AutosendResponseData(TypedDict):
    success: bool
    data: Optional[Dict]
    error: Optional[AutosendErrorResponseData]

def send_email(payload: Dict) -> Tuple[bool, Union[AutosendResponseData, Dict]]:
    """
        Send email via Autosend API

        Returns:
            Tuple of (success: bool, response_data: AutosendResponseData or error dict)
    """
    api_url = settings.AUTOSEND_API_URL
    api_key = settings.AUTOSEND_API_KEY
    try:
        response = requests.post(
            url=api_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=10.0
        )

        response_data: AutosendResponseData = response.json()

        if response.status_code == 200:
            logger.info(f"Email sent successfully. Message: {response_data}")
            return True, response_data
        else:
            error_msg = response_data.get('error')
            logger.error(f"Autosend API error: {error_msg}")
            return False, response_data

    except requests.exceptions.Timeout:
        logger.error("Autosend API request timed out")
        return False, {'error': 'Request timeout'}
    except requests.exceptions.RequestException as e:
        logger.error(f"Autosend API request failed: {str(e)}")
        return False, {'error': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False, {'error': str(e)}
