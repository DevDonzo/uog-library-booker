# Login Automation Guide

## How the Autofill-Assisted Login Works

The script now intelligently assists with the UoG CAS login process, making it nearly automatic!

## Login Flow

### Step 1: Password Autofill
```
Script detects CAS login page
    ↓
Script clicks password field
    ↓
Chrome shows autofill suggestion
    ↓
YOU: Press ENTER to accept
    ↓
Password submitted!
```

**What you see:**
```
======================================================================
  CAS LOGIN - AUTOFILL ASSISTANCE
======================================================================
  The script will help automate the login steps:
  1. Click on password field to trigger autofill
  2. Wait for you to press Enter on password
  3. Automatically select 'Text' for SMS verification
  4. Detect 2FA page and wait for autofill
  5. You just need to click the macOS 2FA suggestion!
======================================================================

  → Password field is ready. Press ENTER when autofill appears!
```

### Step 2: Select Verification Method
```
Password accepted
    ↓
"Verify your identity" screen appears
    ↓
Script automatically clicks "Text" option
    ↓
(Not "Call")
```

**What you see:**
```
  ✓ Password accepted!
  → Selecting 'Text' for SMS verification...
  ✓ Selected 'Text' method
```

### Step 3: 2FA Code Autofill (MacOS Feature)
```
SMS being sent
    ↓
Script detects 2FA code page
    ↓
Script clicks 2FA code field
    ↓
MacOS detects incoming SMS
    ↓
MacOS shows code suggestion popup
    ↓
YOU: Click the code suggestion
    ↓
Code auto-filled and submitted!
    ↓
Login complete! 🎉
```

**What you see:**
```
  ✓ Password accepted! Now on 2FA page
  → Look for the macOS autofill suggestion for the SMS code
  → Click on the code suggestion when it appears!
```

### Step 3: Session Saved
After successful login, the session is saved in `.chrome_automation_profile/`, so future bookings won't require login!

## MacOS SMS Autofill

For the 2FA step to work smoothly, make sure:

1. **iPhone Text Message Forwarding** is enabled:
   - On iPhone: Settings → Messages → Text Message Forwarding
   - Enable your MacBook

2. **Same Apple ID** on both devices

3. **Bluetooth** enabled on both devices

When a verification code arrives via SMS, macOS will automatically suggest it when you click on a code input field!

## Configuration

You can adjust the login timeout in `config.json`:

```json
{
  "advanced": {
    "login_timeout": 180  // 3 minutes - adjust if you need more time
  }
}
```

## First Time vs. Subsequent Runs

### First Time
- You'll need to complete the login process once
- Script assists with autofill
- Session is saved after successful login

### Subsequent Times
- Session is already saved
- **No login required!**
- Script proceeds directly to booking

## Scheduled Runs (Midnight Booking)

When running at midnight via scheduler:
- If session is still valid → Automatic booking!
- If session expired → Script will attempt booking without login, fail gracefully, and retry
- You may need to run manually once to refresh the session

## Tips for Smooth Login

1. **Save Your Password in Chrome**: Make sure your UoG credentials are saved in the automation profile
   - First time: Let Chrome save the password when prompted

2. **Keep MacOS SMS Features Enabled**: Ensure text message forwarding works

3. **Stay Near Your MacBook**: During first login, you'll need to click the autofill suggestions

4. **Test It**: Run a dry-run booking to test the login flow:
   ```bash
   python3 library_booker.py --dry-run
   ```

## Troubleshooting Login

### "Password field not found"
- The CAS page might have changed
- Check if you're on the correct login page
- Try logging in manually once

### "Login timeout"
- Increase `login_timeout` in config.json
- Make sure you're clicking the autofill suggestions promptly

### "2FA code not autofilling"
- Check iPhone text message forwarding settings
- Make sure both devices are on same Apple ID
- Try clicking the code field again to trigger the suggestion

### Session Expired
If you get logged out:
```bash
# Run once manually to re-authenticate
python3 library_booker.py --check
```

This will prompt for login and save the new session.

## Security Note

The script uses a dedicated Chrome profile (`.chrome_automation_profile/`) which stores:
- Cookies and session data
- Saved passwords (if you let Chrome save them)

This profile is separate from your main Chrome profile, so your regular browsing data stays private.

**Keep this directory secure** as it contains your authenticated session!

Add to `.gitignore` (already done):
```
.chrome_automation_profile/
```
