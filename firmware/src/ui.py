import lvgl as lv
import time

class UI:
    '''
    All application UI screens for the Mini 4WD Motor Tester.

    Requires an initialised ST7735 display (st7735_display.ST7735) to be
    passed in; the display driver handles hardware initialisation and LVGL
    setup before this class is used.

    Example:
        import st7735_display, ui
        display = st7735_display.ST7735()
        app = ui.UI(display)
        app.show_menu(psu, tmp, motor, rotary, enc_btn)
    '''

   # LONG HOLD THRESHOLD
    HOLD_MS = 800

    # VOLTAGE SET LIMITS
    VOLTAGE_DEFAULT_MV = 1500
    VOLTAGE_MIN_MV = 500
    VOLTAGE_MAX_MV = 3000

    # CURRENT TRIP LIMITS
    CURRENT_DEFAULT_10 = 10  # 1A default trip
    CURRENT_MIN_10 = 1  # 100mA min trip current
    CURRENT_MAX_10 = 20  # 2A max trip current

    # TEMP TRIP LIMITS
    TEMP_DEFAULT_C = 40
    TEMP_MIN_C = 20
    TEMP_MAX_C = 50

    # DEFAULT BREAK IN ARRAY
    # TODO: SAVE THE BELOW TO EEPROM BETWEEN POWER CYCLES
    # [dir_fwd, vol_10, dur_30, cool_30]
    BREAK_IN_STEPS = [
        [True, 15, 2, 2],
        [False, 15, 2, 2],
        [True, 15, 2, 2],
        [False, 15, 2, 2],
        [True, 15, 2, 2],
    ]

    # Global Colours
    COL_TILE     = lv.color_white()
    COL_TEXT     = lv.color_black()
    COL_SEL_TEXT = lv.color_white()
    COL_BCKGND   = lv.palette_lighten(lv.PALETTE.GREY,4)
    COL_BORDER   = lv.palette_lighten(lv.PALETTE.GREY,1)
    COL_BACK_BAR = lv.palette_main(lv.PALETTE.BLUE_GREY)

    # Page Colours
    COL_MANUAL = lv.palette_darken(lv.PALETTE.RED,2)
    COL_BREAK_IN = lv.palette_darken(lv.PALETTE.BLUE, 2)
    COL_SPEED_TEST = lv.palette_darken(lv.PALETTE.TEAL, 2)
    COL_SETTINGS = lv.palette_darken(lv.PALETTE.AMBER, 2)

    def __init__(self, display):
        self.display  = display
        self.cur_10 = [self.CURRENT_DEFAULT_10]
        self.tmp_c = [self.TEMP_DEFAULT_C]
        # Manual motor screen persisted values
        self.manual_dir_fwd = True
        self.manual_vol_10  = self.VOLTAGE_DEFAULT_MV / 100  

    # ─────────────────────────── LVGL helpers ────────────────────────────

    def _clear_screen(self):
        '''Remove all LVGL children from the active screen.'''
        scrn = lv.screen_active()
        while scrn.get_child_count() > 0:
            scrn.get_child(0).delete()
        lv.tick_inc(10)
        lv.task_handler()

    def _wait_btn_release(self, enc_btn):
        '''Block until button is released to prevent double-triggering.'''
        
        while True:
            enc_btn.read()
            if enc_btn._state == enc_btn.IDLE:
                break
            lv.tick_inc(10)
            lv.task_handler()
            time.sleep_ms(10)

    def _make_back_bar(self, scrn):
        '''
        Add the long-press progress bar to a screen.
        Returns the fill object whose width is updated by the caller.
        '''

        track = lv.obj(scrn)
        track.set_size(160, 2)
        track.set_pos(0, 0)
        track.set_style_bg_color(self.COL_BACK_BAR, 0)
        track.set_style_border_width(0, 0)
        track.set_style_radius(0, 0)
        track.set_style_pad_all(0, 0)

        fill = lv.obj(scrn)
        fill.set_size(1, 2)
        fill.set_pos(0, 0)
        fill.set_style_bg_color(self.COL_BACK_BAR, 0)
        fill.set_style_border_width(0, 0)
        fill.set_style_radius(0, 0)
        fill.set_style_pad_all(0, 0)

        return fill

    def _update_back_bar(self, fill, enc_btn, ps):
        '''
        Call every loop tick to handle the back-bar fill and long-press
        detection.  Returns the updated press_start timestamp:
          - 0        → not pressed / timed out
          - -1       → long-press threshold reached (caller should return)
          - >0       → still holding, bar updated
        Pass ps=0 when not pressed.
        '''
        
        enc_btn.read()
        if enc_btn._prev_state == enc_btn.IDLE and enc_btn._state == enc_btn.PRESSING:
            return time.ticks_ms()
        elif enc_btn._state == enc_btn.PRESSING and ps > 0:
            elapsed = time.ticks_diff(time.ticks_ms(), ps)
            fill.set_width(max(1, int(160 * min(elapsed, self.HOLD_MS) / self.HOLD_MS)))
            if elapsed >= self.HOLD_MS:
                fill.set_width(1)
                return -1
            return ps
        elif enc_btn._prev_state == enc_btn.PRESSING and enc_btn._state == enc_btn.IDLE:
            fill.set_width(1)
            return 0
        return ps

    # ──────────────────────────── Main menu ──────────────────────────────

    def show_menu(self, psu, motor, tmp, rotary, enc_btn, wheel_sensor):
        self._psu = psu
        self._motor = motor
        self._tmp = tmp
        self._wheel_sensor = wheel_sensor
        '''
        Main menu — 2×2 tile grid.
        Navigate with rotary encoder, short-press to select.
        Loops forever, returning to the menu after each sub-screen exits.
        '''

        MENU_ITEMS = [
            ('Manual',     lv.SYMBOL.PLAY,     self.COL_MANUAL),
            ('Break-in',   lv.SYMBOL.REFRESH,  self.COL_BREAK_IN),
            ('Speed Test', lv.SYMBOL.CHARGE,   self.COL_SPEED_TEST),
            ('Settings',   lv.SYMBOL.SETTINGS, self.COL_SETTINGS),
        ]

        MARGIN = 3
        GAP    = 3
        TILE_W = (160 - 2 * MARGIN - GAP) // 2   # 75
        TILE_H = (128 - 2 * MARGIN - GAP) // 2   # 61

        while True:
            self._clear_screen()
            scrn = lv.screen_active()
            scrn.set_style_bg_color(self.COL_BCKGND, 0)

            tiles     = []
            tile_syms = []
            tile_lbls = []

            # Display 2x2 grid of items
            for idx in range(len(MENU_ITEMS)):
                name, symbol, sel_col = MENU_ITEMS[idx]
                col = idx % 2
                row = idx // 2

                tx = MARGIN + col * (TILE_W + GAP)
                tw = TILE_W

                ty = MARGIN + row * (TILE_H + GAP)

                tile = lv.obj(scrn)
                tile.set_size(tw, TILE_H)
                tile.set_pos(tx, ty)
                tile.set_style_bg_color(self.COL_TILE, 0)
                tile.set_style_border_color(self.COL_BORDER, 0)
                tile.set_style_border_width(1, 0)
                tile.set_style_radius(3, 0)
                tile.set_style_pad_all(0, 0)
                tiles.append(tile)

                sym = lv.label(tile)
                sym.set_text(symbol)
                sym.set_style_text_color(self.COL_TEXT, 0)
                sym.align(lv.ALIGN.CENTER, 0, -10)
                tile_syms.append(sym)

                lbl = lv.label(tile)
                lbl.set_text(name)
                lbl.set_style_text_color(self.COL_TEXT, 0)
                lbl.set_style_text_font(lv.font_montserrat_12, 0)
                lbl.align(lv.ALIGN.CENTER, 0, 10)
                tile_lbls.append(lbl)

            # Config encoder to be bounded at extremes of menu
            rotary.set(min_val=0, max_val=len(MENU_ITEMS) - 1, value=0, range_mode=rotary.RANGE_BOUNDED)
            selected      = 0
            prev_selected = -1

            lv.tick_inc(10)
            lv.task_handler()

            # When the encoder moves, highlight the selected menu item
            while True:
                new_val = rotary.value()
                if new_val != prev_selected:
                    selected      = new_val
                    prev_selected = selected
                    for i in range(len(MENU_ITEMS)):
                        if i == selected:
                            tiles[i].set_style_bg_color((MENU_ITEMS[i][2]), 0)
                            tiles[i].set_style_border_width(0, 0)
                            tile_syms[i].set_style_text_color(self.COL_SEL_TEXT, 0)
                            tile_lbls[i].set_style_text_color(self.COL_SEL_TEXT, 0)
                        else:
                            tiles[i].set_style_bg_color(self.COL_TILE, 0)
                            tiles[i].set_style_border_width(1, 0)
                            tile_syms[i].set_style_text_color(self.COL_TEXT, 0)
                            tile_lbls[i].set_style_text_color(self.COL_TEXT, 0)
                    lv.tick_inc(5)
                    lv.task_handler()

                enc_btn.read()
                if enc_btn._state == enc_btn.PRESSING:
                    self._wait_btn_release(enc_btn)
                    break

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

    