import requests
from get_api_token import get_api_token

BASE_URL = "https://e-ticket.railway.uz"


def get_train_availability(station_from, station_to, date):
    """
    Check train availability between two stations.

    Args:
        station_from: Departure station ID
        station_to: Destination station ID
        date: Date in format 'dd.mm.yyyy' (e.g., '31.10.2025')

    Returns:
        dict: JSON response from the API
    """
    url = f"{BASE_URL}/api/v3/trains/availability/space/between/stations"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "uz",
        "Sec-Fetch-Mode": "cors",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://e-ticket.railway.uz",
        "Referer": "https://e-ticket.railway.uz/uz/pages/trains-page",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Safari/605.1.15",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "device-type": "BROWSER",
        "X-XSRF-TOKEN": get_api_token(),
    }

    payload = {
        "direction": [
            {
                "depDate": date,
                "fullday": True,
                "type": "Forward"
            }
        ],
        "stationFrom": str(station_from),
        "stationTo": str(station_to),
        "detailNumPlaces": 1,
        "showWithoutPlaces": 0
    }

    cookies = {
        "XSRF-TOKEN": get_api_token()
    }

    response = requests.post(url, headers=headers, cookies=cookies, json=payload)
    print(f"API Status: {response.status_code}")
    print(f"Response length: {len(response.content)} bytes")

    try:
        raw_data = response.json()

        # The API now wraps the response in an 'express' key
        if 'express' in raw_data:
            data = raw_data['express']
            print(f"Extracted from 'express' wrapper. hasError: {data.get('hasError', False)}")
        else:
            # Fallback for old API format (if they change it back)
            data = raw_data
            print(f"Using direct response. hasError: {data.get('hasError', False)}")

        return data
    except ValueError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response.text[:200]}")
        raise
