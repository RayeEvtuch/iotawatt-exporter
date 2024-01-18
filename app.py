#! /usr/bin/env python3

from time import sleep
import requests
import json

from prometheus_client import start_http_server, Gauge

# Create metrics to track data
POWER_USAGE_WATTS = Gauge(
    'power_usage_watts', 'Total amount of watts being drawn', ['circuit'])
POWER_SUPPLY_VOLTS = Gauge(
    'power_supply_volts', 'Total amount of volts being supplied', ['circuit'])

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    while True:
        # Poll once every five seconds
        sleep(5)

        # Get the list of series from the IoTaWatt
        series_response = requests.get(
            url='http://iotawatt.local/query?show=series')
        series_data = json.loads(series_response.content)
        series = dict([(serie['name'], serie['unit'])
                      for serie in series_data['series']])

        # Build the query for the series data
        query = {
            'select': "[{}]".format(','.join(series.keys())),
            'group': 'all',
            'begin': 's-5s',
            'end': 's',
            'header': 'yes',
        }

        # Query the IoTaWatt
        values_response = requests.get(
            url='http://iotawatt.local/query', params=query)
        values_data = json.loads(values_response.content)

        # Parse the series data
        i = 0
        # Iterate through each labeled provided in the response
        for label in values_data['labels']:
            # Check if the label was returned in the list of series
            if label in series.keys():
                # Check to see if there is actually data
                if values_data['data'][0][i]:
                    if series[label] == 'Watts':
                        POWER_USAGE_WATTS.labels(label).set(
                            values_data['data'][0][i])
                    elif series[label] == 'Volts':
                        POWER_SUPPLY_VOLTS.labels(label).set(
                            values_data['data'][0][i])
                    else:
                        print("{} is not a valid unit for {}".format(
                            series[label], label))
                else:
                    print("{} has a null value".format(label))
            else:
                print("{} is not a valid series".format(label))
            i += 1
