"""
Phone Service
Twilio call logging.
"""
from app.core.config import get_settings
import httpx
import logging
from datetime import datetime

settings = get_settings()
logger = logging.getLogger(__name__)


class PhoneService:
    def __init__(self):
        self.twilio_account_sid = settings.twilio_account_sid
        self.twilio_auth_token = settings.twilio_auth_token
        self.twilio_api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}"

    async def log_call(
        self,
        to_number: str,
        from_number: str,
        call_sid: str = None,
        duration: int = 0,
        recording_url: str = None,
    ) -> dict:
        """
        Log a call using Twilio API.
        """
        if not self.twilio_account_sid:
            logger.warning("Twilio not configured")
            return {"status": "error", "message": "Twilio not configured"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.twilio_api_url}/Calls.json",
                    data={
                        "To": to_number,
                        "From": from_number,
                        "Url": "http://demo.twilio.com/docs/voice.xml",
                    },
                    auth=(self.twilio_account_sid, self.twilio_auth_token),
                )

                if response.status_code in (200, 201):
                    call_data = response.json()
                    return {
                        "status": "logged",
                        "call_sid": call_data.get("sid"),
                        "to": to_number,
                        "from": from_number,
                    }
                else:
                    return {"status": "error", "message": f"Twilio error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Twilio call logging failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_call_logs(self, from_number: str = None, limit: int = 20) -> list:
        """
        Retrieve call logs from Twilio.
        """
        if not self.twilio_account_sid:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {"PageSize": limit}
                if from_number:
                    params["From"] = from_number

                response = await client.get(
                    f"{self.twilio_api_url}/Calls.json",
                    params=params,
                    auth=(self.twilio_account_sid, self.twilio_auth_token),
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "sid": c.get("sid"),
                            "from": c.get("from"),
                            "to": c.get("to"),
                            "status": c.get("status"),
                            "duration": c.get("duration"),
                            "date_created": c.get("date_created"),
                        }
                        for c in data.get("calls", [])
                    ]
                else:
                    return []
        except Exception as e:
            logger.error(f"Twilio call log retrieval failed: {e}")
            return []

    async def transcribe_call(self, call_sid: str) -> dict:
        """
        Get transcription for a recorded call.
        """
        if not self.twilio_account_sid:
            return {"status": "error", "message": "Twilio not configured"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.twilio_api_url}/Calls/{call_sid}/Transcriptions.json",
                    auth=(self.twilio_account_sid, self.twilio_auth_token),
                )

                if response.status_code == 200:
                    data = response.json()
                    transcriptions = data.get("transcriptions", [])
                    if transcriptions:
                        return {
                            "status": "success",
                            "transcription_text": transcriptions[0].get("transcription_text", ""),
                        }
                    return {"status": "no_transcription"}
                else:
                    return {"status": "error", "message": f"API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Twilio transcription lookup failed: {e}")
            return {"status": "error", "message": str(e)}


async def get_phone_service() -> PhoneService:
    return PhoneService()