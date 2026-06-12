import time
import lvgl as lv

from ui_common import (
    UIBase,
    Direction,
    VOLTAGE_MIN_MV,
    VOLTAGE_MAX_MV,
    VOLTAGE_DEFAULT_MV,
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


class ManualScreen(UIBase):
    """
    Manual motor test screen.

    Row 0: [RPM]          : read-only live value
    Row 1: [TIMER]        : read-only live value
    Row 2: [AMPS] | [TEMP]: read-only live value
    Row 3: [DIR] | [VOLT] : nav 0 | nav 1
    Row 4: [START/STOP]   : nav 2
    """

    def __init__(self, display):
        super().__init__(display)
        self.motor_run_state = False
        self.manual_dir = Direction.FWD
        self.manual_vol_mv = VOLTAGE_DEFAULT_MV
        self.manual_run_start = None
        self.previous_disp_update_time = time.ticks_ms()

        # Dirty-flag mirrors
        self._old_run_state = self.motor_run_state
        self._old_dir = self.manual_dir
        self._old_vol_mv = self.manual_vol_mv

        self._last_amps = ""
        self._last_rpm = ""
        self._last_temp = ""
        self._last_timer = ""

    # ── Private helpers ───────────────────────────────────────────────

    def _param_str(self, key):
        if key == "DIR":
            return "FWD" if self.manual_dir == Direction.FWD else "REV"
        if key == "VOLT":
            return f"{self.manual_vol_mv / 1000:.1f}V"
        return ""

    def _set_tile_state(self, items, idx, state):
        tile, key, val = items[idx]
        if state == "selected":
            tile.set_style_bg_color(COL_SEL_BCKGND, 0)
            tile.set_style_border_width(0, 0)
            val.set_style_text_color(COL_SEL_TEXT, 0)
            if key:
                key.set_style_text_color(COL_SEL_TEXT, 0)
        elif state == "editing":
            tile.set_style_bg_color(COL_EDIT_BCKGND, 0)
            tile.set_style_border_width(0, 0)
            val.set_style_text_color(COL_SEL_TEXT, 0)
            if key:
                key.set_style_text_color(COL_SEL_TEXT, 0)
        else:
            tile.set_style_bg_color(COL_TILE, 0)
            tile.set_style_border_color(COL_BORDER, 0)
            tile.set_style_border_width(1, 0)
            val.set_style_text_color(COL_TEXT, 0)
            if key:
                key.set_style_text_color(COL_TEXT, 0)

    def _redraw_tiles(self, items, sel, editing=False):
        for i in range(len(items) - 1):
            self._set_tile_state(
                items,
                i,
                (
                    "editing"
                    if (i == sel and editing)
                    else "selected" if i == sel else "normal"
                ),
            )
        items[0][2].set_text(self._param_str("DIR"))
        items[1][2].set_text(self._param_str("VOLT"))
        items[2][2].set_text(
            lv.SYMBOL.PLAY + " START"
            if not self.motor_run_state
            else lv.SYMBOL.PAUSE + " PAUSE"
        )
        self._set_tile_state(items, 2, "selected" if sel == 2 else "normal")

    def _half_tile_x(self, col):
        """Left edge x for a half-width tile in the given column (0 or 1)."""
        half_w = int((DISP_WIDTH - 3 * MARGIN) / 2)
        return MARGIN + col * (half_w + MARGIN)

    def _half_tile_w(self):
        return int((DISP_WIDTH - 3 * MARGIN) / 2)

    def _row_y(self, row):
        return 2 * MARGIN + row * (MARGIN + TILE_H)

    # ── Public entry point ────────────────────────────────────────────

    def show(self, motor, rotary, enc_btn):
        self._build_gui(motor, rotary, enc_btn)

    def _build_gui(self, motor, rotary, enc_btn):
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

        # Row 1: TIMER
        t_timer = self._make_tile(
            scrn, MARGIN, self._row_y(1), DISP_WIDTH - 2 * MARGIN, TILE_H
        )
        self._tile_key(t_timer, "TIMER")
        v_timer = self._tile_val(t_timer, "--:--")

        # Row 2: AMPS | TEMP
        t_amps = self._make_tile(
            scrn, self._half_tile_x(0), self._row_y(2), self._half_tile_w(), TILE_H
        )
        self._tile_key(t_amps, "I")
        v_amps = self._tile_val(t_amps, "0mA")

        t_temp = self._make_tile(
            scrn, self._half_tile_x(1), self._row_y(2), self._half_tile_w(), TILE_H
        )
        self._tile_key(t_temp, "T")
        v_temp = self._tile_val(t_temp, f"{motor.get_temp_10s():.1f}°C")

        # Row 3: DIR | VOLT
        t_dir = self._make_tile(
            scrn, self._half_tile_x(0), self._row_y(3), self._half_tile_w(), TILE_H
        )
        k_dir = self._tile_key(t_dir, "DIR")
        v_dir = self._tile_val(t_dir, self._param_str("DIR"))

        t_volt = self._make_tile(
            scrn, self._half_tile_x(1), self._row_y(3), self._half_tile_w(), TILE_H
        )
        k_volt = self._tile_key(t_volt, "VOLT")
        v_volt = self._tile_val(t_volt, self._param_str("VOLT"))

        # Row 4: START / STOP
        start_h = DISP_HEIGHT - (3 * MARGIN + 4 * (MARGIN + TILE_H))
        t_start_stop = self._make_tile(
            scrn, MARGIN, self._row_y(4), DISP_WIDTH - 2 * MARGIN, start_h
        )
        v_start_stop = lv.label(t_start_stop)
        v_start_stop.set_text(lv.SYMBOL.PLAY + " START")
        v_start_stop.set_style_text_color(COL_TEXT, 0)
        v_start_stop.set_style_text_font(lv.font_montserrat_14, 0)
        v_start_stop.align(lv.ALIGN.CENTER, 0, 0)

        items = [
            (t_dir, k_dir, v_dir),
            (t_volt, k_volt, v_volt),
            (t_start_stop, None, v_start_stop),
        ]

        self._run_loop(
            motor, rotary, enc_btn, back_fill, items, v_rpm, v_timer, v_amps, v_temp
        )

    def _run_loop(
        self, motor, rotary, enc_btn, back_fill, items, v_rpm, v_timer, v_amps, v_temp
    ):
        while True:
            for i in range(len(items)):
                self._set_tile_state(items, i, "normal")

            rotary.set(
                min_val=0,
                max_val=len(items) - 1,
                value=2,
                incr=1,
                range_mode=rotary.RANGE_BOUNDED,
            )
            sel = 2
            prev_sel = -1
            editing = False
            press_ms = 0
            self._set_tile_state(items, 2, "selected")

            while True:

                sel, prev_sel, editing = self._handle_rotary(
                    rotary, items, sel, prev_sel, editing
                )

                press_ms = self._update_back_bar(back_fill, enc_btn, press_ms)

                if press_ms == -1:
                    self._on_long_press(motor, rotary, enc_btn, items, sel, editing)
                    return

                elif press_ms == -2:
                    press_ms = 0
                    editing = self._on_short_press(
                        motor, rotary, enc_btn, items, sel, editing
                    )

                self._update_motor(motor)
                self._update_readouts(
                    motor, v_rpm, v_timer, v_amps, v_temp, VALUE_UPDATE_MS
                )

    def _on_long_press(self, motor, rotary, enc_btn, items, sel, editing):
        if editing:
            rotary.set(
                min_val=0,
                max_val=len(items) - 1,
                value=sel,
                incr=1,
                range_mode=rotary.RANGE_BOUNDED,
            )
        self.motor_run_state = False
        motor.set_state(motor.MOTOR_BRAKE, VOLTAGE_MIN_MV)

    def _on_short_press(self, motor, rotary, enc_btn, items, sel, editing):
        """Handle a confirmed short press. Returns the new editing state."""
        if editing:
            editing = False
            rotary.set(
                min_val=0,
                max_val=len(items) - 1,
                value=sel,
                incr=1,
                range_mode=rotary.RANGE_BOUNDED,
            )
            self._redraw_tiles(items, sel)
        else:
            if sel == 0:  # Direction Control
                self.manual_dir = (
                    Direction.REV if self.manual_dir == Direction.FWD else Direction.FWD
                )
                self._redraw_tiles(items, sel)
            elif sel == 1:  # Voltage Control
                editing = True
                rotary.set(
                    min_val=VOLTAGE_MIN_MV,
                    max_val=VOLTAGE_MAX_MV,
                    value=self.manual_vol_mv,
                    incr=100,  # Increments of 100mV
                    range_mode=rotary.RANGE_BOUNDED,
                )
                self._redraw_tiles(items, sel, editing=True)
            elif sel == 2:
                self.motor_run_state = not self.motor_run_state
                if self.motor_run_state:
                    self.manual_run_start = time.ticks_ms()
                self._redraw_tiles(items, sel)
        return editing

    def _handle_rotary(self, rotary, items, sel, prev_sel, editing):
        """Process rotary encoder movement. Returns updated (sel, prev_sel, editing)."""
        rv = rotary.value()
        if editing:
            if sel == 1 and rv != self.manual_vol_mv:
                self.manual_vol_mv = rv
                items[1][2].set_text(self._param_str("VOLT"))
        else:
            if rv != prev_sel:
                sel = rv
                prev_sel = sel
                self._redraw_tiles(items, sel)
        return sel, prev_sel, editing

    def _update_motor(self, motor):
        """Push state to motor driver only when something has changed."""
        if (
            self.motor_run_state != self._old_run_state
            or self.manual_dir != self._old_dir
            or self.manual_vol_mv != self._old_vol_mv
        ):
            self._old_run_state = self.motor_run_state
            self._old_dir = self.manual_dir
            self._old_vol_mv = self.manual_vol_mv

            if not self.motor_run_state:
                mode = motor.MOTOR_BRAKE
            elif self.manual_dir == Direction.FWD:
                mode = motor.MOTOR_FORWARD
            else:
                mode = motor.MOTOR_REVERSE

            motor.set_state(mode, self.manual_vol_mv)

        motor.update_state()
        motor.update_current_ma()
        motor.update_rpm()
        motor.update_temp()

    def _update_readouts(self, motor, v_rpm, v_timer, v_amps, v_temp, delay_ms):
        """Refresh all live-value labels only if they've changed and it's been more than delay ms since last update"""

        now = time.ticks_ms()
        if time.ticks_diff(now, self.previous_disp_update_time) > delay_ms:
            self.previous_disp_update_time = now

            current_ma = max(0, motor.get_current_1s())
            new_amps = f"{current_ma:.0f}mA"
            if new_amps != self._last_amps:
                self._last_amps = new_amps
                v_amps.set_text(new_amps)

            new_rpm = f"{motor.get_rpm_1s():d}"
            if new_rpm != self._last_rpm:
                self._last_rpm = new_rpm
                v_rpm.set_text(new_rpm)

            new_temp = f"{motor.get_temp_10s():.1f}°C"
            if new_temp != self._last_temp:
                self._last_temp = new_temp
                v_temp.set_text(new_temp)

            if self.manual_run_start is not None and self.motor_run_state:
                elapsed_s = (
                    time.ticks_diff(time.ticks_ms(), self.manual_run_start) // 1000
                )
                new_timer = f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}"
                if new_timer != self._last_timer:
                    self._last_timer = new_timer
                    v_timer.set_text(new_timer)
