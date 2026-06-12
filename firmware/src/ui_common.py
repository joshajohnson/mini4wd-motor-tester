import time
import lvgl as lv


# ────────────────────────────── Enums ────────────────────────────────────
class Direction:
    FWD = 1
    REV = 2


# ────────────────────── Constants for all screens ───────────────────────

HOLD_MS = 800

VOLTAGE_MIN_MV = 500
VOLTAGE_MAX_MV = 3000

CURRENT_LIM_MIN_MA = 100
CURRENT_LIM_MAX_MA = 2000

TEMP_LIM_MIN_C = 20
TEMP_LIM_MAX_C = 50

# TODO: add these to eeprom so they are persistent
VOLTAGE_DEFAULT_MV = 1500
CURRENT_LIM_DEFAULT_MA = 500
TEMP_LIM_DEFAULT_C = 40

# TODO: add these to eeprom so they are persistent
# [dir, vol_x10, dur_30, cool_30]
BREAK_IN_STEPS = [
    [Direction.FWD, 15, 2, 2],
    [Direction.REV, 15, 2, 2],
    [Direction.FWD, 15, 2, 2],
    [Direction.REV, 15, 2, 2],
    [Direction.FWD, 15, 2, 2],
]

# ────────────────────── Display / Colours ──────────────────────────

# Dimensions
DISP_WIDTH = 160
DISP_HEIGHT = 128
MARGIN = 2

# Delay on how frequently we update live values
VALUE_UPDATE_MS = 200

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


class UIBase:
    """
    Shared LVGL helpers inherited by all screen classes.
    Not instantiated directly.
    """

    def __init__(self, display):
        self.display = display

    def _clear_screen(self):
        """Remove all LVGL children from the active screen."""
        scrn = lv.screen_active()
        while scrn.get_child_count() > 0:
            scrn.get_child(0).delete()

    def _make_tile(self, scrn, x, y, w, h):
        t = lv.obj(scrn)
        t.set_size(w, h)
        t.set_pos(x, y)
        t.set_style_bg_color(COL_BCKGND, 0)
        t.set_style_border_color(COL_BORDER, 0)
        t.set_style_border_width(1, 0)
        t.set_style_radius(3, 0)
        t.set_style_pad_all(2, 0)
        return t

    def _tile_key(self, tile, text):
        k = lv.label(tile)
        k.set_text(text)
        k.set_style_text_color(COL_TEXT, 0)
        k.set_style_text_font(lv.font_montserrat_12, 0)
        k.align(lv.ALIGN.LEFT_MID, 0, 0)
        return k

    def _tile_val(self, tile, text):
        v = lv.label(tile)
        v.set_text(text)
        v.set_style_text_color(COL_TEXT, 0)
        v.set_style_text_font(lv.font_montserrat_12, 0)
        v.align(lv.ALIGN.RIGHT_MID, 0, 0)
        return v

    def _wait_btn_release(self, enc_btn):
        """Block until button is released to prevent double-triggering."""
        while True:
            enc_btn.read()
            if enc_btn.get_state() == enc_btn.IDLE:
                break
            time.sleep_ms(10)

    def _update_back_bar(self, fill, enc_btn, pressed_ms):
        """
        Call every loop tick to handle the back-bar fill and long-press
        detection.  Returns the updated press_start timestamp:
          - 0   → not pressed / timed out
          - -1  → long-press threshold reached (caller should return)
          - -2  → short-press released (caller should handle selection)
          - >0  → still holding, bar updated
        Pass pressed_ms=0 when not pressed.
        """
        enc_btn.read()
        if (
            enc_btn._prev_state == enc_btn.IDLE
            and enc_btn.get_state() == enc_btn.PRESSING
        ):
            return time.ticks_ms()
        elif enc_btn.get_state() == enc_btn.PRESSING and pressed_ms > 0:
            elapsed = time.ticks_diff(time.ticks_ms(), pressed_ms)
            fill.set_width(max(1, int(DISP_WIDTH * min(elapsed, HOLD_MS) / HOLD_MS)))
            if elapsed >= HOLD_MS:
                fill.set_width(DISP_WIDTH)
                return -1
            return pressed_ms
        elif (
            enc_btn._prev_state == enc_btn.PRESSING
            and enc_btn.get_state() == enc_btn.IDLE
        ):
            fill.set_width(0)
            if pressed_ms > 0:
                return -2
            return 0
        return pressed_ms

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

    def _show_placeholder(self, title, enc_btn):
        self._clear_screen()
        scrn = lv.screen_active()
        scrn.set_style_bg_color(COL_BCKGND, 0)

        header = lv.label(scrn)
        header.set_text(title)
        header.set_style_text_color(COL_TEXT, 0)
        header.set_style_text_font(lv.font_montserrat_16, 0)
        header.align(lv.ALIGN.TOP_MID, 0, 10)

        lbl = lv.label(scrn)
        lbl.set_text("Coming Soon...")
        lbl.set_style_text_color(COL_TEXT, 0)
        lbl.set_style_text_font(lv.font_montserrat_12, 0)
        lbl.align(lv.ALIGN.CENTER, 0, 0)

        hint = lv.label(scrn)
        hint.set_text("Hold button to go back")
        hint.set_style_text_color(COL_TEXT, 0)
        hint.set_style_text_font(lv.font_montserrat_12, 0)
        hint.align(lv.ALIGN.BOTTOM_MID, 0, -10)

        back_fill = self._make_back_bar(scrn)

        pressed_ms = 0
        while True:
            pressed_ms = self._update_back_bar(back_fill, enc_btn, pressed_ms)
            if pressed_ms == -1:
                self._wait_btn_release(enc_btn)
                return
