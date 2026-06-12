import time
import lvgl as lv

# ────────────────────── Constants for all screens ───────────────────────

# LONG HOLD THRESHOLD
HOLD_MS = 800

# VOLTAGE SET LIMITS
VOLTAGE_MIN_MV = 500
VOLTAGE_MAX_MV = 3000

# CURRENT TRIP LIMITS
CURRENT_MIN_10 = 1  # 100mA min trip current
CURRENT_MAX_10 = 20  # 2A max trip current

# TEMP TRIP LIMITS
TEMP_MIN_C = 20
TEMP_MAX_C = 50

# USER SET DEFAULTS
# TODO: add these to eeprom so they are persistent
VOLTAGE_DEFAULT_MV = 1000
CURRENT_DEFAULT_10 = 10  # 1A default trip
TEMP_DEFAULT_C = 40

# DEFAULT BREAK IN ARRAY
# TODO: add these to eeprom so they are persistent
# [dir_fwd, vol_x10, dur_30, cool_30]
BREAK_IN_STEPS = [
    [True, 15, 2, 2],
    [False, 15, 2, 2],
    [True, 15, 2, 2],
    [False, 15, 2, 2],
    [True, 15, 2, 2],
]

# DISPLAY DIMENSIONS
DISP_WIDTH = 160
DISP_HEIGHT = 128
MARGIN = 2

# Global Colours
COL_TILE = lv.color_white()
COL_TEXT = lv.color_black()
COL_SEL_TEXT = lv.color_white()
COL_EDIT_TEXT = lv.palette_darken(lv.PALETTE.GREY, 4)
COL_BCKGND = lv.palette_lighten(lv.PALETTE.GREY, 4)
COL_SEL_BCKGND = lv.palette_darken(lv.PALETTE.INDIGO, 2)
COL_EDIT_BCKGND = lv.palette_darken(lv.PALETTE.INDIGO, 4)
COL_BORDER = lv.palette_lighten(lv.PALETTE.GREY, 1)
COL_BACK_BAR = lv.palette_main(lv.PALETTE.BLUE)

# Page Colours
COL_MANUAL = lv.palette_darken(lv.PALETTE.RED, 2)
COL_BREAK_IN = lv.palette_darken(lv.PALETTE.BLUE, 2)
COL_SPEED_TEST = lv.palette_darken(lv.PALETTE.TEAL, 2)
COL_SETTINGS = lv.palette_darken(lv.PALETTE.AMBER, 2)


class UI:
    """
    All application UI screens for the Mini 4WD Motor Tester.

    Requires an initialised ST7735 display (st7735_display.ST7735) to be
    passed in; the display driver handles hardware initialisation and LVGL
    setup before this class is used.

    Example:
        import st7735_display, ui
        display = st7735_display.ST7735()
        app = ui.UI(display)
        app.show_menu(psu, tmp, motor, rotary, enc_btn)
    """

    def __init__(self, display):
        self.display = display
        # Trip limits
        self.cur_10 = CURRENT_DEFAULT_10
        self.tmp_c = TEMP_DEFAULT_C
        # Manual mode
        # Defaults
        self.motor_run_state = False
        self.manual_dir_fwd = True
        self.manual_vol_x10 = VOLTAGE_DEFAULT_MV / 100
        # State Control
        self.old_motor_run_state = self.motor_run_state
        self.old_manual_dir_fwd = self.manual_dir_fwd
        self.old_manual_vol_x10 = self.manual_vol_x10
        self.manual_run_start = None

    # ─────────────────────────── LVGL helpers ────────────────────────────

    def _clear_screen(self):
        """Remove all LVGL children from the active screen."""
        scrn = lv.screen_active()
        while scrn.get_child_count() > 0:
            scrn.get_child(0).delete()
        lv.tick_inc(10)
        lv.task_handler()

    def _wait_btn_release(self, enc_btn):
        """Block until button is released to prevent double-triggering."""

        while True:
            enc_btn.read()
            if enc_btn.get_state() == enc_btn.IDLE:
                break
            lv.tick_inc(10)
            lv.task_handler()
            time.sleep_ms(10)

    def _make_back_bar(self, scrn):
        """
        Add the long-press progress bar to a screen.
        Returns the fill object whose width is updated by the caller.
        """

        fill = lv.obj(scrn)
        fill.set_size(1, 2)
        fill.set_pos(0, 0)
        fill.set_style_bg_color(COL_BACK_BAR, 0)
        fill.set_style_border_width(0, 0)
        fill.set_style_radius(0, 0)
        fill.set_style_pad_all(0, 0)

        return fill

    def _update_back_bar(self, fill, enc_btn, press_ms):
        """
        Call every loop tick to handle the back-bar fill and long-press
        detection.  Returns the updated press_start timestamp:
          - 0        -> not pressed / timed out
          - -1       -> long-press threshold reached (caller should return)
          - >0       -> still holding, bar updated
        Pass press_ms=0 when not pressed.
        """

        enc_btn.read()
        if (
            enc_btn.get_prev_state() == enc_btn.IDLE
            and enc_btn.get_state() == enc_btn.PRESSING
        ):
            return time.ticks_ms()
        elif enc_btn.get_state() == enc_btn.PRESSING and press_ms > 0:
            elapsed = time.ticks_diff(time.ticks_ms(), press_ms)
            fill.set_width(max(1, int(DISP_WIDTH * min(elapsed, HOLD_MS) / HOLD_MS)))
            if elapsed >= HOLD_MS:
                fill.set_width(1)
                return -1
            return press_ms
        elif (
            enc_btn.get_prev_state() == enc_btn.PRESSING
            and enc_btn.get_state() == enc_btn.IDLE
        ):
            fill.set_width(1)
            return 0
        return press_ms

    # ──────────────────────────── Main menu ──────────────────────────────

    def show_menu(self, psu, motor, tmp, rotary, enc_btn, wheel_sensor):
        """
        Main menu — 2×2 grid
        [Manual] [Break-in]
        [Speed Test] [Settings]
        """

        MENU_ITEMS = [
            ("Manual", lv.SYMBOL.PLAY, COL_MANUAL),
            ("Break-in", lv.SYMBOL.REFRESH, COL_BREAK_IN),
            ("Speed Test", lv.SYMBOL.CHARGE, COL_SPEED_TEST),
            ("Settings", lv.SYMBOL.SETTINGS, COL_SETTINGS),
        ]

        TILE_W = int((DISP_WIDTH - 2 * MARGIN - MARGIN) // 2)
        TILE_H = int((DISP_HEIGHT - 2 * MARGIN - MARGIN) // 2)

        while True:
            self._clear_screen()
            scrn = lv.screen_active()
            scrn.set_style_bg_color(COL_BCKGND, 0)

            tiles = []
            tile_syms = []
            tile_lbls = []

            # Display 2x2 grid of items
            for idx in range(len(MENU_ITEMS)):
                name, symbol, sel_col = MENU_ITEMS[idx]
                col = idx % 2
                row = idx // 2

                tx = MARGIN + col * (TILE_W + MARGIN)
                tw = TILE_W

                ty = MARGIN + row * (TILE_H + MARGIN)

                tile = lv.obj(scrn)
                tile.set_size(tw, TILE_H)
                tile.set_pos(tx, ty)
                tile.set_style_bg_color(COL_TILE, 0)
                tile.set_style_border_color(COL_BORDER, 0)
                tile.set_style_border_width(1, 0)
                tile.set_style_radius(3, 0)
                tile.set_style_pad_all(0, 0)
                tiles.append(tile)

                sym = lv.label(tile)
                sym.set_text(symbol)
                sym.set_style_text_color(COL_TEXT, 0)
                sym.align(lv.ALIGN.CENTER, 0, -10)
                tile_syms.append(sym)

                lbl = lv.label(tile)
                lbl.set_text(name)
                lbl.set_style_text_color(COL_TEXT, 0)
                lbl.set_style_text_font(lv.font_montserrat_12, 0)
                lbl.align(lv.ALIGN.CENTER, 0, 10)
                tile_lbls.append(lbl)

            # Config encoder to be bounded at extremes of menu
            rotary.set(
                min_val=0,
                max_val=len(MENU_ITEMS) - 1,
                value=0,
                range_mode=rotary.RANGE_BOUNDED,
            )
            selected = 0
            prev_selected = -1

            lv.tick_inc(10)
            lv.task_handler()

            # When the encoder moves, highlight the selected menu item
            while True:
                new_val = rotary.value()
                if new_val != prev_selected:
                    selected = new_val
                    prev_selected = selected
                    for i in range(len(MENU_ITEMS)):
                        if i == selected:
                            tiles[i].set_style_bg_color((MENU_ITEMS[i][2]), 0)
                            tiles[i].set_style_border_width(0, 0)
                            tile_syms[i].set_style_text_color(COL_SEL_TEXT, 0)
                            tile_lbls[i].set_style_text_color(COL_SEL_TEXT, 0)
                        else:
                            tiles[i].set_style_bg_color(COL_TILE, 0)
                            tiles[i].set_style_border_width(1, 0)
                            tile_syms[i].set_style_text_color(COL_TEXT, 0)
                            tile_lbls[i].set_style_text_color(COL_TEXT, 0)
                    lv.tick_inc(5)
                    lv.task_handler()

                enc_btn.read()
                if enc_btn.get_state() == enc_btn.PRESSING:
                    self._wait_btn_release(enc_btn)
                    break

                motor.update_state()  # If the user exits a lower screen we want to continue the ramp down of the motor
                lv.tick_inc(20)
                lv.task_handler()

            # Call the menu items when selected
            if selected == 0:
                self._show_manual_motor(psu, tmp, motor, rotary, enc_btn)
            elif selected == 1:
                self._show_breakin(psu, tmp, motor, rotary, enc_btn)
            elif selected == 2:
                self._show_speed_test(rotary, enc_btn, wheel_sensor)
            elif selected == 3:
                self._show_settings(rotary, enc_btn)

    # ──────────────────────── Manual motor test ──────────────────────────

    def _show_manual_motor(self, psu, tmp, motor, rotary, enc_btn):
        """
        Manual motor test screen

        Row 0: [RPM]          : read-only live value
        Row 1: [AMPS]         : read-only live value
        Row 2: [TIMER]        : read-only live value
        Row 3: [DIR] | [VOLT] : nav0 | nav 1
        Row 5: [START/STOP]   : nav 2
        """

        TILE_H = 22

        # ── Helpers ───────────────────────────────────────────────────────
        def make_tile(x, y, w, h):
            t = lv.obj(scrn)
            t.set_size(w, h)
            t.set_pos(x, y)
            t.set_style_bg_color(COL_BCKGND, 0)
            t.set_style_border_color(COL_BORDER, 0)
            t.set_style_border_width(1, 0)
            t.set_style_radius(3, 0)
            t.set_style_pad_all(2, 0)
            return t

        def tile_key(tile, text):
            k = lv.label(tile)
            k.set_text(text)
            k.set_style_text_color(COL_TEXT, 0)
            k.set_style_text_font(lv.font_montserrat_12, 0)
            k.align(lv.ALIGN.LEFT_MID, 0, 0)
            return k

        def tile_val(tile, text):
            v = lv.label(tile)
            v.set_text(text)
            v.set_style_text_color(COL_TEXT, 0)
            v.set_style_text_font(lv.font_montserrat_12, 0)
            v.align(lv.ALIGN.RIGHT_MID, 0, 0)
            return v

        def param_str(idx):
            if idx == "DIR":
                return "FWD" if self.manual_dir_fwd else "REV"
            if idx == "VOLT":
                return "{:.1f}V".format(self.manual_vol_x10 / 10)
            return ""

        # ── GUI Setup ──────────────────────────────────────────────────
        self._clear_screen()
        scrn = lv.screen_active()
        scrn.set_style_bg_color(COL_BCKGND, 0)
        back_fill = self._make_back_bar(scrn)

        # Row 0: RPM
        t_rpm = make_tile(MARGIN, 2 * MARGIN, DISP_WIDTH - 2 * MARGIN, TILE_H)
        k_rpm = tile_key(t_rpm, "RPM")
        v_rpm = tile_val(t_rpm, "---")

        # Row 1: AMPS
        t_amps = make_tile(
            MARGIN, 2 * MARGIN + 1 * (MARGIN + TILE_H), DISP_WIDTH - 2 * MARGIN, TILE_H
        )
        k_amps = tile_key(t_amps, "CURRENT")
        v_amps = tile_val(t_amps, "---")

        # Row 2: TIMER
        t_timer = make_tile(
            MARGIN, 2 * MARGIN + 2 * (MARGIN + TILE_H), DISP_WIDTH - 2 * MARGIN, TILE_H
        )
        k_timer = tile_key(t_timer, "TIMER")
        v_timer = tile_val(t_timer, "-:--")

        # Row 3: DIR | VOLT
        t_dir = make_tile(
            MARGIN,
            2 * MARGIN + 3 * (MARGIN + TILE_H),
            int((DISP_WIDTH - 3 * MARGIN) / 2),
            TILE_H,
        )
        k_dir = tile_key(t_dir, "DIR")
        v_dir = tile_val(t_dir, param_str("DIR"))
        t_volt = make_tile(
            int((DISP_WIDTH - 3 * MARGIN) / 2) + 2 * MARGIN,
            2 * MARGIN + 3 * (MARGIN + TILE_H),
            int((DISP_WIDTH - 3 * MARGIN) / 2),
            TILE_H,
        )
        k_volt = tile_key(t_volt, "VOLT")
        v_volt = tile_val(t_volt, param_str("VOLT"))

        # Row 4: START / STOP button
        t_start_stop = make_tile(
            MARGIN,
            2 * MARGIN + 4 * (MARGIN + TILE_H),
            DISP_WIDTH - 2 * MARGIN,
            DISP_HEIGHT - (3 * MARGIN + 4 * (MARGIN + TILE_H)),
        )
        v_start_stop = lv.label(t_start_stop)
        v_start_stop.set_text(lv.SYMBOL.PLAY + " START")
        v_start_stop.set_style_text_color(COL_TEXT, 0)
        v_start_stop.set_style_text_font(lv.font_montserrat_14, 0)
        v_start_stop.align(lv.ALIGN.CENTER, 0, 0)

        MANUAL_ITEMS = [
            (t_dir, k_dir, v_dir),
            (t_volt, k_volt, v_volt),
            (t_start_stop, None, v_start_stop),
        ]

        # Sets background and text colour of the selected cell
        def set_tile_state(idx, state):
            tile, key, val = MANUAL_ITEMS[idx][0:]
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

        # Updates tile value and colour
        def redraw_tiles(sel, editing=False):
            # Last field (play / pause) is an outlier, handle seperately
            for i in range(len(MANUAL_ITEMS) - 1):
                set_tile_state(
                    i,
                    (
                        "editing"
                        if (i == sel and editing)
                        else "selected" if i == sel else "normal"
                    ),
                )
            MANUAL_ITEMS[0][2].set_text(param_str("DIR"))
            MANUAL_ITEMS[1][2].set_text(param_str("VOLT"))
            MANUAL_ITEMS[2][2].set_text(
                lv.SYMBOL.PLAY + " START"
                if not self.motor_run_state
                else lv.SYMBOL.PAUSE + " PAUSE"
            )
            set_tile_state(2, "selected" if sel == 2 else "normal")
            lv.tick_inc(5)
            lv.task_handler()

        # Post GUI setup super loop
        while True:
            for i in range(len(MANUAL_ITEMS)):
                set_tile_state(i, "normal")

            rotary.set(
                min_val=0,
                max_val=len(MANUAL_ITEMS) - 1,
                value=2,
                range_mode=rotary.RANGE_BOUNDED,
            )
            # Defaulting to 2, which is start/stop
            sel = 2
            prev_sel = -1
            editing = False
            press_ms = 0
            set_tile_state(2, "selected")

            lv.tick_inc(1)
            lv.task_handler()

            # Supeloop of editing fields and updating the motor call functions
            while True:
                enc_btn.read()
                if (
                    enc_btn.get_prev_state() == enc_btn.IDLE
                    and enc_btn.get_state() == enc_btn.PRESSING
                ):
                    press_ms = time.ticks_ms()
                elif enc_btn.get_state() == enc_btn.PRESSING and press_ms > 0:
                    elapsed = time.ticks_diff(time.ticks_ms(), press_ms)
                    back_fill.set_width(
                        max(1, int(DISP_WIDTH * min(elapsed, HOLD_MS) / HOLD_MS))
                    )
                    # User has exited the manual screen, return to main menu
                    if elapsed >= HOLD_MS:
                        back_fill.set_width(DISP_WIDTH)
                        if editing:
                            rotary.set(
                                min_val=0,
                                max_val=len(MANUAL_ITEMS) - 1,
                                value=sel,
                                range_mode=rotary.RANGE_BOUNDED,
                            )
                        self._wait_btn_release(enc_btn)
                        # Stop the motor running
                        self.motor_run_state = False
                        # Brake on exit, extra safety just in case the above does not trip the disable conditional
                        motor.set_state(motor.MOTOR_BRAKE, VOLTAGE_MIN_MV / 1000)
                        return
                elif (
                    enc_btn.get_prev_state() == enc_btn.PRESSING
                    and enc_btn.get_state() == enc_btn.IDLE
                    and press_ms > 0
                ):
                    # User let go before HOLD_MS, so they wanted to select a field
                    elapsed = time.ticks_diff(time.ticks_ms(), press_ms)
                    press_ms = 0
                    back_fill.set_width(0)
                    if elapsed < HOLD_MS:
                        if editing:
                            editing = False
                            rotary.set(
                                min_val=0,
                                max_val=len(MANUAL_ITEMS) - 1,
                                value=sel,
                                range_mode=rotary.RANGE_BOUNDED,
                            )
                            redraw_tiles(sel)
                        else:
                            # Toggle between forward and reverse
                            if sel == 0:
                                self.manual_dir_fwd = not self.manual_dir_fwd
                                redraw_tiles(sel)
                            # Adjust voltage in 100mV steps
                            elif sel == 1:
                                editing = True
                                rotary.set(
                                    min_val=VOLTAGE_MIN_MV / 100,
                                    max_val=VOLTAGE_MAX_MV / 100,
                                    value=self.manual_vol_x10,
                                    range_mode=rotary.RANGE_BOUNDED,
                                )
                                redraw_tiles(sel, editing=True)
                            # Toggle motor run state
                            elif sel == 2:
                                self.motor_run_state = not self.motor_run_state

                                if self.motor_run_state is True:
                                    self.manual_run_start = time.ticks_ms()

                                redraw_tiles(sel)

                rv = rotary.value()
                if editing:
                    changed = False
                    if sel == 1 and rv != self.manual_vol_x10:
                        self.manual_vol_x10 = rv
                        changed = True
                    if changed:
                        if sel == 0:
                            string = "DIR"
                        elif sel == 1:
                            string = "VOLT"
                        MANUAL_ITEMS[sel][2].set_text(param_str(string))
                        lv.tick_inc(5)
                        lv.task_handler()
                else:
                    if rv != prev_sel:
                        sel = rv
                        prev_sel = sel
                        redraw_tiles(sel)

                # Only call the set_state function if something has changed
                if (
                    self.motor_run_state != self.old_motor_run_state
                    or self.manual_dir_fwd != self.old_manual_dir_fwd
                    or self.manual_vol_x10 != self.old_manual_vol_x10
                ):
                    self.old_motor_run_state = self.motor_run_state
                    self.old_manual_dir_fwd = self.manual_dir_fwd
                    self.old_manual_vol_x10 = self.manual_vol_x10

                    # Direction Control:
                    if self.motor_run_state is False:
                        mode = motor.MOTOR_BRAKE
                    elif self.manual_dir_fwd is True:
                        mode = motor.MOTOR_FORWARD
                    else:
                        mode = motor.MOTOR_REVERSE

                    motor.set_state(mode, self.manual_vol_x10 / 10)

                # With the state set, update all the things
                # motor.update_state() expects to be called every ms to handle ramping and direction changes
                motor.update_state()
                motor.update_current()
                motor.update_rpm()

                # When motor is off, noise can sometimes show current as negative. Don't want to confuse the user
                current_ma = motor.get_current_1s() * 1000
                if current_ma < 1:
                    current_ma = 0

                # Update live readouts in tiles
                v_amps.set_text(f"{current_ma:.0f}mA")
                v_rpm.set_text(f"{motor.get_rpm_1s():d}")

                # Elapsed time, this only resets on the start / stop, not on direction / voltage changes
                if self.manual_run_start is not None and self.motor_run_state is True:
                    elapsed_ms = time.ticks_diff(time.ticks_ms(), self.manual_run_start)
                    elapsed_s = elapsed_ms // 1000
                    v_timer.set_text(f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}")

                lv.tick_inc(2)
                lv.task_handler()
