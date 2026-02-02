# University of Guelph Library Room Booker

Automatically book study rooms at the University of Guelph Library.

## Features

- **Automatic Booking**: Books rooms based on your preferences for capacity, time, and specific rooms
- **Smart Scheduling**: Runs daily at midnight to grab rooms 2 days in advance (when slots become available)
- **Session Authentication**: Uses your existing Chrome login session - no need to store credentials
- **Configurable Preferences**: Set preferred times, room capacity, and excluded rooms
- **Notifications**: Desktop notifications when booking succeeds or fails
- **Dry Run Mode**: Test the script without actually booking

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

Edit `config.json` to set your preferences:

```json
{
    "room_preferences": {
        "capacity": 1,          // 1 for single rooms, 2 for 2-person rooms
        "preferred_rooms": [],  // e.g., ["315", "316"] or empty for any
        "excluded_rooms": []    // Rooms to never book
    },
    "time_preferences": {
        "preferred_start_times": ["10:00", "11:00", "12:00", "13:00", "14:00"],
        "booking_duration_hours": 2,
        "days_in_advance": 2    // Book 2 days ahead (max allowed)
    }
}
```

### 4. Set Up Chrome Profile (Important!)

The script uses a dedicated automation profile to avoid conflicts with your main Chrome browser.

**First Time Setup:**
- The first time you run the script, it will create a `.chrome_automation_profile` directory
- You'll need to log into the UoG library booking system when prompted
- After that, the session will be saved for future runs

**Optional: Use Custom Profile**
If you want to use a custom Chrome profile path, add it to config.json:
```json
"chrome_profile_path": "/path/to/custom/profile"
```

**Note**: The script can run even when Chrome is open - no need to close your browser!

### 5. Login with Autofill (MacOS Feature!)

The script now helps automate the UoG CAS login process:

**How it works:**
1. **Password Field**: Script clicks the password field to trigger Chrome autofill
   - Just press **Enter** when Chrome shows your saved password
2. **2FA Code**: Script detects the 2FA page and clicks the code field
   - MacOS will show the SMS code suggestion - just click it!
3. **Done**: Login completes automatically

**Benefits:**
- No need to type anything manually
- Uses Chrome's saved passwords
- Uses MacOS SMS autofill for 2FA
- Works great for scheduled midnight bookings

**Note**: After the first successful login, the session is saved in the automation profile, so you won't need to log in again for future bookings!

## Usage

### Run Tests

Verify everything is working correctly:

```bash
python test.py
```

This will check dependencies, configuration, and run test bookings.

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

This will show you the cron command to add. To add it:
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

This keeps the script running and executes at the configured time daily.

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
Check the project folder for `*.png` screenshots taken on errors or during dry runs.

## Logs

- `booking.log` - Detailed booking attempt logs
- `scheduler.log` - Scheduler activity logs

## Disclaimer

This tool is for personal use to automate the manual booking process. Please:
- Follow the library's terms of service
- Don't abuse the booking system
- Cancel bookings you don't need

## License

MIT License - Use at your own risk.
