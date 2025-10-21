"""
Train monitoring service for checking availability and sending notifications.
"""

import aiosqlite
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from get_trains import get_train_availability
from json_parser import extract_train_info

logger = logging.getLogger(__name__)

DB_PATH = Path("train_monitors.db")


async def init_database():
    """Initialize the database schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS monitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                station_from TEXT NOT NULL,
                station_to TEXT NOT NULL,
                travel_date TEXT NOT NULL,
                check_interval INTEGER NOT NULL,
                last_check TIMESTAMP,
                known_trains TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        """)
        await db.commit()
        logger.info("Database initialized")


async def add_monitor(
    user_id: int,
    chat_id: int,
    station_from: str,
    station_to: str,
    travel_date: str,
    check_interval: int
) -> int:
    """
    Add a new monitor to the database.
    Initializes known_trains with current available trains.

    Returns:
        Monitor ID
    """
    import json

    # Get current trains to initialize known_trains
    initial_trains = []
    try:
        data = get_train_availability(station_from, station_to, travel_date)
        if not data.get('hasError'):
            current_trains = extract_train_info(data)
            initial_trains = [t['trainNumber'] for t in current_trains]
            logger.info(f"Initialized monitor with {len(initial_trains)} existing trains")
    except Exception as e:
        logger.warning(f"Could not fetch initial trains for monitor: {e}")
        # Continue with empty list

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO monitors (
                user_id, chat_id, station_from, station_to,
                travel_date, check_interval, known_trains
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, chat_id, station_from, station_to, travel_date, check_interval, json.dumps(initial_trains))
        )
        await db.commit()
        monitor_id = cursor.lastrowid
        logger.info(f"Added monitor {monitor_id} for user {user_id}")
        return monitor_id


async def get_user_monitors(user_id: int) -> List[Dict[str, Any]]:
    """Get all active monitors for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM monitors
            WHERE user_id = ? AND active = 1
            ORDER BY created_at DESC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_all_active_monitors() -> List[Dict[str, Any]]:
    """Get all active monitors."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM monitors WHERE active = 1"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def stop_monitor(monitor_id: int):
    """Deactivate a monitor."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE monitors SET active = 0 WHERE id = ?",
            (monitor_id,)
        )
        await db.commit()
        logger.info(f"Stopped monitor {monitor_id}")


async def stop_all_user_monitors(user_id: int):
    """Deactivate all monitors for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE monitors SET active = 0 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
        logger.info(f"Stopped all monitors for user {user_id}")


async def update_monitor_check(monitor_id: int, known_trains: List[str]):
    """Update last check time and known trains."""
    import json

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE monitors
            SET last_check = CURRENT_TIMESTAMP, known_trains = ?
            WHERE id = ?
            """,
            (json.dumps(known_trains), monitor_id)
        )
        await db.commit()


async def cleanup_expired_monitors():
    """Deactivate monitors for past travel dates."""
    today = datetime.now().strftime("%d.%m.%Y")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE monitors SET active = 0 WHERE travel_date < ? AND active = 1",
            (today,)
        )
        await db.commit()
        if cursor.rowcount > 0:
            logger.info(f"Cleaned up {cursor.rowcount} expired monitors")


async def check_monitor(monitor: Dict[str, Any], bot) -> List[Dict[str, Any]]:
    """
    Check a single monitor for new trains.

    Returns:
        List of new trains that appeared
    """
    import json

    try:
        # Fetch current train data
        data = get_train_availability(
            monitor['station_from'],
            monitor['station_to'],
            monitor['travel_date']
        )

        if data.get('hasError'):
            logger.warning(f"API error for monitor {monitor['id']}")
            return []

        # Extract current trains
        current_trains = extract_train_info(data)
        current_train_numbers = {t['trainNumber'] for t in current_trains}

        # Load known trains
        known_train_numbers = set(json.loads(monitor['known_trains'] or '[]'))

        # Find new trains
        new_train_numbers = current_train_numbers - known_train_numbers
        new_trains = [t for t in current_trains if t['trainNumber'] in new_train_numbers]

        # Update known trains
        await update_monitor_check(monitor['id'], list(current_train_numbers))

        return new_trains

    except Exception as e:
        logger.error(f"Error checking monitor {monitor['id']}: {e}")
        return []


def format_train_summary(train: Dict[str, Any]) -> str:
    """Format a brief train summary for notifications."""
    # Get total seats and price from first car
    total_seats = sum(car['freeSeats'] for car in train['cars'])
    prices = [car['price'] for car in train['cars']]
    price_range = f"{min(prices):,}" if len(set(prices)) == 1 else f"{min(prices):,}-{max(prices):,}"

    return (
        f"Train {train['trainNumber']} ({train['brand']})\n"
        f"Departure: {train['departureTime']}\n"
        f"Arrival: {train['arrivalTime']}\n"
        f"Seats: {total_seats}\n"
        f"Price: from {price_range} so'm"
    )


async def monitor_loop(bot):
    """Background task that checks monitors periodically."""
    logger.info("Starting monitor loop")

    # Group monitors by check interval
    check_groups = {
        1: [],   # 1 minute
        5: [],   # 5 minutes
        10: [],  # 10 minutes
    }

    last_cleanup = datetime.now()

    while True:
        try:
            # Cleanup expired monitors once per hour
            if (datetime.now() - last_cleanup) > timedelta(hours=1):
                await cleanup_expired_monitors()
                last_cleanup = datetime.now()

            # Get all active monitors
            monitors = await get_all_active_monitors()

            # Organize by interval
            for interval in check_groups:
                check_groups[interval] = []

            for monitor in monitors:
                interval = monitor['check_interval']
                if interval in check_groups:
                    check_groups[interval].append(monitor)

            # Check monitors based on their interval
            now = datetime.now()
            for interval, monitors_list in check_groups.items():
                for monitor in monitors_list:
                    # Check if it's time to check this monitor
                    last_check = monitor['last_check']
                    if last_check:
                        last_check_time = datetime.fromisoformat(last_check)
                        if (now - last_check_time).total_seconds() < interval * 60:
                            continue

                    # Check for new trains
                    new_trains = await check_monitor(monitor, bot)

                    # Send notifications
                    for train in new_trains:
                        try:
                            summary = format_train_summary(train)
                            message = f"🔔 New train available!\n\n{summary}"

                            await bot.send_message(
                                chat_id=monitor['chat_id'],
                                text=message
                            )
                            logger.info(f"Sent notification for train {train['trainNumber']} to user {monitor['user_id']}")
                        except Exception as e:
                            logger.error(f"Error sending notification: {e}")

            # Sleep for 30 seconds before next iteration
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(60)
