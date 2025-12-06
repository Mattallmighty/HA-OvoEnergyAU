# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-12-06

### Added
- **Hourly Data Support**: Integration now fetches hourly consumption data for graphing in Home Assistant
  - Fetches hourly data for the last 7 days during the 2am daily update
  - 3 new hourly sensors added:
    - `hourly_solar_consumption` - Total solar consumption with hourly breakdown
    - `hourly_grid_consumption` - Total grid consumption with hourly breakdown
    - `hourly_return_to_grid` - Total return to grid with hourly breakdown
  - Each hourly sensor includes all hourly entries as attributes for detailed graphing
  - Hourly data automatically refreshes daily at 2am
- Added `HOURLY_DATA_DAYS` constant to configure how many days of hourly data to fetch

### Changed
- Coordinator now fetches both interval data (daily/monthly/yearly) and hourly data in a single update
- Total sensor count increased from 18 to 21

### Technical
- Added `_process_hourly_data()` method to coordinator for processing hourly entries
- Hourly data keeps all entries (not just latest) to enable Home Assistant graphing
- Hourly sensors expose consumption totals as state and hourly entries as attributes

## [1.2.1] - 2025-12-06

### Fixed
- **CRITICAL BUG FIX**: Coordinator was summing ALL historical data instead of using latest period
  - Daily sensors now show only the most recent day's data (not sum of all 577 days)
  - Monthly sensors now show only the current month's data (not sum of all 20 months)
  - Yearly sensors now show only the current year's data (not sum of both years)
  - This fixes the issue where all periods showed identical totals (10,749.06 kWh)

### Technical
- Updated `_process_data()` to use only the last entry from API response arrays
- Added documentation explaining API returns arrays of historical data

## [1.2.0] - 2025-12-06

### Added
- **🎉 Username/Password Authentication**: Users can now sign in with email and password instead of manual token entry
  - Auth0 OAuth2 PKCE flow implemented
  - Automatic token management behind the scenes
  - Tokens are automatically refreshed
- **Hourly Data Support**: Added `get_hourly_data()` API method
  - Fetch hourly consumption data for specific date ranges
  - Uses GetHourlyData GraphQL query
  - Foundation for future hourly sensors

### Changed
- **BREAKING**: Config flow now requires username/password instead of manual token entry
- Updated UI strings and translations for new auth flow
- Added necessary Auth0 constants (OAUTH_LOGIN_URL, OAUTH_CONNECTION, OAUTH_REDIRECT_URI)

### Technical
- Added PKCE (Proof Key for Code Exchange) parameter generation
- Implemented full Auth0 authentication flow with callback handling
- Added comprehensive error handling for authentication failures

## [1.1.0] - 2025-12-02

### Added
- **New Feature**: Differentiate between grid consumption and return to grid based on charge type
  - DEBIT, FREE, PEAK, OFF_PEAK charges → Grid Consumption (pulling from grid)
  - CREDIT charges → Return to Grid (solar export back to grid)
- Added 6 new sensors for return to grid tracking:
  - `daily_return_to_grid` / `daily_return_to_grid_charge`
  - `monthly_return_to_grid` / `monthly_return_to_grid_charge`
  - `yearly_return_to_grid` / `yearly_return_to_grid_charge`

### Changed
- Coordinator now separates consumption by charge type for accurate grid vs return tracking
- Total sensors increased from 12 to 18

## [1.0.0] - 2025-12-02

### 🎉 Production Release

First stable production release! The integration is fully tested and ready for use.

### Changed
- **BREAKING**: Renamed all "Export" sensors to "Grid Consumption" for clarity
  - `daily_export_consumption` → `daily_grid_consumption`
  - `monthly_export_consumption` → `monthly_grid_consumption`
  - `yearly_export_consumption` → `yearly_grid_consumption`
  - All charge sensors updated accordingly
- Improved Energy Dashboard compatibility with proper sensor naming

### Added
- Automatic token refresh using refresh_token (users only enter tokens once!)
- Clear documentation for Energy Dashboard integration
- Production-ready status with full testing completed

### Fixed
- Sensor naming now accurately reflects what data represents (grid consumption, not export)
- Icon updates for grid consumption sensors

## [0.3.0] - 2025-12-02 (Internal)

### Added
- Automatic account ID detection via GetContactInfo GraphQL query
- No manual account ID entry required - automatically fetched using user's email from ID token
- Support for multiple accounts (uses first active account)

### Changed
- **BREAKING**: Account ID is now automatically detected, removing the need for manual entry
- Updated polling to occur daily at 2:00 AM (since OVO data is only available for yesterday)
- Added manual refresh service `ovoenergy_au.refresh_data`

### Fixed
- Proper account information retrieval flow matching OVO Energy website behavior

## [0.2.0] - 2025-12-02 (Internal)

### Added
- Daily polling at 2:00 AM instead of every 30 minutes
- Manual refresh service for on-demand data updates
- Service documentation

### Changed
- Optimized update schedule for yesterday's data availability

## [0.1.0] - 2025-12-02 (Initial)

### Added
- Initial release
- OAuth2 authentication with Auth0
- Manual token entry support
- 12 sensor entities:
  - Daily solar/export consumption and charges
  - Monthly solar/export consumption and charges
  - Yearly solar/export consumption and charges
- Home Assistant Energy Dashboard integration
- Automatic token refresh
- HACS compatibility
