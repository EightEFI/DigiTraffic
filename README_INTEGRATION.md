# Digitraffic Road Conditions Integration

A custom Home Assistant integration that fetches real-time road condition data from the Finnish Digitraffic API (https://www.digitraffic.fi/).

## Features

- **Real-time road conditions**: Get current driving conditions for your selected road section
- **12-hour forecast**: View weather and road condition forecasts for the next 12 hours
- **Multiple road sections**: Add multiple instances to monitor different road sections
- **Automatic updates**: Data refreshes every 5 minutes (configurable)
- **Reliability indicator**: Shows data reliability percentage for informed decision making

## Installation

### Via HACS

1. Open HACS in Home Assistant
2. Click on "Custom repositories"
3. Add `https://github.com/EightEFI/Digitraffic-road-conditions` as repository with category "Integration"
4. Click "Install"
5. Restart Home Assistant

### Manual Installation

1. Copy the `digitraffic_road` folder to `custom_components/` in your Home Assistant configuration directory
2. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **Create Integration** and search for "Digitraffic Road Conditions"
3. Select your desired road section from the available options
4. The integration will create two entities:
   - **Current Conditions**: Shows the current road conditions in text format
   - **12h Forecast**: Shows the road condition forecast for the next 12 hours

## Entities

### Sensor: Current Conditions
- **Entity ID**: `sensor.<section_name>_current_conditions`
- **State**: Current road condition text
- **Attributes**:
  - `reliability`: Data reliability percentage (0-100)
  - `last_updated`: Last update timestamp from the API

### Sensor: 12h Forecast
- **Entity ID**: `sensor.<section_name>_12h_forecast`
- **State**: Multi-line forecast text
- **Attributes**:
  - `forecast_data`: Structured forecast data with time and condition for each hour

## Available Road Sections

Road sections are automatically fetched from the Digitraffic API. Available sections include major Finnish highways and roads monitored by the Finnish Traffic Agency.

## Usage Examples

### Automations

```yaml
automation:
  - alias: "Alert on poor road conditions"
    trigger:
      platform: state
      entity_id: sensor.e18_current_conditions
      to:
        - "Snowing heavily"
        - "Icy"
    action:
      service: notify.mobile_app
      data:
        message: "Poor conditions on E18!"
```

### Template Sensors

```yaml
template:
  - sensor:
      - name: "Road Status"
        unique_id: road_status
        state: "{{ state_attr('sensor.e18_current_conditions', 'reliability') }}%"
```

### Dashboard Card

Use the Entities card or a custom template card to display road conditions:

```yaml
type: entities
entities:
  - entity: sensor.e18_current_conditions
  - entity: sensor.e18_12h_forecast
title: Road Conditions
```

## Data Update Interval

By default, road condition data is updated every 5 minutes. To modify this, you can edit the `UPDATE_INTERVAL` constant in `const.py` (value in seconds).

## API Information

This integration uses the Digitraffic API v3:
- Base URL: `https://www.digitraffic.fi/api/v3/road-conditions`
- Documentation: https://digitraffic.fi/en/
- Rate limits: Standard API rate limits apply

## Troubleshooting

### Integration won't load

- Check internet connection
- Verify the Digitraffic API is accessible: https://www.digitraffic.fi/api/v3/road-conditions/road-sections
- Check Home Assistant logs for detailed error messages

### No road sections appearing

- Ensure the Digitraffic API is responding
- Check that you have internet connectivity
- Try restarting Home Assistant

### Data not updating

- Verify the section ID is correct
- Check Home Assistant logs for API errors
- Ensure your Home Assistant instance can reach the Digitraffic API

## Support

For issues, feature requests, or contributions, please visit:
https://github.com/EightEFI/Digitraffic-road-conditions/issues

## License

See the LICENSE file for details.

## Disclaimer

This integration is not affiliated with the Finnish Transport Infrastructure Agency (Väylävirasto). The data is provided as-is from the Digitraffic API.
