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
        output.append(f"\n{'='*30}")
        output.append(f"Train #{i}: {train['trainNumber']} ({train['brand']})")
        output.append(f"{'='*30}")
        output.append(f"Departure: {train['departureTime']} ({train['departureDate']})")
        output.append(f"Arrival: {train['arrivalTime']} ({train['arrivalDate']})")
        output.append(f"Duration: {train['timeInWay']}")
        output.append(f"\nAvailable cars:")

        for car in train['cars']:
            output.append(f"\n  {car['type']}:")
            output.append(f"    Total seats: {car['freeSeats']}")
            output.append(f"    Price: {car['price']:,} so'm")

            # Show seat breakdown
            breakdown = car['seatBreakdown']
            seats_detail = []
            if breakdown['seatsUndef']:
                seats_detail.append(f"Undefined: {breakdown['seatsUndef']}")
            if breakdown['seatsDn']:
                seats_detail.append(f"Lower: {breakdown['seatsDn']}")
            if breakdown['seatsUp']:
                seats_detail.append(f"Upper: {breakdown['seatsUp']}")
            if breakdown['seatsLateralDn']:
                seats_detail.append(f"Lateral lower: {breakdown['seatsLateralDn']}")
            if breakdown['seatsLateralUp']:
                seats_detail.append(f"Lateral upper: {breakdown['seatsLateralUp']}")

            if seats_detail:
                output.append(f"    Breakdown: {', '.join(seats_detail)}")
        
        output.append(f"Route: {train['route']['from']} → {train['route']['to']}")
    
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

