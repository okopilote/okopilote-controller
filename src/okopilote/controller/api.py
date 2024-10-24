import json
from time import sleep

from bottle import Bottle, JSONPlugin, abort, static_file


class API:

    def __init__(self, app, host="127.0.0.1", port="8881"):
        self.app = app
        self.host = host
        self.port = port

    def start(self):
        mybottle = Bottle()

        @mybottle.get("/api/controller")
        def api_get_controller():
            data = {
                "is_alive": self.app.controller.is_alive(),
                "cold_rooms": [
                    {"name": r.name, "temp_deviation": r.temp_deviation}
                    for r in self.app.controller.cold_rooms
                ],
            }
            for k in [
                "accept_ctrl",
                "force_heat",
                "set_offset",
                "boiler_change_time",
                "fireon_allowed",
                "errors",
                "warnings",
            ]:
                data[k] = getattr(self.app.controller, k)
            return data

        @mybottle.get("/api/controller/restart")
        def api_restart_controller():
            self.app.restart()
            return {"success": self.app.controller.is_alive() is True}

        @mybottle.get("/api/controller/stop")
        def api_stop_controller():
            if self.app.controller.is_alive():
                self.app.controller.stop()
                sleep(0.5)
                if self.app.controller.is_alive():
                    sleep(1)
                return {"success": self.app.controller.is_alive() is False}
            else:
                return "Already stopped"

        @mybottle.get("/api/controller/dump")
        def api_dump_controller():
            dump = {k: v for k, v in vars(self.app.controller).items() if k[0] != "_"}
            dump.update({"is_alive": self.app.controller.is_alive()})
            return dump

        @mybottle.get("/api/boiler/ambiant_temperature")
        def api_get_boiler_ambiant_temperature():
            try:
                return str(self.app.controller.boiler.ambiant_temperature)
            except NotImplementedError:
                abort(
                    404, "Boiler object does not implement ambiant temperature sensor"
                )

        @mybottle.get("/")
        def index():
            return static_file("index.html", root="./views")

        mybottle.install(
            JSONPlugin(json_dumps=lambda body: json.dumps(body, default=str))
        )
        mybottle.run(host=self.host, port=self.port)
