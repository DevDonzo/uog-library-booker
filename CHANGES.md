# Changes Made - 2026-02-02

## Issues Fixed

### 1. Chrome WebDriver Session Error ✓
**Problem**: Script failed with "Chrome instance exited" error when trying to use Chrome profile
**Root Cause**: Selenium couldn't access the default Chrome profile while Chrome was running
**Solution**:
- Created dedicated `.chrome_automation_profile` directory for Selenium
- Added proper Chrome options to prevent conflicts
- Removed remote debugging port conflicts

### 2. Chrome Profile Conflicts ✓
**Problem**: Script required Chrome to be closed before running
**Root Cause**: Both Chrome and Selenium tried to use the same profile simultaneously
**Solution**: Use isolated automation profile that doesn't conflict with running Chrome

## Code Changes

### library_booker.py
**Line 71-106**: Updated `_setup_driver()` method
- Creates dedicated automation profile in `.chrome_automation_profile/` directory
- Added better Chrome options for stability
- Removed conflicting remote debugging port
- Added `excludeSwitches` to prevent automation detection
- Improved logging for debugging

## New Files

### test.py
- Comprehensive test suite to verify all functionality
- Checks dependencies, configuration, availability, and booking flow
- Provides clear pass/fail results

### .gitignore
- Excludes automation profile directory
- Excludes screenshots and logs
- Excludes sensitive config data

### CHANGES.md
- This file documenting all changes

## Updated Documentation

### README.md
- Updated Chrome profile setup instructions
- Added test.py usage instructions
- Updated troubleshooting section with new fixes
- Clarified that Chrome can remain open while script runs

## Testing Results

All tests passed successfully:
- ✓ Dependencies installed correctly
- ✓ Configuration file valid
- ✓ Room availability check working
- ✓ Dry run booking flow successful

## What Works Now

1. **Chrome Integration**: Script can run with Chrome open
2. **Session Management**: Uses dedicated profile for automation
3. **Error Handling**: Better error messages and logging
4. **Testing**: Comprehensive test suite for verification
5. **Documentation**: Clear setup and troubleshooting guide

## Next Steps for Users

1. Run `python test.py` to verify everything works
2. First run will prompt for UoG login (one-time setup)
3. Subsequent runs will use saved session
4. Configure preferences in `config.json`
5. Set up scheduler for automatic booking

## Technical Details

### Chrome Profile Strategy
- Main Chrome: Uses default profile at `~/Library/Application Support/Google/Chrome`
- Automation: Uses `.chrome_automation_profile/` in project directory
- No conflicts: Each has its own profile data and lock files

### Chrome Options Added
```python
--no-sandbox                    # Improves stability
--disable-dev-shm-usage        # Prevents shared memory issues
--disable-gpu                   # Better compatibility
--window-size=1920,1080        # Consistent viewport
excludeSwitches: enable-automation  # Less detectable
useAutomationExtension: false  # Cleaner automation
```

## Compatibility

- ✓ macOS (tested on Darwin 25.2.0)
- ✓ Python 3.14.0
- ✓ Selenium 4.40.0
- ✓ Chrome 144.x
- ✓ Should work on Windows and Linux (untested)
