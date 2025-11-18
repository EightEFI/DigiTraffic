"""Sensor platform for DigiTraffic."""
import json
import logging
import os
import re
from typing import Any, Dict

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_MONITOR_TYPE,
    CONF_ROAD_SECTION,
    CONF_ROAD_SECTION_ID,
    CONF_TMS_ID,
    CONF_WEATHER_STATION_ID,
    MONITOR_CONDITIONS,
    MONITOR_TMS,
    MONITOR_WEATHER,
    SENSOR_TYPE_CONDITIONS,
    SENSOR_TYPE_FORECAST,
)
from .coordinator import DigitraficDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Cache for loaded translations
_TRANSLATION_CACHE: Dict[str, Dict[str, Any]] = {}

# Weather station measurements that are enabled by default
# All other measurements will be created but disabled
WEATHER_ENABLED_BY_DEFAULT = {
    "ILMA",
    "ILMANPAINE",
    "ILMAN_KOSTEUS",
    "JÄÄN_MÄÄRÄ1",
    "JÄÄTYMISPISTE_1",
    "KASTEPISTE",
    "MAA_1",
    "SADE_INTENSITEETTI",
    "VALLITSEVA_SÄÄ",
    "KESKITUULI",
    "TUULENSUUNTA",
}

# WMO weather code translations (WMO Code Table 4677)
# Source: https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
WMO_WEATHER_CODES_FI = {
    0: "Ei merkittävää säätä",
    1: "Pilvisyys vähentynyt",
    2: "Pilvipeite muuttumaton",
    3: "Pilvisyys lisääntynyt",
    4: "Näkyvyys heikentynyt savun tai tulivuorentuhkan takia",
    5: "Utua",
    6: "Leijailevaa pölyä ilmassa",
    7: "Pölyä tai hiekkaa pyörteissä",
    8: "Hyvin kehittyneitä pöly- tai hiekkapyörteitä",
    9: "Pölymyrsky tai hiekkamyrsky",
    10: "Kostea sumu",
    11: "Ohutta sumua tai utua laikkuina",
    12: "Yhtenäistä ohutta sumua tai utua",
    13: "Salamoita näkyvissä, ukkosta ei kuulu",
    14: "Sadetta ei saavu maahan",
    15: "Sadetta saapuu maahan kaukana",
    16: "Sadetta saapuu maahan lähellä",
    17: "Ukkosta mutta ei sadetta",
    18: "Rajuja puuskia",
    19: "Pyörremyrsky",
    20: "Tihkusadetta tai lumijyväsiä",
    21: "Vesisadetta",
    22: "Lumisadetta",
    23: "Räntäsadetta",
    24: "Jäätävää tihkua tai jäätävää vesisadetta",
    25: "Kuurosadetta",
    26: "Lumikuuroja tai räntäkuuroja",
    27: "Raekuuroja",
    28: "Sumua tai jääsumua",
    29: "Ukkosta",
    30: "Lievä tai kohtalainen pölymyrsky, vähentynyt",
    31: "Lievä tai kohtalainen pölymyrsky, muuttumaton",
    32: "Lievä tai kohtalainen pölymyrsky, voimistunut",
    33: "Voimakas pölymyrsky, vähentynyt",
    34: "Voimakas pölymyrsky, muuttumaton",
    35: "Voimakas pölymyrsky, voimistunut",
    36: "Lievä tai kohtalainen tuiskuava lumi",
    37: "Voimakas tuiskuava lumi",
    38: "Lievä tai kohtalainen tuiskuava lumi, vähentynyt",
    39: "Voimakas tuiskuava lumi, vähentynyt",
    40: "Sumua kaukana",
    41: "Sumua laikkuina",
    42: "Sumua, taivas näkyvissä, ohentunut",
    43: "Sumua, taivas ei näkyvissä, ohentunut",
    44: "Sumua, taivas näkyvissä, muuttumaton",
    45: "Sumua, taivas ei näkyvissä, muuttumaton",
    46: "Sumua, taivas näkyvissä, muodostunut",
    47: "Sumua, taivas ei näkyvissä, muodostunut",
    48: "Sumua, kuuraavaa, taivas näkyvissä",
    49: "Sumua, kuuraavaa, taivas ei näkyvissä",
    50: "Ajoittaista tihkua, heikko",
    51: "Jatkuvaa tihkua, heikko",
    52: "Ajoittaista tihkua, kohtalainen",
    53: "Jatkuvaa tihkua, kohtalainen",
    54: "Ajoittaista tihkua, voimakas",
    55: "Jatkuvaa tihkua, voimakas",
    56: "Heikko jäätävä tihku",
    57: "Kohtalainen tai voimakas jäätävä tihku",
    58: "Heikko tihku ja vesi",
    59: "Kohtalainen tai voimakas tihku ja vesi",
    60: "Ajoittaista vesisadetta, heikko",
    61: "Jatkuvaa vesisadetta, heikko",
    62: "Ajoittaista vesisadetta, kohtalainen",
    63: "Jatkuvaa vesisadetta, kohtalainen",
    64: "Ajoittaista vesisadetta, voimakas",
    65: "Jatkuvaa vesisadetta, voimakas",
    66: "Heikko jäätävä vesisade",
    67: "Kohtalainen tai voimakas jäätävä vesisade",
    68: "Heikko räntäsade",
    69: "Kohtalainen tai voimakas räntäsade",
    70: "Ajoittaista lumisadetta, heikko",
    71: "Jatkuvaa lumisadetta, heikko",
    72: "Ajoittaista lumisadetta, kohtalainen",
    73: "Jatkuvaa lumisadetta, kohtalainen",
    74: "Ajoittaista lumisadetta, voimakas",
    75: "Jatkuvaa lumisadetta, voimakas",
    76: "Jääkiteitä (pilareita, neulosia)",
    77: "Lumijyväsiä",
    78: "Yksittäisiä tähdenmuotoisia lumikiteitä",
    79: "Jääjyväsiä",
    80: "Heikko vesikuuro",
    81: "Kohtalainen tai voimakas vesikuuro",
    82: "Erittäin voimakas vesikuuro",
    83: "Heikko räntäkuuro",
    84: "Kohtalainen tai voimakas räntäkuuro",
    85: "Heikko lumikuuro",
    86: "Kohtalainen tai voimakas lumikuuro",
    87: "Heikko lumirakeita tai räntää",
    88: "Kohtalainen tai voimakas lumirakeita tai räntää",
    89: "Heikko raekuuro",
    90: "Kohtalainen tai voimakas raekuuro",
    91: "Heikko vesisade, ukkonen viimeisen tunnin aikana",
    92: "Kohtalainen tai voimakas vesisade, ukkonen",
    93: "Heikko lumi- tai räntäsade, ukkonen",
    94: "Kohtalainen tai voimakas lumi- tai räntäsade, ukkonen",
    95: "Heikko tai kohtalainen ukkonen, vesi- tai lumisade",
    96: "Heikko tai kohtalainen ukkonen, raesade",
    97: "Voimakas ukkonen, vesi- tai lumisade",
    98: "Voimakas ukkonen, pölymyrsky",
    99: "Voimakas ukkonen, raesade",
}

WMO_WEATHER_CODES_EN = {
    0: "No significant weather",
    1: "Clouds dissolving",
    2: "State of sky unchanged",
    3: "Clouds developing",
    4: "Visibility reduced by smoke or volcanic ash",
    5: "Haze",
    6: "Widespread dust in suspension",
    7: "Dust or sand raised by wind",
    8: "Well developed dust or sand whirls",
    9: "Duststorm or sandstorm",
    10: "Mist",
    11: "Patches of shallow fog",
    12: "Continuous shallow fog",
    13: "Lightning visible, no thunder heard",
    14: "Precipitation not reaching ground",
    15: "Precipitation reaching ground, distant",
    16: "Precipitation reaching ground, near",
    17: "Thunderstorm but no precipitation",
    18: "Squalls",
    19: "Funnel cloud",
    20: "Drizzle or snow grains",
    21: "Rain",
    22: "Snow",
    23: "Rain and snow",
    24: "Freezing drizzle or freezing rain",
    25: "Shower of rain",
    26: "Shower of snow or rain and snow",
    27: "Shower of hail",
    28: "Fog or ice fog",
    29: "Thunderstorm",
    30: "Slight or moderate duststorm, decreased",
    31: "Slight or moderate duststorm, no change",
    32: "Slight or moderate duststorm, increased",
    33: "Severe duststorm, decreased",
    34: "Severe duststorm, no change",
    35: "Severe duststorm, increased",
    36: "Slight or moderate drifting snow, below eye level",
    37: "Heavy drifting snow, below eye level",
    38: "Slight or moderate drifting snow, above eye level",
    39: "Heavy drifting snow, above eye level",
    40: "Fog at a distance",
    41: "Fog in patches",
    42: "Fog, sky visible, thinning",
    43: "Fog, sky invisible, thinning",
    44: "Fog, sky visible, no change",
    45: "Fog, sky invisible, no change",
    46: "Fog, sky visible, begun or thickened",
    47: "Fog, sky invisible, begun or thickened",
    48: "Fog, depositing rime, sky visible",
    49: "Fog, depositing rime, sky invisible",
    50: "Drizzle, intermittent, slight",
    51: "Drizzle, continuous, slight",
    52: "Drizzle, intermittent, moderate",
    53: "Drizzle, continuous, moderate",
    54: "Drizzle, intermittent, heavy",
    55: "Drizzle, continuous, heavy",
    56: "Drizzle, freezing, slight",
    57: "Drizzle, freezing, moderate or heavy",
    58: "Drizzle and rain, slight",
    59: "Drizzle and rain, moderate or heavy",
    60: "Rain, intermittent, slight",
    61: "Rain, continuous, slight",
    62: "Rain, intermittent, moderate",
    63: "Rain, continuous, moderate",
    64: "Rain, intermittent, heavy",
    65: "Rain, continuous, heavy",
    66: "Rain, freezing, slight",
    67: "Rain, freezing, moderate or heavy",
    68: "Rain and snow, slight",
    69: "Rain and snow, moderate or heavy",
    70: "Snow, intermittent, slight",
    71: "Snow, continuous, slight",
    72: "Snow, intermittent, moderate",
    73: "Snow, continuous, moderate",
    74: "Snow, intermittent, heavy",
    75: "Snow, continuous, heavy",
    76: "Ice crystals (diamond dust)",
    77: "Snow grains",
    78: "Isolated star-like snow crystals",
    79: "Ice pellets",
    80: "Rain shower, slight",
    81: "Rain shower, moderate or heavy",
    82: "Rain shower, violent",
    83: "Shower of rain and snow, slight",
    84: "Shower of rain and snow, moderate or heavy",
    85: "Snow shower, slight",
    86: "Snow shower, moderate or heavy",
    87: "Shower of snow pellets or small hail, slight",
    88: "Shower of snow pellets or small hail, moderate or heavy",
    89: "Shower of hail, slight",
    90: "Shower of hail, moderate or heavy",
    91: "Slight rain, thunderstorm during past hour",
    92: "Moderate or heavy rain, thunderstorm",
    93: "Slight snow or rain and snow, thunderstorm",
    94: "Moderate or heavy snow or rain and snow, thunderstorm",
    95: "Slight or moderate thunderstorm with rain or snow",
    96: "Slight or moderate thunderstorm with hail",
    97: "Heavy thunderstorm with rain or snow",
    98: "Thunderstorm with duststorm",
    99: "Heavy thunderstorm with hail",
}


def _load_translations(language: str = "fi") -> Dict[str, Any]:
    """Load translations from JSON file."""
    if language in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[language]
    
    try:
        translation_file = os.path.join(
            os.path.dirname(__file__),
            "translations",
            f"{language}.json"
        )
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _TRANSLATION_CACHE[language] = translations
            return translations
    except Exception as e:
        _LOGGER.warning("Failed to load translations for %s: %s", language, e)
        return {}


def _get_datapoint_translation(key: str, language: str = "fi") -> str:
    """Get translated name for a datapoint from translation files."""
    translations = _load_translations(language)
    datapoints = translations.get("sensor", {}).get("datapoints", {})
    return datapoints.get(key, key)


def translate_wmo_code(code: int | float | str, language: str = "fi") -> str:
    """Translate WMO weather code to human-readable description."""
    try:
        code_int = int(float(code))
        if language == "en":
            return WMO_WEATHER_CODES_EN.get(code_int, f"Unknown weather code: {code_int}")
        return WMO_WEATHER_CODES_FI.get(code_int, f"Tuntematon sääkoodi: {code_int}")
    except (ValueError, TypeError):
        return str(code)


WEATHER_SENSOR_NAME_EN = {
    "ILMA": "Air temperature",
    "ILMA_DERIVAATTA": "Air temperature trend",
    "TIE_1": "Road temperature lane 1",
    "TIE_1_DERIVAATTA": "Road temperature trend lane 1",
    "MAA_1": "Ground temperature sensor 1",
    "KASTEPISTE": "Dew point",
    "J\u00c4\u00c4TYMISPISTE_1": "Freezing point sensor 1",
    "KESKITUULI": "Average wind speed",
    "MAKSIMITUULI": "Maximum wind speed",
    "TUULENSUUNTA": "Wind direction",
    "ILMAN_KOSTEUS": "Relative humidity",
    "SADE": "Weather description",
    "SADE_INTENSITEETTI": "Precipitation intensity",
    "SADESUMMA": "Precipitation sum",
    "SATEEN_OLOMUOTO_PWDXX": "Precipitation form",
    "N\u00c4KYVYYS_KM": "Visibility",
    "KELI_1": "Road condition lane 1",
    "VAROITUS_1": "Warning 1",
    "JOHTAVUUS_1": "Conductivity sensor 1",
}

WEATHER_SENSOR_DEFINITIONS = {
    "ILMA": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "ILMA_DERIVAATTA": {
        "icon": "mdi:thermometer-lines",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "TIE_1": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:road-variant",
    },
    "TIE_1_DERIVAATTA": {
        "icon": "mdi:thermometer-lines",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "MAA_1": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "KASTEPISTE": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-percent",
    },
    "J\u00c4\u00c4TYMISPISTE_1": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "KESKITUULI": {
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:weather-windy",
    },
    "MAKSIMITUULI": {
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:weather-windy",
    },
    "TUULENSUUNTA": {
        "device_class": SensorDeviceClass.WIND_DIRECTION,
        "icon": "mdi:compass",
    },
    "ILMAN_KOSTEUS": {
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-percent",
    },
    "SADE": {
        "use_description": True,
        "icon": "mdi:weather-pouring",
    },
    "SADE_INTENSITEETTI": {
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:weather-pouring",
    },
    "SADESUMMA": {
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water",
    },
    "SATEEN_OLOMUOTO_PWDXX": {
        "use_description": True,
        "icon": "mdi:weather-snowy-rainy",
    },
    "N\u00c4KYVYYS_KM": {
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:binoculars",
    },
    "KELI_1": {
        "use_description": True,
        "icon": "mdi:road",
    },
    "VAROITUS_1": {
        "use_description": True,
        "icon": "mdi:alert-outline",
    },
    "JOHTAVUUS_1": {
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
}


def _humanize_weather_key(key: str) -> str:
    text = key.replace("_", " ")
    humanized = text.title()
    humanized = humanized.replace("Pwdxx", "PWDXX")
    humanized = humanized.replace("Km", "km")
    return humanized


def format_weather_measurement_name(key: str, language: str) -> str:
    """Return a localized display name for a weather measurement key."""
    # Try to get translation from JSON files first
    translated = _get_datapoint_translation(key, language)
    if translated != key:
        return translated
    
    # Fallback to old behavior for backwards compatibility
    if language == "en":
        return WEATHER_SENSOR_NAME_EN.get(key, _humanize_weather_key(key))
    return _humanize_weather_key(key)


def slugify_measurement_key(key: str) -> str:
    """Return a safe unique-id suffix derived from the measurement key."""
    normalized = key.lower()
    normalized = (
        normalized.replace("ä", "a")
        .replace("ö", "o")
        .replace("å", "a")
        .replace(" ", "_")
    )
    return re.sub(r"[^a-z0-9_]+", "_", normalized)


def should_skip_weather_key(key: str) -> bool:
    """Determine if a weather key should be skipped (duplicates, unused channels)."""
    return str(key).upper().endswith("_2")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: DigitraficDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    data = config_entry.data

    monitor_type = data.get(CONF_MONITOR_TYPE)
    tms_id = data.get(CONF_TMS_ID)
    weather_station_id = data.get(CONF_WEATHER_STATION_ID)

    if monitor_type is None:
        if tms_id:
            monitor_type = MONITOR_TMS
        elif weather_station_id:
            monitor_type = MONITOR_WEATHER
        else:
            monitor_type = MONITOR_CONDITIONS

    if monitor_type == MONITOR_TMS and tms_id:
        section_name = data.get(CONF_ROAD_SECTION) or str(tms_id)

        lam_measurement_keys = [
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1",
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2",
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1_VVAPAAS1",
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2_VVAPAAS2",
            "KESKINOPEUS_60MIN_KIINTEA_SUUNTA1",
            "KESKINOPEUS_60MIN_KIINTEA_SUUNTA2",
            "KESKINOPEUS_5MIN_KIINTEA_SUUNTA1_VVAPAAS1",
            "KESKINOPEUS_5MIN_KIINTEA_SUUNTA2_VVAPAAS2",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA1",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA2",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA1_MS1",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA2_MS2",
            "OHITUKSET_5MIN_KIINTEA_SUUNTA1_MS1",
            "OHITUKSET_5MIN_KIINTEA_SUUNTA2_MS2",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA1",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA2",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA1_MS1",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA2_MS2",
        ]

        entities = [
            DigitraficTmsMeasurementSensor(coordinator, tms_id, section_name, key)
            for key in lam_measurement_keys
        ]
        entities.append(DigitraficTmsConstantsSensor(coordinator, tms_id, section_name))

        async_add_entities(entities)
        return

    if monitor_type == MONITOR_WEATHER and weather_station_id:
        station_name = data.get(CONF_ROAD_SECTION) or str(weather_station_id)
        existing = coordinator.data.get("measurements") if coordinator.data else {}

        measurement_keys = []
        if isinstance(existing, dict):
            measurement_keys = [
                key for key in existing.keys() if not should_skip_weather_key(key)
            ]

        if not measurement_keys:
            measurement_keys = [
                key
                for key in WEATHER_SENSOR_DEFINITIONS.keys()
                if not should_skip_weather_key(key)
            ]

        created_keys: set[str] = set()

        def _normalize_key(key: str) -> str:
            return str(key).upper()

        def _make_entities(keys) -> list:
            entities: list = []
            for raw_key in keys:
                if should_skip_weather_key(raw_key):
                    continue
                norm = _normalize_key(raw_key)
                if norm in created_keys:
                    continue
                created_keys.add(norm)
                metadata = WEATHER_SENSOR_DEFINITIONS.get(raw_key, {})
                entities.append(
                    DigitraficWeatherMeasurementSensor(
                        coordinator,
                        weather_station_id,
                        station_name,
                        raw_key,
                        metadata,
                    )
                )
            return entities

        initial_entities = _make_entities(measurement_keys)
        if initial_entities:
            async_add_entities(initial_entities)

        async def _async_check_new_measurements() -> None:
            if not coordinator.data:
                return
            measurements = coordinator.data.get("measurements")
            if not isinstance(measurements, dict):
                return
            new_entities = _make_entities(measurements.keys())
            if new_entities:
                async_add_entities(new_entities)

        def _handle_coordinator_update() -> None:
            hass.async_create_task(_async_check_new_measurements())

        remove_listener = coordinator.async_add_listener(_handle_coordinator_update)
        config_entry.async_on_unload(remove_listener)

        return

    section_id = data.get(CONF_ROAD_SECTION_ID)
    section_name = data.get(CONF_ROAD_SECTION) or section_id

    entities = [
        DigitraficCurrentConditionsSensor(coordinator, section_id, section_name),
        DigitraficForecastSensor(coordinator, section_id, section_name),
    ]

    async_add_entities(entities)


class DigitraficCurrentConditionsSensor(CoordinatorEntity, SensorEntity):
    """Sensor for current road conditions."""

    def __init__(
        self, 
        coordinator: DigitraficDataCoordinator, 
        section_id: str,
        section_name: str
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.section_id = section_id
        self._section_name = section_name
        self._attr_unique_id = f"{DOMAIN}_{section_id}_conditions"
        # Use language-specific label
        label = "Ajokeli tällä hetkellä" if coordinator.language == "fi" else "Current Conditions"
        self._attr_name = f"{section_name} - {label}"

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        conditions_data = self.coordinator.data.get("conditions")
        if conditions_data:
            return self.coordinator.client.parse_conditions(conditions_data)
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity extra state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        conditions_data = self.coordinator.data.get("conditions")
        if conditions_data and conditions_data.get("features"):
            feature = conditions_data["features"][0]
            properties = feature.get("properties", {})
            
            if "reliability" in properties:
                attributes["reliability"] = properties.get("reliability")
            if "last_updated" in properties:
                attributes["last_updated"] = properties.get("last_updated")
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:road"


def format_station_name(raw: str) -> str:
    """Format station name for display.

    Rules:
    - If the raw name contains underscores, replace them with spaces and
      capitalize each token (e.g., 'vt4_Marostenmäki' -> 'Vt4 Marostenmäki').
    - Otherwise, title-case the words.
    """
    if not raw:
        return ""
    if "_" in raw:
        s = raw.replace("_", " ")
        tokens = s.split()
        return " ".join(t.capitalize() for t in tokens)
    # Default: title-case words (preserve numbers)
    return " ".join(t.capitalize() for t in raw.split())


def format_measurement_key(key: str, language: str = "fi") -> str:
    """Format measurement key tokens according to agreed rules.

    Args:
        key: The measurement key to format.
        language: Language code ('fi' or 'en').

    Rules:
    - Try to get translation from JSON files first.
    - Fallback to hardcoded translations for backwards compatibility.
    - Otherwise title-case Finnish tokens.
    """
    if not key:
        return ""
    
    # Try to get translation from JSON files first
    translated = _get_datapoint_translation(key, language)
    if translated != key:
        return translated
    
    # English translations map (kept for backwards compatibility)
    english_translations = {
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1": "Rolling avg speed 5min sliding dir 1",
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2": "Rolling avg speed 5min sliding dir 2",
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1_VVAPAAS1": "Rolling avg speed 5min pct of free-flow dir 1",
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2_VVAPAAS2": "Rolling avg speed 5min pct of free-flow dir 2",
        "KESKINOPEUS_60MIN_KIINTEA_SUUNTA1": "Fixed avg speed 60min dir 1",
        "KESKINOPEUS_60MIN_KIINTEA_SUUNTA2": "Fixed avg speed 60min dir 2",
        "KESKINOPEUS_5MIN_KIINTEA_SUUNTA1_VVAPAAS1": "Fixed avg speed 5min pct of free-flow dir 1",
        "KESKINOPEUS_5MIN_KIINTEA_SUUNTA2_VVAPAAS2": "Fixed avg speed 5min pct of free-flow dir 2",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA1": "Rolling count overtakes 5min dir 1",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA2": "Rolling count overtakes 5min dir 2",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA1_MS1": "Rolling count overtakes 5min lane 1 dir 1",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA2_MS2": "Rolling count overtakes 5min lane 2 dir 2",
        "OHITUKSET_5MIN_KIINTEA_SUUNTA1_MS1": "Fixed count overtakes 5min lane 1 dir 1",
        "OHITUKSET_5MIN_KIINTEA_SUUNTA2_MS2": "Fixed count overtakes 5min lane 2 dir 2",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA1": "Fixed count overtakes 60min dir 1",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA2": "Fixed count overtakes 60min dir 2",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA1_MS1": "Fixed count overtakes 60min lane 1 dir 1",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA2_MS2": "Fixed count overtakes 60min lane 2 dir 2",
    }
    
    if language == "en" and key in english_translations:
        return english_translations[key]
    
    # Finnish formatting (default)
    tokens = key.split("_")
    out = []
    for t in tokens:
        # Keep some tokens uppercase
        if t.upper().startswith("VVAPAAS"):
            out.append(t.upper())
            continue
        if t.upper() in ("MS1", "MS2"):
            out.append(t.upper())
            continue
        # Convert time window tokens like '5MIN' or '60MIN'
        m = re.match(r"^(\d+)MIN$", t, flags=re.IGNORECASE)
        if m:
            out.append(f"{m.group(1)}min")
            continue
        # Default: Title case
        out.append(t.capitalize())
    # Friendly display: join tokens with spaces for readability
    return " ".join(out)


class DigitraficForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor for road condition forecast."""

    def __init__(
        self, 
        coordinator: DigitraficDataCoordinator, 
        section_id: str,
        section_name: str
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.section_id = section_id
        self._section_name = section_name
        self._attr_unique_id = f"{DOMAIN}_{section_id}_forecast"
        # Use language-specific label
        label = "Ennuste" if coordinator.language == "fi" else "Forecast"
        self._attr_name = f"{section_name} - {label}"

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        forecast_data = self.coordinator.data.get("forecast")
        if forecast_data:
            return self.coordinator.client.parse_forecast(forecast_data)
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity extra state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        forecast_data = self.coordinator.data.get("forecast")
        if forecast_data and forecast_data.get("features"):
            # Include detailed forecast data as attributes
            forecasts = []
            for forecast in forecast_data["features"]:
                properties = forecast.get("properties", {})
                forecasts.append({
                    "time": properties.get("time"),
                    "condition": properties.get("condition")
                })
            
            if forecasts:
                attributes["forecast_data"] = forecasts
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:weather-cloudy"


class DigitraficWeatherMeasurementSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity representing a single weather-station measurement."""

    def __init__(
        self,
        coordinator: DigitraficDataCoordinator,
        station_id: int | str,
        station_name: str,
        measurement_key: str,
        metadata: Dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self.station_id = station_id
        self.measurement_key = measurement_key
        self._metadata = metadata or {}
        self._use_description = bool(self._metadata.get("use_description"))

        slug = slugify_measurement_key(measurement_key)
        self._attr_unique_id = f"{DOMAIN}_weather_{station_id}_{slug}"

        friendly_name = self._metadata.get(
            "name_fi" if coordinator.language == "fi" else "name_en"
        )
        if not friendly_name:
            friendly_name = format_weather_measurement_name(measurement_key, coordinator.language)

        self._attr_name = f"{format_station_name(str(station_name))} - {friendly_name}"

        device_class = self._metadata.get("device_class")
        state_class = self._metadata.get("state_class")
        icon = self._metadata.get("icon")

        if device_class:
            self._attr_device_class = device_class
        if state_class:
            self._attr_state_class = state_class
        if icon:
            self._attr_icon = icon
        
        # Set entity_registry_enabled_default based on measurement key
        self._attr_entity_registry_enabled_default = measurement_key in WEATHER_ENABLED_BY_DEFAULT

    def _get_measurement(self) -> Dict[str, Any] | None:
        data = self.coordinator.data or {}
        measurements = data.get("measurements") or {}
        if not isinstance(measurements, dict):
            return None

        measurement = measurements.get(self.measurement_key)
        if measurement is not None:
            return measurement

        for key, value in measurements.items():
            if isinstance(key, str) and key.lower() == self.measurement_key.lower():
                return value

        return None

    @property
    def available(self) -> bool:
        if not self.coordinator.last_update_success:
            return False
        return self._get_measurement() is not None

    @property
    def state(self) -> Any:
        measurement = self._get_measurement()
        if not measurement:
            return None

        # Special handling for VALLITSEVA_SÄÄ - translate WMO code
        if self.measurement_key == "VALLITSEVA_SÄÄ":
            value = measurement.get("value")
            if value is not None:
                lang = self.coordinator.language or "fi"
                return translate_wmo_code(value, lang)
            return None

        if self._use_description:
            lang = self.coordinator.language or "fi"
            desc_key = "sensorValueDescriptionFi" if lang == "fi" else "sensorValueDescriptionEn"
            description = (
                measurement.get(desc_key)
                or measurement.get("sensorValueDescriptionFi")
                or measurement.get("sensorValueDescriptionEn")
            )
            return description or measurement.get("value")

        return measurement.get("value")

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self._use_description:
            return None
        measurement = self._get_measurement()
        if not measurement:
            return None
        return measurement.get("unit")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        measurement = self._get_measurement()
        if not measurement:
            return {}

        attrs: Dict[str, Any] = {
            "sensor_id": measurement.get("id"),
            "measured_time": measurement.get("measuredTime"),
        }

        # For VALLITSEVA_SÄÄ, always include the raw WMO code
        if self.measurement_key == "VALLITSEVA_SÄÄ":
            attrs["wmo_code"] = measurement.get("value")

        if not self._use_description:
            attrs["raw_value"] = measurement.get("value")

        if measurement.get("unit"):
            attrs["unit"] = measurement.get("unit")

        desc_fi = measurement.get("sensorValueDescriptionFi")
        if desc_fi:
            attrs["description_fi"] = desc_fi

        desc_en = measurement.get("sensorValueDescriptionEn")
        if desc_en:
            attrs["description_en"] = desc_en

        data_updated = (self.coordinator.data or {}).get("data_updated_time")
        if data_updated:
            attrs["station_data_updated_time"] = data_updated

        return attrs


class DigitraficTmsConstantsSensor(CoordinatorEntity, SensorEntity):
    """Sensor that exposes TMS sensor-constant values (VVAPAAS, MS1/MS2, etc.).

    This sensor aggregates the station's sensor-constant values into a single
    JSON-serializable attribute so users can inspect LAM constants.
    """

    def __init__(self, coordinator: DigitraficDataCoordinator, station_id: int, station_name: str):
        super().__init__(coordinator)
        self.station_id = station_id
        self._station_name = station_name
        self._attr_unique_id = f"{DOMAIN}_tms_{station_id}_constants"
        self._attr_name = f"{format_station_name(station_name)} - Sensor Constants"

    @property
    def state(self) -> str | None:
        # No single scalar state — return availability indicator
        return "available" if self.coordinator.last_update_success else "unavailable"

    @property
    def extra_state_attributes(self):
        attrs = {}
        data = self.coordinator.data or {}
        sc = data.get("sensor_constants") or {}
        # Expecting sensorConstantValues list
        vals = sc.get("sensorConstantValues") if isinstance(sc, dict) else None
        if vals:
            for v in vals:
                name = v.get("name")
                value = v.get("value")
                if name:
                    attrs[name] = value
        return attrs


class DigitraficTmsMeasurementSensor(CoordinatorEntity, SensorEntity):
    """Placeholder sensor for a specific LAM/TMS measurement key.

    Currently this reads values from coordinator.data if available; if the
    integration later implements per-sensor observations fetching, the
    coordinator can populate `measurements` and this entity will pick them up.
    """

    def __init__(self, coordinator: DigitraficDataCoordinator, station_id: int, station_name: str, measure_key: str):
        super().__init__(coordinator)
        self.station_id = station_id
        self._station_name = station_name
        self.measure_key = measure_key
        self._attr_unique_id = f"{DOMAIN}_tms_{station_id}_{measure_key}"
        # Use friendly formatting for station and measurement names
        self._attr_name = f"{format_station_name(station_name)} - {format_measurement_key(measure_key, coordinator.language)}"
        # Enable HA statistics and graphing
        self._attr_state_class = "measurement"

    @property
    def state(self) -> Any:
        data = self.coordinator.data or {}
        _LOGGER.debug("Getting state for %s, data keys: %s", self.measure_key, list(data.keys()))
        
        # Try sensor constants first (some keys like VVAPAAS may be constants)
        sc = data.get("sensor_constants") or {}
        vals = sc.get("sensorConstantValues") if isinstance(sc, dict) else None
        if vals:
            for v in vals:
                if v.get("name") == self.measure_key:
                    value = v.get("value")
                    _LOGGER.debug("Found constant value for %s: %s", self.measure_key, value)
                    # Return numeric constant value as-is (int/float)
                    return value

        # Next try station measurements if coordinator provides them under 'measurements'
        measurements = data.get("measurements") or {}
        _LOGGER.debug("Measurements available: %s", list(measurements.keys()) if isinstance(measurements, dict) else "None")
        
        if isinstance(measurements, dict) and self.measure_key in measurements:
            m = measurements.get(self.measure_key)
            if isinstance(m, dict) and "value" in m:
                value = m.get("value")
                _LOGGER.debug("Found measurement value for %s: %s", self.measure_key, value)
                return value
            # If measurement entry is a raw value, return it (numeric)
            _LOGGER.debug("Found raw measurement for %s: %s", self.measure_key, m)
            return m

        # Check if there's a close match (sometimes the API returns slightly different keys)
        if isinstance(measurements, dict):
            for key, measurement in measurements.items():
                if self.measure_key.lower() in key.lower() or key.lower() in self.measure_key.lower():
                    if isinstance(measurement, dict) and "value" in measurement:
                        value = measurement.get("value")
                        _LOGGER.debug("Found fuzzy match %s -> %s: %s", self.measure_key, key, value)
                        return value

        _LOGGER.debug("No data found for %s", self.measure_key)
        # Return unavailable state instead of None to distinguish from "no data yet"
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Sensor is available if coordinator is successful AND we have data for this measurement
        if not self.coordinator.last_update_success:
            return False
            
        # Check if we have actual measurement data
        data = self.coordinator.data or {}
        measurements = data.get("measurements") or {}
        sensor_constants = data.get("sensor_constants") or {}
        
        # Available if we have either measurement data or sensor constant data
        has_measurement = isinstance(measurements, dict) and self.measure_key in measurements
        has_constant = False
        if isinstance(sensor_constants, dict):
            vals = sensor_constants.get("sensorConstantValues", [])
            has_constant = any(v.get("name") == self.measure_key for v in vals)
            
        return has_measurement or has_constant

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement from coordinator data."""
        data = self.coordinator.data or {}
        measurements = data.get("measurements") or {}
        if isinstance(measurements, dict) and self.measure_key in measurements:
            m = measurements.get(self.measure_key)
            if isinstance(m, dict) and "unit" in m:
                unit = m.get("unit")
                _LOGGER.debug("Unit for %s: %s", self.measure_key, unit)
                # Handle special unit cases (°, km/h, %, kpl/h)
                if unit == "***":
                    return "%"  # Common placeholder for percentage
                # For speed measurements, ensure we have km/h
                if "KESKINOPEUS" in self.measure_key and unit in ["km/h", "kmh", "km"]:
                    return "km/h"
                return unit
                
        # Default units based on measurement type
        if "KESKINOPEUS" in self.measure_key:
            return "km/h"
        elif "OHITUKSET" in self.measure_key:
            return "count"
        elif "VVAPAAS" in self.measure_key:
            return "%"
            
        return None

    @property
    def icon(self) -> str:
        return "mdi:counter"
