from datetime import datetime, timedelta
import pytz
import logging
import json
import os
import sys
import signal
import threading, time

from chasemapper.listeners import OziListener, UDPListener, fix_datetime
from oled.device import ssd1306, sh1106
from oled.render import canvas
from PIL import ImageFont

data_listeners = []
EXTRA_FIELDS = ['bt', 'temp', 'humidity', 'sats', 'snr','batt']

font = ImageFont.load_default()
oled = ssd1306(port=0, address=0x3C)

global _lat 
global _lon
global _alt
global _time_dt
global _callsign
global _snr 
global data_pacote


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def udp_listener_summary_callback(data):
    ''' Handle a Payload Summary Message from UDPListener '''

    # Modem stats messages are also passed in via this callback.
    # handle them separately.
    if data['type'] == 'MODEM_STATS':
        handle_modem_stats(data)
        return

    # Otherwise, we have a PAYLOAD_SUMMARY message.

    # Extract the fields we need.
    # Convert to something generic we can pass onwards.
    output = {}
    output['lat'] = float(data['latitude'])
    output['lon'] = float(data['longitude'])
    output['alt'] = float(data['altitude'])
    output['callsign'] = data['callsign']

    logging.info("Horus UDP Data: %.5f, %.5f, %.1f" % (output['lat'], output['lon'], output['alt']))

    # Process the 'short time' value if we have been provided it.
    if 'time' in data.keys():
        output['time_dt'] = fix_datetime(data['time'])
        #_full_time = datetime.utcnow().strftime("%Y-%m-%dT") + data['time'] + "Z"
        #output['time_dt'] = parse(_full_time)
    else:
        # Otherwise use the current UTC time.
        
        output['time_dt'] = pytz.utc.localize(datetime.utcnow())

    # Copy out any extra fields that we want to pass on to the GUI.
    for _field in EXTRA_FIELDS:
        if _field in data:
            output[_field] = data[_field]

    try:
        handle_new_payload_position(output)
    except Exception as e:
        logging.error("Error Handling Payload Position - %s" % str(e))

def handle_new_payload_position(data):

    _lat = data['lat']
    _lon = data['lon']
    _alt = data['alt']
    _time_dt = data['time_dt']
    _callsign = data['callsign']
    _snr = data['snr']
    _time_dt = data['time_dt']
    _batt = data['batt']


    
    with canvas(oled) as draw:
        draw.text((0, 0), "Sonde:" + str(_callsign), font=font, fill=255)
        draw.text((0, 10), "Lat: " + str(_lat), font=font, fill=255)
        draw.text((0, 20), "Lng: " + str(_lon), font=font, fill=255)
        draw.text((0, 30), "Alt: " + str(_alt), font=font, fill=255)
        draw.text((0, 40), "SNR: " + str(_snr), font=font, fill=255)
        draw.text((0, 50), "Vlt: " + str(_batt), font=font, fill=255)
            


           


def main():
    _telem_horus_udp_listener = UDPListener(summary_callback=udp_listener_summary_callback,
                                            gps_callback=None,
                                            bearing_callback=None,
                                            port=55673)
    _telem_horus_udp_listener.start()
    data_listeners.append(_telem_horus_udp_listener)

    with canvas(oled) as draw:
        draw.text((1, 30), "Sem dados no Momento!", font=font, fill=255)


if __name__ == "__main__":
    main()
