# Development Guide

## Project Overview

This is a Home Assistant custom integration for fetching road condition data from the Finnish Digitraffic API.

## Architecture

### Core Components

1. **`__init__.py`** - Integration lifecycle management
   - `async_setup_entry()` - Called when adding integration
   - `async_unload_entry()` - Called when removing integration
   - `async_reload_entry()` - Called when updating configuration

2. **`config_flow.py`** - User interface for configuration
   - `DigitraficRoadConfigFlow` - Main configuration flow
   - `DigitraficRoadOptionsFlow` - Options/settings flow
   - Handles road section selection

3. **`client.py`** - API communication
   - `DigitraficClient` - Wraps HTTP requests to Digitraffic API
   - Methods: `get_road_sections()`, `get_road_conditions()`, `get_forecast()`
   - Parsing methods: `parse_conditions()`, `parse_forecast()`

4. **`coordinator.py`** - Data management
   - `DigitraficDataCoordinator` - Implements `DataUpdateCoordinator` pattern
   - Handles periodic updates (default: 5 minutes)
   - Manages error handling and retries

5. **`sensor.py`** - Entity definitions
   - `DigitraficCurrentConditionsSensor` - Current conditions entity
   - `DigitraficForecastSensor` - Forecast entity
   - Both inherit from `CoordinatorEntity` and `SensorEntity`

6. **`const.py`** - Constants and configuration
   - Domain, entity types, update intervals
   - Attribute names

7. **`manifest.json`** - Integration metadata
   - Version, requirements, Home Assistant version requirement
   - Links to documentation and issue tracker

## Development Workflow

### Running Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/EightEFI/Digitraffic-road-conditions
   cd Digitraffic-road-conditions
   ```

2. Copy to Home Assistant dev environment:
   ```bash
   cp -r custom_components/digitraffic_road <HA_CONFIG>/custom_components/
   ```

3. Restart Home Assistant

### Testing

The integration follows Home Assistant best practices:

- Async/await patterns throughout
- Error handling with proper logging
- Type hints for IDE support
- Integration validation through manifest.json

### Common Tasks

#### Adding a New Sensor Type

1. Add constant in `const.py`
2. Create sensor class in `sensor.py` inheriting from `CoordinatorEntity` and `SensorEntity`
3. Add to entities list in `async_setup_entry()`
4. Add strings to `strings.json`

#### Modifying API Calls

1. Update `client.py` methods
2. Update `coordinator.py` `_async_update_data()` if needed
3. Update sensors to use new data structure

#### Changing Update Interval

Edit in `const.py`:
```python
UPDATE_INTERVAL = 300  # Change to desired seconds
```

## API Reference

### Digitraffic API Endpoints

- **Road Sections**: `GET /api/v3/road-conditions/road-sections`
  - Returns: GeoJSON with available road sections
  
- **Current Conditions**: `GET /api/v3/road-conditions/road-sections/{sectionId}`
  - Returns: GeoJSON with current conditions
  
- **Forecast**: `GET /api/v3/road-conditions/road-sections/{sectionId}/forecast`
  - Returns: GeoJSON with 12h forecast

### Response Format

All endpoints return GeoJSON with features containing:
- `geometry` - Geographic coordinates
- `properties` - Data (condition, reliability, time, etc.)

## Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Use logging for debug/error messages

## Adding Languages

Add translation files to `strings/`:

1. Create `strings/<language_code>.json`
2. Mirror structure of `strings/en.json`
3. Translate all strings

Example: `strings/fi.json` for Finnish

## Future Enhancements

Potential improvements:

1. **Additional Sensors**
   - Temperature readings
   - Wind speed
   - Visibility

2. **Camera Platform**
   - Traffic camera images
   - Live traffic streams

3. **Binary Sensors**
   - Road closed status
   - Chain requirement status

4. **Custom Services**
   - Manual data refresh
   - Get nearest section

5. **Statistics**
   - Historical condition tracking
   - Statistics service integration

## Debugging Tips

1. Enable debug logging in Home Assistant:
   ```yaml
   logger:
     logs:
       custom_components.digitraffic_road: debug
   ```

2. Check API responses:
   ```bash
   curl https://www.digitraffic.fi/api/v3/road-conditions/road-sections | jq
   ```

3. Use VS Code with Home Assistant extension for development

## Testing Against API

Test current API structure:

```python
import aiohttp
import asyncio

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://www.digitraffic.fi/api/v3/road-conditions/road-sections"
        ) as resp:
            print(await resp.json())

asyncio.run(test())
```

## Performance Considerations

- Update interval set to 5 minutes to respect API rate limits
- Timeout set to 10 seconds for API calls
- Single coordinator per section prevents duplicate API calls
- Error handling prevents crashes on API failures

## Home Assistant Integration Best Practices

✅ Implemented:
- Config flow for easy setup
- Entity naming convention
- Type hints
- Async/await patterns
- Data coordinator pattern
- Error handling and logging
- Unique IDs for entities

## Contributing Guidelines

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## License

See LICENSE file for details.
