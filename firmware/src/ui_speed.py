import time
import lvgl as lv

from ui_common import (
    UIBase,
    WHEEL_CIRCUMFERENCE,
    DISP_WIDTH,
    DISP_HEIGHT,
    MARGIN,
    TILE_H,
    COL_BCKGND,
    COL_TILE,
    COL_BORDER,
    COL_TEXT,
    COL_SEL_TEXT,
    COL_SEL_BCKGND,
    COL_EDIT_BCKGND,
    VALUE_UPDATE_MS,
)


class SpeedScreen(UIBase):
    """
    Wheel speed tester screen
    Row 0: [RPM] : read-only live value
    Row 1: [m/s] : read-only live value
    Row 2: [kph] : read-only live value
    """

    def __init__(self, display):
        super().__init__(display)

        self.previous_disp_update_time = time.ticks_ms()

        self._last_rpm = ""
        self._last_ms = ""
        self._last_kph = ""

    def _row_y(self, row):
        return 2 * MARGIN + row * (MARGIN + TILE_H)

    # ── Public entry point ────────────────────────────────────────────

    def show(self, wheel_sensor, enc_btn):
        self._build_gui(wheel_sensor, enc_btn)

    def _build_gui(self, wheel_sensor, enc_btn):
        self._clear_screen()
        scrn = lv.screen_active()
        scrn.set_style_bg_color(COL_BCKGND, 0)
        back_fill = self._make_back_bar(scrn)

        # Row 0: RPM
        t_rpm = self._make_tile(
            scrn, MARGIN, self._row_y(0), DISP_WIDTH - 2 * MARGIN, TILE_H
        )
        self._tile_key(t_rpm, "RPM")
        v_rpm = self._tile_val(t_rpm, "0")

        # Row 1: m/s
        t_ms = self._make_tile(
            scrn, MARGIN, self._row_y(1), DISP_WIDTH - 2 * MARGIN, TILE_H
        )
        self._tile_key(t_ms, "Speed (m/s)")
        v_ms = self._tile_val(t_ms, "0")

        # Row 2: kph
        t_kph = self._make_tile(
            scrn, MARGIN, self._row_y(2), DISP_WIDTH - 2 * MARGIN, TILE_H
        )
        self._tile_key(t_kph, "Speed (kph)")
        v_kph = self._tile_val(t_kph, "0")

        self._run_loop(wheel_sensor, enc_btn, back_fill, v_rpm, v_ms, v_kph)

    def _run_loop(self, wheel_sensor, enc_btn, back_fill, v_rpm, v_ms, v_kph):

        press_ms = 0

        while True:
            press_ms = self._update_back_bar(back_fill, enc_btn, press_ms)
            if press_ms == -1:
                return

            wheel_sensor.update_pulse_count()
            self._update_readouts(wheel_sensor, v_rpm, v_ms, v_kph, VALUE_UPDATE_MS)

    def _update_readouts(self, wheel_sensor, v_rpm, v_ms, v_kph, delay_ms):
        """Refresh all live-value labels only if they've changed and it's been more than delay ms since last update"""

        now = time.ticks_ms()
        if time.ticks_diff(now, self.previous_disp_update_time) > delay_ms:
            self.previous_disp_update_time = now

            new_rpm = f"{wheel_sensor.get_rpm_1s():d}"
            if new_rpm != self._last_rpm:
                self._last_rpm = new_rpm
                v_rpm.set_text(new_rpm)

            wheel_hz = wheel_sensor.get_hz_1s()
            wheel_ms = wheel_hz * WHEEL_CIRCUMFERENCE

            new_ms = f"{wheel_ms:.1f}"
            if new_ms != self._last_ms:
                self._last_ms = new_ms
                v_ms.set_text(new_ms)

            wheel_kph = wheel_ms * 3.6

            new_kph = f"{wheel_kph:.1f}"
            if new_kph != self._last_kph:
                self._last_ms = new_kph
                v_kph.set_text(new_kph)
