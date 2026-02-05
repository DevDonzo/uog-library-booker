# University of Guelph Library Room Booker

Automatically book study rooms at the University of Guelph Library.

## Features

- **Automatic Booking**: Books rooms based on your preferences for capacity, time, and specific rooms
- **Smart Scheduling**: Runs daily at midnight to grab rooms 2 days in advance (when slots become available)
- **Session Authentication**: Handles Microsoft OAuth + 2FA automatically
- **Configurable Preferences**: Set preferred times, room capacity, and excluded rooms
- **Notifications**: Desktop notifications when booking succeeds or fails
- **Dry Run Mode**: Test the script without actually booking

## Project Structure

```
uog-library-booker/
├── src/                    # Main source code
│   ├── __init__.py
│   ├── auth.py            # Authentication handling (Microsoft/UoG CAS)
│   ├── booker.py          # Main booking logic
│   ├── config.py          # Configuration management
│   ├── scheduler.py       # Scheduling functionality
│   └── utils.py           # Utility functions
├── scripts/               # Shell scripts for convenience
│   ├── run.sh
│   └── run.bat
├── logs/                  # Log files (git-ignored)
├── screenshots/           # Screenshots (git-ignored)
├── library_booker.py      # Main entry point
├── scheduler.py           # Scheduler entry point
├── test.py               # Test suite
├── config.json           # Your configuration (git-ignored)
├── config.example.json   # Example configuration
├── .env                  # Credentials (git-ignored)
├── .env.example          # Example credentials file
└── requirements.txt      # Python dependencies
```

## Installation

### 1. Install Python Dependencies

```bash
cd uog-library-booker
pip install -r requirements.txt
```

### 2. Install ChromeDriver

The script uses Selenium with Chrome. Make sure you have:
- Google Chrome installed
- ChromeDriver (will be auto-downloaded by webdriver-manager if not present)

### 3. Configure Your Preferences

Copy `config.example.json` to `config.json` and edit:

```json
{
    "room_preferences": {
        "capacity": 1,
        "preferred_rooms": [],
        "excluded_rooms": []
    },
    "time_preferences": {
        "preferred_start_times": ["11:00", "11:30", "12:00", "12:30", "13:00"],
        "booking_duration_hours": 4,
        "days_in_advance": 2
    }
}
```

### 4. Set Up Credentials (Optional)

Copy `.env.example` to `.env` and add your credentials:

```
UOG_EMAIL=youremail@uoguelph.ca
UOG_PASSWORD=  # Optional - leave empty to use autofill
```

### 5. Chrome Profile Setup

The script uses a dedicated automation profile (`.chrome_automation_profile/`) to avoid conflicts with your main Chrome browser.

**First Time Setup:**
- The first time you run the script, you'll need to log in
- After that, the session will be saved for future runs

## Usage

### Run Tests

Verify everything is working correctly:

```bash
python test.py
```

### Check Room Availability

```bash
python library_booker.py --check
```

### Test Booking (Dry Run)

```bash
python library_booker.py --dry-run
```

### Book a Room

```bash
python library_booker.py
```

### Set Up Daily Scheduling

#### macOS/Linux (Cron)

```bash
python scheduler.py --setup
```

This will show you the cron command to add:
```bash
crontab -e
# Add the line shown by the setup command
```

#### Windows (Task Scheduler)

```bash
python scheduler.py --setup
```

Follow the PowerShell instructions shown.

#### Run as Background Daemon

```bash
python scheduler.py --daemon
```

## Configuration Options

### config.json Reference

| Setting | Description | Default |
|---------|-------------|---------|
| `booking_url` | LibCal booking page URL | UoG Study Rooms |
| `chrome_profile_path` | Path to Chrome profile | Auto-detect |
| `room_preferences.capacity` | Preferred room capacity (1 or 2) | 1 |
| `room_preferences.preferred_rooms` | List of room numbers to prefer | [] (any) |
| `room_preferences.excluded_rooms` | Rooms to never book | [] |
| `time_preferences.preferred_start_times` | Preferred start times (24h format) | 10:00-14:00 |
| `time_preferences.booking_duration_hours` | How long to book (max 4) | 2 |
| `time_preferences.days_in_advance` | Days ahead to book (max 2) | 2 |
| `schedule.enabled` | Enable scheduled runs | true |
| `schedule.run_time` | Time to run daily (HH:MM) | 00:05 |
| `schedule.retry_on_failure` | Retry if booking fails | true |
| `schedule.max_retries` | Max retry attempts | 3 |
| `notifications.enabled` | Enable notifications | true |
| `notifications.desktop_notification` | Show desktop alerts | true |
| `advanced.headless_mode` | Run browser invisibly | false |
| `advanced.login_timeout` | Max seconds to wait for login | 180 |
| `advanced.use_chrome_profile` | Use dedicated Chrome profile | true |
| `advanced.screenshot_on_error` | Save screenshots on errors | true |

## Booking Rules (UoG Library)

- **Advance Booking**: Maximum 2 days in advance
- **Duration**: Maximum 4 hours per day
- **Concurrent Bookings**: Only 1 room at a time
- **Increments**: 30-minute slots

## Troubleshooting

### "Chrome instance exited" or "Session not created"
- This is automatically fixed by using the dedicated automation profile
- If you still see this, make sure you don't have another Selenium session running
- Try deleting `.chrome_automation_profile` and running again

### "User needs to authenticate"
- The first time you run the script, you'll need to log in manually
- The script will wait for you to complete the login
- After that, your session is saved in the automation profile

### "No available rooms matching preferences"
- Check if rooms are actually available on the website
- Widen your time preferences
- Try removing specific room preferences

### Script times out
- The library website might be slow - increase `wait_timeout` in config
- Check your internet connection

### Screenshots
Check the `screenshots/` folder for debugging screenshots.

## Logs

- `logs/booking.log` - Detailed booking attempt logs
- `logs/scheduler.log` - Scheduler activity logs

## Disclaimer

This tool is for personal use to automate the manual booking process. Please:
- Follow the library's terms of service
- Don't abuse the booking system
- Cancel bookings you don't need

## License

MIT License - Use at your own risk.
