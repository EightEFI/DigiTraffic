# Digitraffic Road Conditions - Home Assistant Custom Integration

This is a custom HACS integration for Home Assistant that fetches real-time road condition data from the Finnish Digitraffic service (https://www.digitraffic.fi/tieliikenne/).

## Overview

This integration provides:

- **Current Road Conditions**: Real-time text description of driving conditions on your selected road section
- **12-Hour Forecast**: Predicted road and weather conditions for the next 12 hours
- **Multiple Sections**: Monitor different road sections by adding multiple integration instances
- **Automatic Updates**: Data updates every 5 minutes automatically

## Project Structure

```
Digitraffic-road-conditions/
├── custom_components/
│   └── digitraffic_road/
│       ├── __init__.py                    # Integration setup and lifecycle management
│       ├── manifest.json                  # Integration metadata
│       ├── client.py                      # Digitraffic API client
│       ├── coordinator.py                 # Data coordinator for periodic updates
│       ├── config_flow.py                 # Configuration UI flow
│       ├── const.py                       # Constants and configuration
│       ├── sensor.py                      # Sensor platform entities
│       ├── strings.json                   # English UI strings
│       ├── py.typed                       # Type hints marker
│       └── strings/
│           └── en.json                    # English language strings
├── hacs.json                              # HACS repository metadata
├── README.md                              # Main repository README
├── README_INTEGRATION.md                  # Integration-specific documentation
└── LICENSE                                # License file
```

## Features

### 1. **Configuration Flow**
- User-friendly interface to select road sections
- Automatic fetching of available road sections from Digitraffic API
- Prevents duplicate configurations

### 2. **Entities Created**
- **Sensor: Current Conditions** - Shows text description of current road conditions
- **Sensor: Forecast** - Shows multi-line forecast with time-stamped conditions

### 3. **Attributes**
- Current conditions include reliability percentage and last update time
- Forecast includes structured data for each hour

### 4. **API Integration**
- Uses Digitraffic API v3 endpoint: `https://www.digitraffic.fi/api/v3/road-conditions`
- Handles connection errors gracefully
- Implements proper timeouts and error handling

### 5. **Data Coordinator**
- Centralized data fetching with UpdateCoordinator pattern
- Configurable update interval (default: 5 minutes)
- Automatic retry on failures

## Installation Steps

### Option 1: Via HACS (Recommended)

1. Ensure HACS is installed in your Home Assistant
2. Go to HACS → Integrations → Custom repositories
3. Add URL: `https://github.com/EightEFI/Digitraffic-road-conditions`
4. Category: `Integration`
5. Click "Install"
6. Restart Home Assistant
7. Go to Settings → Devices & Services → Create Integration
8. Search for "Digitraffic Road Conditions"
9. Follow the configuration flow to select your road section

### Option 2: Manual Installation

1. Clone or download this repository
2. Copy `custom_components/digitraffic_road` to your Home Assistant's `custom_components/` folder
3. Restart Home Assistant
4. Proceed with configuration (steps 7-9 above)

## Usage

### Adding the Integration

After installation, add the integration through the Home Assistant UI:

1. Settings → Devices & Services → Integrations
2. Click "Create Integration"
3. Search for and select "Digitraffic Road Conditions"
4. Choose your desired road section from the dropdown
5. Click "Create"

### Accessing the Data

The integration creates two sensors:

- `sensor.<road_section_name>_current_conditions` - Current conditions text
- `sensor.<road_section_name>_forecast` - Forecast text (time-stamped entries)

Use these entities in automations, templates, or dashboard cards:

```yaml
- platform: state
  entity_id: sensor.e18_current_conditions
  to: "Icy"
```

## Technical Details

### API Endpoints Used

- `GET /api/v3/road-conditions/road-sections` - List available road sections
- `GET /api/v3/road-conditions/road-sections/{section_id}` - Get current conditions
- `GET /api/v3/road-conditions/road-sections/{section_id}/forecast` - Get forecast

### Data Processing

The client parses GeoJSON responses from Digitraffic API and extracts:
- Road condition descriptions
- Reliability percentages
- Forecast data with timestamps

### Configuration

Key constants in `const.py`:

- `UPDATE_INTERVAL = 300` - Update interval in seconds (5 minutes)
- `DOMAIN = "digitraffic_road"` - Integration domain

## Debugging

Check Home Assistant logs for detailed information:

```bash
# View logs in Home Assistant UI
Settings → System → Logs
```

Or search for `digitraffic_road` in the logs to filter integration-specific messages.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[See LICENSE file](LICENSE)

## Disclaimer

This integration is not officially affiliated with Digitraffic or the Finnish Transport Infrastructure Agency. Data is provided as-is from the Digitraffic public API.

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository:
https://github.com/EightEFI/Digitraffic-road-conditions/issues
