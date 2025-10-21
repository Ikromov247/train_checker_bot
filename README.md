# Train Checker Bot

A Telegram bot for checking train availability in Uzbekistan. The bot helps users search for available trains between cities, view seat availability, and check prices.

## Features

- Select departure and destination cities from a list of major Uzbek cities
- Interactive date picker showing the next 14 days
- View all available trains with seat information
- Detailed seat breakdown (upper, lower, lateral seats)
- Price information including tariffs and commission fees
- Multilingual support (Uzbek/Russian city names)

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow the instructions to choose a name and username for your bot
4. BotFather will give you a **bot token** - save this for later
5. (Optional) Send `/setdescription` to add a description for your bot
6. (Optional) Send `/setabouttext` to add an "About" section

### 2. Install Dependencies

Make sure you have Python 3.13 or higher installed.

Install the project dependencies using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   ```

   Replace `your_actual_bot_token_here` with the token you got from BotFather.

### 4. Run the Bot

```bash
python telegram_bot.py
```

You should see a message like:
```
INFO:__main__:Starting bot...
```

### 5. Test the Bot

1. Open Telegram and search for your bot by username
2. Send `/start` command
3. Follow the interactive prompts to search for trains

## Project Structure

```
train_checker_bot/
├── telegram_bot.py      # Main bot application
├── get_trains.py        # API handler for train data
├── json_parser.py       # JSON parser for train information
├── city_data.py         # City mappings and station codes
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment file
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## How to Use the Bot

1. **Start the bot**: Send `/start` command
2. **Select departure city**: Choose from the list of cities
3. **Select destination city**: Choose where you want to go
4. **Select date**: Pick a date from the calendar (next 14 days)
5. **View results**: The bot will show all available trains with:
   - Train number and type (brand)
   - Departure and arrival times
   - Duration
   - Total route (start and end stations)
   - Available car types with seat counts and prices

## Supported Cities

- Toshkent (Tashkent)
- Samarqand (Samarkand)
- Buxoro (Bukhara)
- Xiva (Khiva)
- Urganch (Urgench)
- Nukus
- Navoiy (Navoi)
- Andijon (Andijan)
- Qarshi (Karshi)
- Jizzax (Jizzakh)
- Termiz (Termez)
- Guliston (Gulistan)
- Qo'qon (Kokand)
- Margilon
- Pop
- Namangan

## API Information

The bot uses the official Uzbekistan Railways e-ticket API:
- Base URL: `https://e-ticket.railway.uz`
- Endpoint: `/api/v3/trains/availability/space/between/stations`

## Development

### Adding New Features

The bot is built using:
- **aiogram 3.x**: Modern async Telegram bot framework
- **python-dotenv**: Environment variable management
- **requests**: HTTP library for API calls

### Code Structure

- `TrainSearch`: FSM (Finite State Machine) states for managing conversation flow
- `create_city_keyboard()`: Generates inline keyboard for city selection
- `create_date_keyboard()`: Generates interactive date picker
- Command handlers process user selections and make API calls

## Troubleshooting

### Bot doesn't respond
- Check that `TELEGRAM_BOT_TOKEN` is correctly set in `.env`
- Ensure the bot is running (`python telegram_bot.py`)
- Check console for error messages

### No trains found
- Try different dates (some routes may not have daily service)
- Verify the route exists (not all city pairs have direct trains)
- Check if the departure date is not too far in the future

### API errors
- The API might be temporarily unavailable
- Check your internet connection
- Verify the station codes in `city_data.py` are correct

## License

This project is for educational purposes.

## Contributing

Feel free to submit issues or pull requests to improve the bot!
