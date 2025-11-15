# Quick Start Guide

## Installation

### Via HACS:
1. Add custom repository: `https://github.com/EightEFI/Digitraffic-road-conditions`
2. Install "Digitraffic Road Conditions"
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Integrations
5. Create Integration → Search "Digitraffic" → Select road section

### Manual:
1. Copy `custom_components/digitraffic_road/` to your Home Assistant `custom_components/` folder
2. Restart Home Assistant
3. Follow steps 4-5 above

## Configuration

### Searching for Road Sections

The integration features a powerful search system to find exact road sections:

1. When adding the integration, you'll be prompted to **search** for a road section
2. You can search by:
   - **Road number**: E18, E75, VT1, VT4, ST101, ST105, etc.
   - **Location name**: Perämerentie, Hämeentie, Helsinki, Tampere, etc.
   - **Area description**: "Espoo area", "Oulu direction", etc.
   - **Partial matches**: Just type part of the name (case-insensitive)

### Search Examples:
- "**E18**" → All E18 sections
- "**Perämerentie**" → VT4: Perämerentie [50.0-130.0]
- "**Helsinki**" → All sections in Helsinki area
- "**VT4**" → All VT4 sections with KM markers

### Setup Process:
1. Enter search term (e.g., "VT4" or "Perämerentie")
2. View matching sections with road number, KM range, and location
3. Select the specific section you want to monitor
4. Integration creates sensors automatically

## Entities Created

| Entity | Description |
|--------|-------------|
| `sensor.*_current_conditions` | Real-time driving conditions text |
| `sensor.*_forecast` | Time-stamped weather/road forecast |

## Example Automation

Alert when road conditions worsen:

```yaml
automation:
  - alias: Poor Road Conditions Alert
    trigger:
      platform: state
      entity_id: sensor.e18_current_conditions
      to:
        - "Snowing heavily"
        - "Icy"
        - "Wet"
    action:
      service: notify.mobile_app_phone
      data:
        message: "Road conditions alert: {{ trigger.to_state.state }}"
```

## Available Entities in Templates

Current conditions sensor attributes:
- `reliability` - Data reliability percentage (0-100%)
- `last_updated` - Timestamp of last API update

Forecast sensor attributes:
- `forecast_data` - Array of hourly forecasts with time and condition

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| Update Interval | 300s (5 min) | How often to fetch new data |

To change: Edit `const.py` `UPDATE_INTERVAL` value

## Troubleshooting

**Integration won't load:**
- Check internet connectivity
- Verify Digitraffic API is accessible
- Check Home Assistant logs

**No road sections shown:**
- API may be temporarily unavailable
- Try restarting Home Assistant

**Data not updating:**
- Check Home Assistant logs for errors
- Verify internet connection
- Ensure section ID is valid

## Support

- GitHub Issues: https://github.com/EightEFI/Digitraffic-road-conditions/issues
- Full Documentation: See README_INTEGRATION.md
