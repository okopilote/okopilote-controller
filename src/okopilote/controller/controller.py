import logging
import threading
from time import time

logger = logging.getLogger(__name__)


class Controller(threading.Thread):
    """
    Control the boiler to keep rooms warm.
    """

    def __init__(
        self,
        boiler=None,
        roomset=None,
        period=10.0,
        low_watermark_gen=-0.3,
        high_watermark_gen=0.4,
        low_watermark_avail=-0.1,
        high_watermark_avail=0.0,
        boiler_min_off=1200.0,
        no_delay_on_start=False,
        room_sync_expiration=600,
        dry_run=False,
    ):

        super().__init__(name="controller")

        self.boiler = boiler
        self.roomset = roomset
        self.period = period
        self.lo_watermk_gen = low_watermark_gen
        self.hi_watermk_gen = high_watermark_gen
        self.lo_watermk_deliv = low_watermark_avail
        self.hi_watermk_deliv = high_watermark_avail
        self.boiler_min_off = boiler_min_off
        self.no_delay_on_start = no_delay_on_start
        self.dry_run = dry_run
        self.room_sync_expir = room_sync_expiration

        self.fireon_allowed = None
        self.cold_rooms = []
        self.worse_deviation = 0

        # Delay to wait between each cycle, in seconds
        self.wait_delay = self.period
        # Temperature deviation threshold to decide wether we force the system
        # to heat or not.
        self.set_offset = None
        # Used to terminate the thread
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.errors = []
        self.warnings = []

        # Boiler data
        self.accept_ctrl = None
        self.boiler_gen_heat = None
        self.boiler_deliv_heat = None
        self.boiler_heat_avail = None
        self.force_heat = False
        # Engine (boiler) starter
        self.starter = False
        # Track boiler status in order to avoid changing it too often
        self.boiler_change_time = None

    def run(self):
        try:
            logger.info("Controller started")
            while not self.event.is_set():
                self._do_core_stuff()
                self.event.wait(self.wait_delay)
        except Exception as e:
            logger.exception(("FATAL ERROR: {}").format(e))
            self.errors.append("FATAL ERROR: {}".format(e))
        try:
            self.boiler.release_heating()
        except Exception:
            pass
        logger.info("Controller stopped")

    def stats(self):
        return self._stats()

    def stop(self):
        """
        End the thread.
        """
        self.event.set()

    def _do_core_stuff(self):
        errors, warnings = [], []

        try:
            # Collect boiler data
            self.boiler.acquire()
            self.accept_ctrl = self.boiler.does_accept_ctrl()
            new_boiler_gen_heat = self.boiler.is_gen_heat()
            self.boiler_deliv_heat = self.boiler.is_deliv_heat()
            self.boiler_heat_avail = self.boiler.is_heat_avail()
        except Exception as e:
            errors.append(("Failed to request boiler data: {}").format(e))
            self.wait_delay = min(600, 2 * self.wait_delay)
            logger.error(errors[-1])
            self.errors = errors
            self.warnings = warnings
            return

        # Track boiler changes
        if new_boiler_gen_heat is not self.boiler_gen_heat:
            if self.boiler_gen_heat is None and self.no_delay_on_start:
                self.boiler_change_time = None
            else:
                self.boiler_change_time = time()
            self.boiler_gen_heat = new_boiler_gen_heat

        # Allow or not fire on the boiler
        if (
            self.boiler_change_time is not None
            and self.boiler_change_time > time() - self.boiler_min_off
        ):
            self.fireon_allowed = False
        else:
            self.fireon_allowed = True

        # Check that the controller is requested
        if not self.accept_ctrl:
            self.errors = errors
            self.warnings = warnings
            self.wait_delay = self.period
            return

        # Compute offset for temperature setpoint
        if self.boiler_gen_heat:
            self.set_offset = self.hi_watermk_gen
            self.starter = False
        elif self.boiler_deliv_heat and self.boiler_heat_avail:
            self.set_offset = self.hi_watermk_deliv
            self.starter = False
        elif self.starter:
            self.set_offset = self.hi_watermk_gen
        elif self.boiler_heat_avail:
            self.set_offset = self.lo_watermk_deliv
        else:
            self.set_offset = self.lo_watermk_gen

        # Sync rooms
        try:
            self.roomset.controller_sync(
                temp_set_offset=self.set_offset, circulator_runs=self.boiler_deliv_heat
            )
        except Exception as e:
            errors.append("Rooms sync: {}".format(e))
            logger.error(errors[-1])
        for id_, r in self.roomset.rooms.items():
            if r.temp_deviation is None:
                warnings.append(
                    ('Room "{}" does\'nt know its temperature ' + "deviation").format(
                        id_
                    )
                )

        # Compute heat necessity
        self.cold_rooms = [
            r
            for r in self.roomset.rooms.values()
            if r.temp_deviation is not None
            and r.temp_deviation < 0
            and r.sync_time > time() - self.room_sync_expir
        ]

        # Make a decision
        if self.cold_rooms:
            self.worse_deviation = min([r.temp_deviation for r in self.cold_rooms])
            if self.boiler_heat_avail or self.fireon_allowed or self.force_heat:
                self.force_heat = True
                # Force until upper offset is rised
                if self.set_offset in [self.lo_watermk_gen, self.lo_watermk_deliv]:
                    self.starter = True
            else:
                self.force_heat = False
                warnings = (
                    "Can't force heating because the boiler is off for"
                    + " less than {} seconds"
                ).format(self.boiler_min_off)
                logger.warning(warnings[-1])
        else:
            self.worse_deviation = 0
            self.force_heat = False

        # Apply the decision
        try:
            if self.force_heat:
                if not self.dry_run:
                    self.boiler.force_heating(-self.worse_deviation)
            else:
                if not self.dry_run:
                    self.boiler.release_heating()
        except Exception as e:
            errors.append(
                "Failed to {} heating: {}".format(
                    "force" if self.force_heat else "release", e
                )
            )
            logger.error(errors[-1])

        self.errors = errors
        self.warnings = warnings
        self.wait_delay = self.period
