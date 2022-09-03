## Obsolete, see [met-next-6-hours-forecast](https://github.com/toringer/home-assistant-met-next-6-hours-forecast)

# met.no location forecast

This component will add a sensor for met.no location forecast. Detailed precipitation data is available in the 'forecast' attribute.

https://api.met.no/weatherapi/locationforecast/2.0/complete


## HACS Installation

1. Open HACS Settings
2. Add `https://github.com/toringer/home-assistant-metlocationforecast` as a custom repository 
2. Add the code to your `configuration.yaml` using the config options below.
3. **You will need to restart after installation for the component to start working.**



## Sample Sensor Configuration

    sensor:
    - platform: metlocationforecast
