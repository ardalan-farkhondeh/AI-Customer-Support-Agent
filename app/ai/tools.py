
import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# =========================
# Configuration
# =========================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

API_TIMEOUT = float(
    os.getenv("INTERNAL_API_TIMEOUT", "30")
)


# =========================
# Tool Definitions
# =========================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Retrieve the current customer's order using "
                "their tracking number. Use only when order "
                "information is requested."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "Customer order tracking number."
                    }
                },
                "required": ["tracking_number"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": (
                "Retrieve the current Telegram customer's "
                "account information."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]


# =========================
# Internal API Headers
# =========================

def get_internal_headers() -> dict:
    """
    Return authentication headers for internal API requests.
    """

    if not INTERNAL_API_KEY:
        raise RuntimeError(
            "INTERNAL_API_KEY is missing from environment."
        )

    return {
        "x-internal-api-key": INTERNAL_API_KEY,
    }


# =========================
# HTTP Request Helper
# =========================

async def make_api_request(
    method: str,
    endpoint: str,
    *,
    params: dict | None = None,
    json_data: dict | None = None,
) -> dict:
    """
    Execute an authenticated request to the internal API.
    """

    url = f"{API_BASE_URL}{endpoint}"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(API_TIMEOUT)
        ) as client:

            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=get_internal_headers(),
            )

            if response.status_code == 404:
                return {
                    "found": False,
                    "message": "No matching record was found.",
                }

            response.raise_for_status()

            result = response.json()

            if not isinstance(result, dict):
                raise RuntimeError(
                    "Internal API returned an invalid response."
                )

            return result

    except httpx.TimeoutException as exc:
        logger.error(
            "Internal API request timed out: %s",
            endpoint,
        )
        raise RuntimeError(
            "Internal API request timed out."
        ) from exc

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Internal API returned HTTP %s for %s",
            exc.response.status_code,
            endpoint,
        )
        raise RuntimeError(
            "Internal API request failed."
        ) from exc

    except httpx.HTTPError as exc:
        logger.exception(
            "Internal API connection error: %s",
            endpoint,
        )
        raise RuntimeError(
            "Could not connect to the internal API."
        ) from exc

    except ValueError as exc:
        logger.exception(
            "Internal API returned invalid JSON."
        )
        raise RuntimeError(
            "Internal API returned invalid data."
        ) from exc


# =========================
# Order Lookup Tool
# =========================

async def lookup_order_tool(
    telegram_id: int,
    tracking_number: str,
) -> dict:
    """
    Retrieve an order belonging to the current Telegram customer.
    """

    if (
        not isinstance(telegram_id, int)
        or isinstance(telegram_id, bool)
        or telegram_id <= 0
    ):
        raise ValueError("Invalid Telegram ID.")

    if not isinstance(tracking_number, str):
        raise ValueError("Invalid tracking number.")

    tracking_number = tracking_number.strip()

    if not tracking_number or len(tracking_number) > 100:
        raise ValueError("Invalid tracking number.")

    return await make_api_request(
        "POST",
        "/orders/lookup",
        json_data={
            "telegram_id": telegram_id,
            "tracking_number": tracking_number,
        },
    )


# =========================
# Customer Lookup Tool
# =========================

async def lookup_customer_tool(
    telegram_id: int,
) -> dict:
    """
    Retrieve the current Telegram customer's account information.
    """

    if (
        not isinstance(telegram_id, int)
        or isinstance(telegram_id, bool)
        or telegram_id <= 0
    ):
        raise ValueError("Invalid Telegram ID.")

    return await make_api_request(
        "GET",
        "/customers/lookup",
        params={
            "telegram_id": telegram_id,
        },
    )
