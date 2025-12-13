# OVO Energy Australia - Home Assistant Integration

<p align="center">
  <img src="images/icon.png" alt="Logo" width="128" height="128">
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.3.8-green.svg)

A Home Assistant custom integration for monitoring your OVO Energy Australia account energy usage and costs.

## Features

- **Easy setup**: Simply enter your OVO Energy email and password
- **Automatic authentication**: Handles OAuth2 token management automatically behind the scenes
- **Auto-Recovery**: Automatically logs in again if tokens expire using stored credentials
- Track daily, monthly, and yearly solar consumption
- Track daily, monthly, and yearly grid consumption (power pulled from grid)
- Track daily, monthly, and yearly return to grid (power exported back to grid)
- **Smart charge type detection**: Automatically differentiates between:
  - Grid consumption (DEBIT, FREE, PEAK, OFF_PEAK charges)
  - Return to grid (CREDIT charges - solar export)
- Monitor energy charges for all consumption types
- **Hourly data support**: Automatically fetches hourly consumption data for detailed graphing
  - Fetches last 7 days of hourly data during the 6am daily update
  - Hourly data available for solar, grid consumption, and return to grid
  - Perfect for Home Assistant energy dashboard graphs
- Automatic token refresh (no need to re-enter credentials)
- Supports Home Assistant energy dashboard
- **Smart polling**: Updates automatically every day at 6:00 AM (since OVO data is only available for yesterday)
- **Manual refresh**: Service available to manually update data on demand

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/Mattallmighty/ovoenergy-au`
6. Select category "Integration"
7. Click "Add"
8. Search for "OVO Energy Australia" in HACS and install it
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ovoenergy_au` directory to your `<config_dir>/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "OVO Energy Australia"
4. Enter your OVO Energy credentials:
   - **Email Address**: Your OVO Energy account email
   - **Password**: Your OVO Energy account password
5. Click **Submit**

That's it! The integration will:
- Automatically authenticate with OVO Energy
- Fetch your account details
- Set up all sensors
- Automatically refresh tokens in the background

**Security Notes:**
- Your password is transmitted securely using HTTPS
- Your password is stored securely in Home Assistant's configuration entry to enable automatic re-authentication if tokens expire
- Tokens are automatically refreshed, but if they are revoked, the integration will use your stored password to get new ones automatically

## Sensors

The integration provides 21 sensors across multiple time periods:

### Daily Sensors

- **Daily Solar Consumption** - Total solar energy consumed today (kWh)
- **Daily Grid Consumption** - Total energy consumed from the grid today (kWh) - DEBIT, FREE, PEAK, OFF_PEAK
- **Daily Return to Grid** - Total energy exported back to grid today (kWh) - CREDIT
- **Daily Solar Charge** - Total cost for solar usage today (AUD)
- **Daily Grid Charge** - Total cost for grid energy today (AUD)
- **Daily Return to Grid Charge** - Credit/charge for energy returned to grid today (AUD)

### Monthly Sensors

- **Monthly Solar Consumption** - Total solar energy consumed this month (kWh)
- **Monthly Grid Consumption** - Total energy consumed from the grid this month (kWh)
- **Monthly Return to Grid** - Total energy exported back to grid this month (kWh)
- **Monthly Solar Charge** - Total cost for solar usage this month (AUD)
- **Monthly Grid Charge** - Total cost for grid energy this month (AUD)
- **Monthly Return to Grid Charge** - Credit/charge for energy returned to grid this month (AUD)

### Yearly Sensors

- **Yearly Solar Consumption** - Total solar energy consumed this year (kWh)
- **Yearly Grid Consumption** - Total energy consumed from the grid this year (kWh)
- **Yearly Return to Grid** - Total energy exported back to grid this year (kWh)
- **Yearly Solar Charge** - Total cost for solar usage this year (AUD)
- **Yearly Grid Charge** - Total cost for grid energy this year (AUD)
- **Yearly Return to Grid Charge** - Credit/charge for energy returned to grid this year (AUD)

### Hourly Sensors

- **Hourly Solar Consumption** - Total solar energy consumed in the last 7 days (kWh)
  - Includes hourly breakdown in attributes for detailed graphing
  - Each entry contains timestamp, consumption, and charge information
- **Hourly Grid Consumption** - Total energy consumed from the grid in the last 7 days (kWh)
  - Includes hourly breakdown with charge type (DEBIT, FREE, PEAK, OFF_PEAK)
  - Perfect for analyzing peak vs off-peak usage patterns
- **Hourly Return to Grid** - Total energy exported back to grid in the last 7 days (kWh)
  - Includes hourly breakdown for tracking solar export patterns
  - Shows credits earned for each hour

**Note**: Hourly data is automatically fetched during the 2am daily update and covers the last 7 days. The sensor attributes contain all hourly entries which can be used for creating custom graphs in Home Assistant.

## Energy Dashboard Integration

Add your consumption sensors to the Home Assistant Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Under "Electricity grid" → **Grid consumption**:
   - Click "Add Consumption"
   - Select: **Daily Grid Consumption** or **Monthly Grid Consumption**
3. If you have solar panels, you can add solar sensors to the Solar Production section

**Note:** The "Grid Consumption" sensors track energy you consume from OVO Energy.

## Manual Data Refresh

The integration automatically updates data daily at 2:00 AM. However, you can manually refresh the data at any time using the service:

### Using Developer Tools

1. Go to **Developer Tools** -> **Services**
2. Select service: `ovoenergy_au.refresh_data`
3. Click **Call Service**

### Using an Automation

```yaml
automation:
  - alias: "Refresh OVO Energy Data"
    trigger:
      - platform: time
        at: "14:00:00" # Refresh at 2 PM
    action:
      - service: ovoenergy_au.refresh_data
```

### Using a Script

```yaml
script:
  refresh_ovo_data:
    alias: "Refresh OVO Energy Data"
    sequence:
      - service: ovoenergy_au.refresh_data
```

**Note**: OVO Energy data is typically only available for yesterday and earlier. Refreshing multiple times per day will fetch the same data.

## Plan Information & Rates

The integration shows energy charges based on your OVO Energy plan:

- **Free 3 Plan**: If you have the "Free 3" plan (3 hours of free electricity from 11am-2pm daily), periods during these hours will show as $0.00/kWh charges
- **Charge Types**: Each entry includes the charge type (e.g., "FREE", "PEAK", "OFF_PEAK") to help you understand your billing
- **Solar & Export**: Both solar consumption and export are tracked separately with their respective charges/credits

You can view detailed rate information in the sensor attributes by clicking on a sensor in the Home Assistant UI.

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:

1. Ensure your tokens are still valid (they expire after some time)
2. Re-extract tokens from your browser following the steps above
3. Check the Home Assistant logs for detailed error messages

### Connection Errors

If you encounter connection errors:

1. Check your internet connection
2. Verify that OVO Energy's API is accessible from your network
3. Check the Home Assistant logs for detailed error messages

### Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ovoenergy_au: debug
```

## Support

If you encounter any issues or have feature requests, please open an issue on the [GitHub repository](https://github.com/Mattallmighty/ovoenergy-au/issues).

## Disclaimer

This integration is not officially supported by OVO Energy. It uses OVO Energy's APIs which may change at any time, potentially breaking this integration.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Inspired by the [OVO Energy UK integration](https://github.com/timmo001/ovoenergy) by timmo001.
