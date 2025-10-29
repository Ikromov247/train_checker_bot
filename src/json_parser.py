import json
from typing import List, Dict, Any


def extract_train_info(data: dict) -> List[Dict[str, Any]]:
    """
    Extract train information from API response.

    Args:
        data: API response JSON data

    Returns:
        List of dictionaries containing train information

    Raises:
        ValueError: If API returned an error
    """
    # Check if input returned with error
    if data['hasError']:
        raise ValueError("API returned error")

    result = []

    # Get direction (using first/forward direction)
    direction = data['direction'][0]

    # Iterate over available trains
    for train_group in direction['trains']:
        for train_data in train_group['train']:
            # Filter out trains with no available seats
            if not train_data['places']['cars']:
                continue

            # Extract car information
            cars_info = []
            for car in train_data['places']['cars']:
                # Get first tariff (usually there's only one)
                tariff_data = car['tariffs']['tariff'][0] if car['tariffs']['tariff'] else None

                if tariff_data:
                    # Calculate price (tariff + comissionFee)
                    price = int(tariff_data['tariff']) + int(tariff_data['comissionFee'])

                    # Extract seat details
                    seats = tariff_data['seats']
                    seat_breakdown = {
                        'seatsUndef': seats.get('seatsUndef'),
                        'seatsDn': seats.get('seatsDn'),
                        'seatsUp': seats.get('seatsUp'),
                        'seatsLateralDn': seats.get('seatsLateralDn'),
                        'seatsLateralUp': seats.get('seatsLateralUp')
                    }

                    car_info = {
                        'type': car['type'],
                        'freeSeats': int(car['freeSeats']),
                        'seatBreakdown': seat_breakdown,
                        'price': price
                    }
                    cars_info.append(car_info)

            # Extract route information
            route_start = train_data['route']['station'][0]
            route_end = train_data['route']['station'][-1]

            # Build train info dictionary
            train_info = {
                'trainNumber': train_data['number'],
                'brand': train_data['brand'],
                'departureTime': train_data['departure']['localTime'],
                'departureDate': train_data['departure']['localDate'],
                'arrivalTime': train_data['arrival']['localTime'],
                'arrivalDate': train_data['arrival']['localDate'],
                'timeInWay': train_data['timeInWay'],
                'route': {
                    'from': route_start,
                    'to': route_end
                },
                'cars': cars_info
            }

            result.append(train_info)

    return result


def extract_sold_out_trains(data: dict, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Extract sold-out trains (basic info only).

    Args:
        data: API response JSON data
        limit: Maximum number of sold-out trains to return

    Returns:
        List of dictionaries containing basic sold-out train information
    """
    if data['hasError']:
        raise ValueError("API returned error")

    result = []
    direction = data['direction'][0]

    for train_group in direction['trains']:
        for train_data in train_group['train']:
            # Only include trains with NO available seats
            if train_data['places']['cars']:
                continue

            # Extract route information
            route_start = train_data['route']['station'][0]
            route_end = train_data['route']['station'][-1]

            # Build basic train info
            train_info = {
                'trainNumber': train_data['number'],
                'brand': train_data['brand'],
                'departureTime': train_data['departure']['localTime'],
                'arrivalTime': train_data['arrival']['localTime'],
                'timeInWay': train_data['timeInWay'],
                'route': {
                    'from': route_start,
                    'to': route_end
                },
                'soldOut': True
            }

            result.append(train_info)

            if len(result) >= limit:
                break

        if len(result) >= limit:
            break

    return result


def format_train_info_readable(trains: List[Dict[str, Any]]) -> str:
    """
    Format train information into a human-readable string.

    Args:
        trains: List of train information dictionaries

    Returns:
        Formatted string with train details
    """
    if not trains:
        return "No trains with available seats found."

    output = []
    for i, train in enumerate(trains, 1):
        # Header with train number and brand
        output.append(f"\n🚂 Train {train['trainNumber']} • {train['brand']}")
        output.append(f"{'─' * 35}")

        # Time and duration
        output.append(f"🕐 {train['departureTime']} → {train['arrivalTime']} ({train['timeInWay']})")
        output.append(f"📅 {train['departureDate']}")
        output.append(f"🛤️  {train['route']['from']} → {train['route']['to']}")

        # Available cars section
        output.append(f"\n💺 Available seats:")

        for car in train['cars']:
            # Car type header with total seats and price
            output.append(f"\n  ▪️ {car['type']} — {car['freeSeats']} seats")
            output.append(f"     💰 {car['price']:,} so'm")

            # Show seat breakdown in compact form
            breakdown = car['seatBreakdown']
            seats_parts = []

            if breakdown['seatsDn'] and str(breakdown['seatsDn']) != '0':
                seats_parts.append(f"⬇️{breakdown['seatsDn']}")
            if breakdown['seatsUp'] and str(breakdown['seatsUp']) != '0':
                seats_parts.append(f"⬆️{breakdown['seatsUp']}")
            if breakdown['seatsLateralDn'] and str(breakdown['seatsLateralDn']) != '0':
                seats_parts.append(f"🔽{breakdown['seatsLateralDn']}")
            if breakdown['seatsLateralUp'] and str(breakdown['seatsLateralUp']) != '0':
                seats_parts.append(f"🔼{breakdown['seatsLateralUp']}")
            if breakdown['seatsUndef']:
                seats_parts.append(f"📍{breakdown['seatsUndef']}")

            if seats_parts:
                output.append(f"     {' | '.join(seats_parts)}")

    return '\n'.join(output)


def format_sold_out_trains(trains: List[Dict[str, Any]]) -> str:
    """
    Format sold-out train information into a compact string.

    Args:
        trains: List of sold-out train information dictionaries

    Returns:
        Formatted string with basic train details
    """
    if not trains:
        return ""

    output = ["\n\n❌ Sold-out trains (can be monitored):"]
    output.append("─" * 35)

    for train in trains:
        output.append(
            f"\n🚃 {train['trainNumber']} • {train['brand']}\n"
            f"   🕐 {train['departureTime']} → {train['arrivalTime']} ({train['timeInWay']})"
        )

    return '\n'.join(output)


# if __name__ == "__main__":
#     # Test with the ligma.json file
#     with open('ligma.json', 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     trains = extract_train_info(data)

#     # Print as JSON
#     print("JSON Output:")
#     print(json.dumps(trains, indent=2, ensure_ascii=False))

#     # Print readable format
#     print("\n" + format_train_info_readable(trains))

