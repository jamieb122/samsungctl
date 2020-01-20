import base64
import json
import logging
import socket
import time
import struct
import wakeonlan

from . import exceptions
from . import utils




URL_FORMAT = "ws://{}:{}/api/v2/channels/samsung.remote.control?name={}&id={}&mac={}&ip={}"

class RemoteWebsocket():
    """Object for remote control connection."""

    def __init__(self, config):
        import websocket

        if not config["port"]:
            config["port"] = 8001

        if config["timeout"] == 0:
            config["timeout"] = None

        url = URL_FORMAT.format(config["host"], config["port"],
                                self._serialize_string(config["name"]), self._serialize_string(config["mac"]), 
                                self._serialize_string(config["mac"]), self._serialize_string(config["ip"]))
        print("URL: %s" % (url,))
        self.config = config

        if utils.check_ping(config["host"]) == False:
            logging.debug("Host not up")
            config["timeout"] = 2
        self.connection = websocket.create_connection(url, config["timeout"])
        self._read_response()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.debug("Connection closed.")

    def control(self, key):
        """Send a control command."""
        if not self.connection:
            raise exceptions.ConnectionClosed()

        elif key =="KEY_POWEROFF":
            if utils.check_ping(self.config["host"]) == True:
                print("TV Alive, turning off")
                key = "KEY_POWER"
            else:
                return

        payload = json.dumps({
            "method": "ms.remote.control",
            "params": {
                "Cmd": "Click",
                "DataOfCmd": key,
                "Option": "false",
                "TypeOfRemote": "SendRemoteKey"
            }
        })

        logging.info("Sending control command: %s", key)
        self.connection.send(payload)
        time.sleep(self._key_interval)

    _key_interval = 0.5

    def _read_response(self):
        response = self.connection.recv()
        response = json.loads(response)

        #print("Response: %s" % (response,))

        if response["event"] != "ms.channel.connect":
            self.close()
            raise exceptions.UnhandledResponse(response)

        logging.debug("Access granted.")

    @staticmethod
    def _serialize_string(string):
        if isinstance(string, str):
            string = str.encode(string)

        return base64.b64encode(string).decode("utf-8")
