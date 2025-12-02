# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
