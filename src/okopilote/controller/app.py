from configparser import ConfigParser
from importlib import import_module

from .api import API
from .controller import Controller
from .room import RoomSet


class App:
    controller = None
    conf = None
    config_file = ""
    dry_run = False

    @classmethod
    def restart(cls):
        cls.controller.stop()
        cls._init_config()
        cls._init_controller()

    @classmethod
    def start(cls, config_file, dry_run=False):

        cls.config_file = config_file
        cls.dry_run = dry_run
        cls._init_config()
        cls._init_controller()
        myapi = API(
            cls,
            host=cls.conf["api"]["listen_addr"],
            port=cls.conf["api"]["listen_port"],
        )
        myapi.start()
        cls.controller.stop()

    @classmethod
    def _init_config(cls):

        cls.conf = ConfigParser()
        cls.conf.read_dict(
            {
                "boiler": {
                    "module": "",
                },
                "rooms": {
                    "url": "",
                },
                "controller": {
                    "period": "10.0",
                    "low_watermark_gen": "-0.3",
                    "high_watermark_gen": "0.4",
                    "low_watermark_avail": "-0.1",
                    "high_watermark_avail": "0.0",
                    "boiler_min_off": "1200",
                    "no_delay_on_start": "no",
                    "room_sync_expiration": "600",
                },
                "api": {
                    "listen_addr": "127.0.0.1",
                    "listen_port": "8881",
                },
            }
        )
        with open(cls.config_file) as f:
            cls.conf.read_file(f)

    @classmethod
    def _init_controller(cls):
        ctrl_conf = cls.conf["controller"]
        boiler_conf = cls.conf["boiler"]
        boiler_module = import_module(boiler_conf["module"])
        cls.controller = Controller(
            boiler=boiler_module.from_conf(boiler_conf),
            roomset=RoomSet(cls.conf["rooms"].get("url").split()),
            period=ctrl_conf.getfloat("period"),
            low_watermark_gen=ctrl_conf.getfloat("low_watermark_gen"),
            high_watermark_gen=ctrl_conf.getfloat("high_watermark_gen"),
            low_watermark_avail=ctrl_conf.getfloat("low_watermark_avail"),
            high_watermark_avail=ctrl_conf.getfloat("high_watermark_avail"),
            boiler_min_off=ctrl_conf.getfloat("boiler_min_off"),
            no_delay_on_start=ctrl_conf.getboolean("no_delay_on_start"),
            room_sync_expiration=ctrl_conf.getint("room_sync_expiration"),
            dry_run=cls.dry_run,
        )
        cls.controller.start()
