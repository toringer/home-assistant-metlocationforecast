"""Support for Yr.no weather service."""
import asyncio
import logging

from xml.parsers.expat import ExpatError

import aiohttp
import async_timeout
import voluptuous as vol
import datetime
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_LATITUDE, CONF_LONGITUDE, ATTR_ATTRIBUTION)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (async_track_utc_time_change,
                                         async_call_later)
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


SCAN_INTERVAL = datetime.timedelta(minutes=30)

# https://api.met.no/license_data.html
ATTRIBUTION = "Weather forecast from met.no, delivered by the Norwegian " \
              "Meteorological Institute."


REQUEST_HEADER = {
    'User-Agent': 'home-assistant-metlocationforecast/0.1 https://github.com/toringer/home-assistant-metlocationforecast'
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LATITUDE): cv.latitude,
    vol.Optional(CONF_LONGITUDE): cv.longitude
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Yr.no sensor."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    if None in (latitude, longitude):
        _LOGGER.error("Latitude or longitude not set in Home Assistant config")
        return False

    coordinates = {
        'lat': str(latitude),
        'lon': str(longitude)
    }

    met_api = MetData(hass, coordinates)
    sensor = MetLocationForecast(met_api)
    await sensor.async_update()
    async_add_entities([sensor])


class MetLocationForecast(Entity):
    """Representation of an Yr.no sensor."""

    def __init__(self, met_api):
        """Initialize the sensor."""
        self._met_api = met_api
        self._state = 0
        self._unit_of_measurement = '???'
        self._forecast = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'met.no location forecast'

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def should_poll(self):
        """No polling needed."""
        return True

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            'forecast': self._forecast
        }

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:package"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    async def async_update(self):
        """Retrieve latest state."""
        data = await self._met_api.fetching_data()
        # forecast = []
        # for time_entry in data["properties"]["timeseries"]:
        #     _LOGGER.info("time_entry: " + str(time_entry))
        #     valid_from = time_entry['time']
        #     valid_to = (dt_util.parse_datetime(time_entry['time']) + datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')
        #     unit = data['properties']['meta']['units']['precipitation_amount']
        #     value = time_entry['data']['instant']['details']['precipitation_rate']
        #     forecast.append({'unit': unit,'value': value, 'from': valid_from, 'to': valid_to})

        self._forecast = data['properties']['timeseries']
        self._state = self._forecast[0]['data']['instant']['details']['air_temperature']
        self._unit_of_measurement = data['properties']['meta']['units']['air_temperature']


class MetData:
    """Get the latest data and updates the states."""

    def __init__(self, hass, coordinates):
        """Initialize the data object."""
        self._url = 'https://api.met.no/weatherapi/locationforecast/2.0/complete'
        self._urlparams = coordinates
        self.data = {}
        self.hass = hass

    async def fetching_data(self, *_):
        """Get the latest data from yr.no."""

        def try_again(err: str):
            """Retry in 15 to 20 minutes."""
            minutes = 15 + randrange(6)
            _LOGGER.error("Retrying in %i minutes: %s", minutes, err)
        try:
            response = requests.get(url = self._url, params = self._urlparams, headers = REQUEST_HEADER)
            if response.status_code != 200:
                try_again('{} returned {}'.format(response.url, response.status_code))
                return

            data = response.json()

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            try_again(err)
            return

        try:
            self.data = data
            return self.data
        except (ExpatError, IndexError) as err:
            try_again(err)
            return

