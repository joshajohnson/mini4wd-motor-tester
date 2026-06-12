import lvgl as lv

from ui_common import (
    UIBase,
    DISP_WIDTH,
    DISP_HEIGHT,
    MARGIN,
    COL_BCKGND,
    COL_TILE,
    COL_BORDER,
    COL_TEXT,
    COL_SEL_TEXT,
    COL_MANUAL,
    COL_BREAK_IN,
    COL_SPEED_TEST,
    COL_SETTINGS,
)
from ui_manual import ManualScreen
from ui_speed import SpeedScreen


class UI(UIBase):
    """
    Top-level UI controller for the Mini 4WD Motor Tester.

    Requires an initialised ST7735 display (st7735_display.ST7735).

    Example:
        import st7735_display, ui
        display = st7735_display.ST7735()
        app = ui.UI(display)
        app.show_menu(motor, rotary, enc_btn, wheel_sensor)
    """

    def __init__(self, display):
        super().__init__(display)
        self._manual = ManualScreen(display)
        self._speed = SpeedScreen(display)
        self._cursor_index = 0

    def show_menu(self, motor, rotary, enc_btn, wheel_sensor):
        """
        Main menu — 2×2 grid
        [Manual]     [Break-in]
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

            tiles, tile_syms, tile_lbls = [], [], []

            for idx, (name, symbol, _) in enumerate(MENU_ITEMS):
                col = idx % 2
                row = idx // 2
                tx = MARGIN + col * (TILE_W + MARGIN)
                ty = MARGIN + row * (TILE_H + MARGIN)

                tile = lv.obj(scrn)
                tile.set_size(TILE_W, TILE_H)
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

            rotary.set(
                min_val=0,
                max_val=len(MENU_ITEMS) - 1,
                value=self._cursor_index,
                range_mode=rotary.RANGE_BOUNDED,
            )
            prev_selected = -1

            while True:
                new_val = rotary.value()
                if new_val != prev_selected:
                    self._cursor_index = new_val
                    prev_selected = self._cursor_index
                    for i, (_, _, sel_col) in enumerate(MENU_ITEMS):
                        if i == self._cursor_index:
                            tiles[i].set_style_bg_color(sel_col, 0)
                            tiles[i].set_style_border_width(0, 0)
                            tile_syms[i].set_style_text_color(COL_SEL_TEXT, 0)
                            tile_lbls[i].set_style_text_color(COL_SEL_TEXT, 0)
                        else:
                            tiles[i].set_style_bg_color(COL_TILE, 0)
                            tiles[i].set_style_border_width(1, 0)
                            tile_syms[i].set_style_text_color(COL_TEXT, 0)
                            tile_lbls[i].set_style_text_color(COL_TEXT, 0)

                enc_btn.read()
                if enc_btn.get_state() == enc_btn.PRESSING:
                    self._wait_btn_release(enc_btn)
                    break

                motor.update_state()

            if self._cursor_index == 0:
                self._manual.show(motor, rotary, enc_btn)
            elif self._cursor_index == 1:
                self._show_breakin(motor, rotary, enc_btn)
            elif self._cursor_index == 2:
                self._speed.show(wheel_sensor, enc_btn)
            elif self._cursor_index == 3:
                self._show_settings(rotary, enc_btn)

    def _show_breakin(self, motor, rotary, enc_btn):
        self._show_placeholder("Break In", enc_btn)

    def _show_settings(self, rotary, enc_btn):
        self._show_placeholder("Settings", enc_btn)
