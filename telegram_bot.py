"""
Telegram bot for checking train availability in Uzbekistan.
"""

import os
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from city_data import CITIES, get_city_name_uz, get_city_name_ru
from get_trains import get_train_availability
from json_parser import extract_train_info, format_train_info_readable
from monitor_service import (
    init_database, add_monitor, get_user_monitors,
    stop_monitor, stop_all_user_monitors, monitor_loop
)


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables!")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# States for the conversation
class TrainSearch(StatesGroup):
    choosing_from = State()
    choosing_to = State()
    choosing_date = State()


class MonitorSetup(StatesGroup):
    choosing_interval = State()


def create_city_keyboard(exclude_code: str = None) -> InlineKeyboardMarkup:
    """Create keyboard with city buttons."""
    buttons = []
    for city in CITIES:
        if exclude_code and city["code"] == exclude_code:
            continue
        # Display in Uzbek
        button = InlineKeyboardButton(
            text=city["uz"],
            callback_data=f"city_{city['code']}"
        )
        buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_date_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with date selection (next 14 days)."""
    buttons = []
    today = datetime.now()

    # Create 2 rows of 7 days each
    for i in range(14):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")

        # Label for button
        if i == 0:
            label = f"Today ({date.strftime('%d.%m')})"
        elif i == 1:
            label = f"Tomorrow ({date.strftime('%d.%m')})"
        else:
            label = date.strftime("%d.%m (%a)")

        button = InlineKeyboardButton(
            text=label,
            callback_data=f"date_{date_str}"
        )
        buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_interval_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for selecting check interval."""
    buttons = [
        [InlineKeyboardButton(text="Every 1 minute", callback_data="interval_1")],
        [InlineKeyboardButton(text="Every 5 minutes", callback_data="interval_5")],
        [InlineKeyboardButton(text="Every 10 minutes", callback_data="interval_10")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 🚆\n\n"
        "I can help you find available trains in Uzbekistan.\n\n"
        "Please select your departure city:",
        reply_markup=create_city_keyboard()
    )
    await state.set_state(TrainSearch.choosing_from)


@dp.callback_query(TrainSearch.choosing_from, F.data.startswith("city_"))
async def process_from_city(callback: CallbackQuery, state: FSMContext):
    """Process departure city selection."""
    city_code = callback.data.split("_")[1]
    await state.update_data(from_city=city_code)

    city_name = get_city_name_uz(city_code)

    await callback.message.edit_text(
        f"Departure: {city_name}\n\n"
        f"Now select your destination city:",
        reply_markup=create_city_keyboard(exclude_code=city_code)
    )
    await state.set_state(TrainSearch.choosing_to)
    await callback.answer()


@dp.callback_query(TrainSearch.choosing_to, F.data.startswith("city_"))
async def process_to_city(callback: CallbackQuery, state: FSMContext):
    """Process destination city selection."""
    city_code = callback.data.split("_")[1]
    await state.update_data(to_city=city_code)

    data = await state.get_data()
    from_city_name = get_city_name_uz(data["from_city"])
    to_city_name = get_city_name_uz(city_code)

    await callback.message.edit_text(
        f"Route: {from_city_name} → {to_city_name}\n\n"
        f"Select travel date:",
        reply_markup=create_date_keyboard()
    )
    await state.set_state(TrainSearch.choosing_date)
    await callback.answer()


@dp.callback_query(TrainSearch.choosing_date, F.data.startswith("date_"))
async def process_date(callback: CallbackQuery, state: FSMContext):
    """Process date selection and fetch train data."""
    date_str = callback.data.split("_")[1]

    # Get stored data
    data = await state.get_data()
    from_city = data["from_city"]
    to_city = data["to_city"]

    from_city_name = get_city_name_uz(from_city)
    to_city_name = get_city_name_uz(to_city)
    from_city_name_ru = get_city_name_ru(from_city)
    to_city_name_ru = get_city_name_ru(to_city)

    # Show loading message
    await callback.message.edit_text(
        f"Searching for trains...\n"
        f"{from_city_name} → {to_city_name}\n"
        f"Date: {date_str}"
    )

    try:
        # Make API request
        response_data = get_train_availability(from_city, to_city, date_str)

        # Check for errors
        if response_data.get("hasError"):
            await callback.message.edit_text(
                "Sorry, there was an error fetching train data. Please try again later."
            )
            await state.clear()
            await callback.answer()
            return

        # Extract train information
        trains = extract_train_info(response_data)

        if not trains:
            await callback.message.edit_text(
                f"❌ No trains with available seats found.\n\n"
                f"Route: {from_city_name_ru.upper()} → {to_city_name_ru.upper()}\n"
                f"Date: {date_str}\n\n"
                f"Try another date or route. Use /start to search again."
            )
        else:
            # Format the response
            formatted_response = format_train_info_readable(trains)

            # Add header with route in caps (from passRoute)
            header = (
                f"🚆 TRAIN SEARCH RESULTS\n"
                f"{'='*30}\n"
                f"Route: {from_city_name_ru.upper()} → {to_city_name_ru.upper()}\n"
                f"Date: {date_str}\n"
                f"Found {len(trains)} train(s) with available seats\n"
                f"{'='*30}\n"
            )

            full_message = header + formatted_response

            # Telegram has a 4096 character limit per message
            if len(full_message) > 4096:
                # Split into multiple messages
                await callback.message.edit_text(header)

                # Send trains in chunks
                for train in trains:
                    train_msg = format_train_info_readable([train])
                    await callback.message.answer(train_msg)
            else:
                await callback.message.edit_text(full_message)

            # Store search data for potential monitoring
            await state.update_data(
                last_search={
                    'from': from_city,
                    'to': to_city,
                    'date': date_str
                }
            )

            # Add monitor and restart buttons
            action_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📡 Monitor this route", callback_data="setup_monitor")],
                    [InlineKeyboardButton(text="🔍 New Search", callback_data="restart")]
                ]
            )
            await callback.message.answer(
                "Use /start to make another search or monitor this route for new trains:",
                reply_markup=action_keyboard
            )

        # Don't clear state here - keep it for monitoring setup

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        await callback.message.edit_text(
            f"An error occurred while searching for trains: {str(e)}\n\n"
            f"Please try again with /start"
        )
        await state.clear()

    await callback.answer()


@dp.callback_query(F.data == "restart")
async def restart_search(callback: CallbackQuery, state: FSMContext):
    """Restart the search process."""
    await state.clear()
    await callback.message.answer(
        "Assalomu alaykum! 🚆\n\n"
        "Please select your departure city:",
        reply_markup=create_city_keyboard()
    )
    await state.set_state(TrainSearch.choosing_from)
    await callback.answer()


# === MONITORING HANDLERS ===

@dp.callback_query(F.data == "setup_monitor")
async def setup_monitor_handler(callback: CallbackQuery, state: FSMContext):
    """Start monitor setup process."""
    data = await state.get_data()
    last_search = data.get('last_search')

    if not last_search:
        await callback.answer("No recent search found. Please search for trains first.", show_alert=True)
        return

    await callback.message.answer(
        "Select how often to check for new trains:",
        reply_markup=create_interval_keyboard()
    )
    await state.set_state(MonitorSetup.choosing_interval)
    await callback.answer()


@dp.callback_query(MonitorSetup.choosing_interval, F.data.startswith("interval_"))
async def process_interval_selection(callback: CallbackQuery, state: FSMContext):
    """Process interval selection and create monitor."""
    interval = int(callback.data.split("_")[1])

    data = await state.get_data()
    last_search = data.get('last_search')

    if not last_search:
        await callback.answer("Search data lost. Please search again.", show_alert=True)
        await state.clear()
        return

    # Create monitor
    try:
        monitor_id = await add_monitor(
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id,
            station_from=last_search['from'],
            station_to=last_search['to'],
            travel_date=last_search['date'],
            check_interval=interval
        )

        from_name = get_city_name_uz(last_search['from'])
        to_name = get_city_name_uz(last_search['to'])

        await callback.message.edit_text(
            f"✅ Monitor created!\n\n"
            f"Route: {from_name} → {to_name}\n"
            f"Date: {last_search['date']}\n"
            f"Check interval: Every {interval} minute(s)\n\n"
            f"You'll be notified when new trains become available.\n"
            f"Use /monitors to manage your active monitors."
        )

        await state.clear()
        await callback.answer("Monitor activated!")

    except Exception as e:
        logger.error(f"Error creating monitor: {e}")
        await callback.message.edit_text("Error creating monitor. Please try again.")
        await callback.answer("Error occurred", show_alert=True)


@dp.message(F.text == "/monitors")
async def list_monitors(message: Message):
    """List all active monitors for the user."""
    monitors = await get_user_monitors(message.from_user.id)

    if not monitors:
        await message.answer(
            "You have no active monitors.\n\n"
            "Search for trains and click 'Monitor this route' to start monitoring."
        )
        return

    response = "📡 Your active monitors:\n\n"

    buttons = []
    for monitor in monitors:
        from_name = get_city_name_uz(monitor['station_from'])
        to_name = get_city_name_uz(monitor['station_to'])

        response += (
            f"🚆 {from_name} → {to_name}\n"
            f"   Date: {monitor['travel_date']}\n"
            f"   Interval: Every {monitor['check_interval']} min\n"
            f"   ID: {monitor['id']}\n\n"
        )

        # Add stop button for each monitor
        buttons.append([
            InlineKeyboardButton(
                text=f"Stop {from_name} → {to_name}",
                callback_data=f"stop_monitor_{monitor['id']}"
            )
        ])

    # Add stop all button
    buttons.append([
        InlineKeyboardButton(text="Stop All Monitors", callback_data="stop_all_monitors")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(response, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("stop_monitor_"))
async def stop_monitor_handler(callback: CallbackQuery):
    """Stop a specific monitor."""
    monitor_id = int(callback.data.split("_")[2])

    await stop_monitor(monitor_id)
    await callback.answer("Monitor stopped", show_alert=True)

    # Refresh the list
    monitors = await get_user_monitors(callback.from_user.id)

    if not monitors:
        await callback.message.edit_text("All monitors stopped.")
        return

    response = "📡 Your active monitors:\n\n"
    buttons = []

    for monitor in monitors:
        from_name = get_city_name_uz(monitor['station_from'])
        to_name = get_city_name_uz(monitor['station_to'])

        response += (
            f"🚆 {from_name} → {to_name}\n"
            f"   Date: {monitor['travel_date']}\n"
            f"   Interval: Every {monitor['check_interval']} min\n"
            f"   ID: {monitor['id']}\n\n"
        )

        buttons.append([
            InlineKeyboardButton(
                text=f"Stop {from_name} → {to_name}",
                callback_data=f"stop_monitor_{monitor['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="Stop All Monitors", callback_data="stop_all_monitors")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(response, reply_markup=keyboard)


@dp.callback_query(F.data == "stop_all_monitors")
async def stop_all_monitors_handler(callback: CallbackQuery):
    """Stop all monitors for the user."""
    await stop_all_user_monitors(callback.from_user.id)
    await callback.message.edit_text("✅ All monitors stopped.")
    await callback.answer("All monitors stopped", show_alert=True)


async def main():
    """Start the bot."""
    logger.info("Starting bot...")

    # Initialize database
    await init_database()

    # Start monitor loop in background
    monitor_task = asyncio.create_task(monitor_loop(bot))

    try:
        await dp.start_polling(bot)
    finally:
        monitor_task.cancel()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
