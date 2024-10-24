import requests
from requests.exceptions import ConnectionError, Timeout
from time import time
from types import SimpleNamespace


class RoomError(Exception):
    """Temporary error with the remote room."""


class RoomSet:
    def __init__(self, URIs=[]):
        self.uris = URIs
        self.rooms = {}

    def _api_controller_sync(self, uri, data):
        url = uri + "/controller_sync"
        try:
            r = requests.post(url, json=data, verify=False, timeout=5)
        except (ConnectionError, Timeout):
            raise RoomError("no answer from {} (network error)".format(url))
        if r.status_code == 404:
            raise RoomError("{} not found (404 error)".format(url))
        if r.status_code != 200:
            raise RoomError("unexpected response from {}: {}".format(url, r))

        now = time()
        for room_id, data in r.json().items():
            self.rooms.setdefault(
                room_id,
                SimpleNamespace(room_id=room_id, temp_deviation=None, sync_time=None),
            )
            self.rooms[room_id].temp_deviation = data["temp_deviation"]
            self.rooms[room_id].sync_time = now

    def controller_sync(self, temp_set_offset, circulator_runs=None):
        errors = []
        data = {"temp_set_offset": temp_set_offset}
        if circulator_runs is not None:
            data["circulator_runs"] = circulator_runs

        for uri in self.uris:
            try:
                self._api_controller_sync(uri, data=data)
            except Exception as e:
                errors.append(str(e))

        if errors:
            raise RoomError("{}".format("; ".join(errors)))

    def __str__(self):
        uri = ["url=" + u for u in self.uris]
        rooms = []
        for r in self.rooms.values():
            keyvals = ["{}={}".format(k, v) for k, v in vars(r).items()]
            rooms.append("Room({})".format(", ".join(keyvals)))
        return "RoomSet({} - {})".format(";".join(uri), "; ".join(rooms))
