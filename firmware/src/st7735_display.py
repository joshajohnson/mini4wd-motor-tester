import lcd_bus
from micropython import const
import machine
import st7735
import lvgl as lv

class ST7735:

    '''
    MicroPython Driver for the ST7735 TFT LCD Display.
    Using https://github.com/lvgl-micropython/lvgl_micropython, not the LVGL library as it's stale

    Assumes the display is on it's own SPI bus, and not shared with other devices.

    NOTE: if running init after the display is already initialized, it will not re-initialize the display.
    You'll have to power cycle the unit, or run import machine; machine.reset() to hard reset the micro. 

    Example:

    display = st7735_display.ST7735()
    display.demo()
    
    '''

    def __init__(self, width: int = 128, height: int = 160, 
                rst_pin: int = 7, dc_pin: int = 10, 
                spi_host: int = 1, mosi_pin: int = 11, sck_pin: int = 12, cs_pin: int = 14, 
                freq: int = 2000000):
        
        self.width = width
        self.height = height
        self.rst_pin = rst_pin
        self.dc_pin = dc_pin
        self.spi_host = spi_host
        self.mosi_pin = mosi_pin
        self.sck_pin = sck_pin
        self.cs_pin = cs_pin
        self.freq = freq

        self.offset_x = 1
        self.offset_y = 2

        self.spi_bus = machine.SPI.Bus(host=self.spi_host, mosi=self.mosi_pin, sck=self.sck_pin)

        self.display_bus = lcd_bus.SPIBus(spi_bus=self.spi_bus, freq=self.freq, dc=self.dc_pin, cs=self.cs_pin)

        self.display = st7735.ST7735(
        data_bus=self.display_bus,
        display_width=self.width,
        display_height=self.height,
        reset_pin=self.rst_pin,
        reset_state=st7735.STATE_LOW,
        color_space=lv.COLOR_FORMAT.RGB565,
        color_byte_order=st7735.BYTE_ORDER_BGR,
        rgb565_byte_swap=True,
        offset_x=self.offset_x,
        offset_y=self.offset_y)

        lv.init()

        self.display.init(st7735.TYPE_R_GREEN)
        self.display.set_rotation(lv.DISPLAY_ROTATION._90)

    def demo(self):
        '''
        A simple demo to show the display works and can be updated.
        NOTE: this is a blocking function, and will brick your micro if you don't CTRL + C out of the loop!
        '''

        print("WARNING: Running demo will block the microcontroller. Press CTRL + C to exit the demo loop.")
        print("If run a second time without power cycling, text will overlap.")
        print("Furthermore, for some reson it'll brick the micro if you don't CTRL + C prior to killing power.")      

        scrn = lv.screen_active()
        scrn.set_style_bg_color(lv.color_hex(0xff0000), 0)

        label = lv.label(scrn)
        label.set_text('HELLO WORLD!')
        label.set_style_text_color(lv.color_hex(0xffffff), 0)
        label.align(lv.ALIGN.CENTER, 0, 30)

        # Draw a rectangle
        rect1 = lv.obj(scrn)
        rect1.set_size(10, 10)
        rect1.set_style_bg_color(lv.color_hex(0x00aa00), 0)
        rect1.set_style_border_color(lv.color_hex(0xffffff), 0)
        rect1.set_style_border_width(1, 0)
        rect1.set_style_radius(0, 0)
        rect1.align(lv.ALIGN.TOP_LEFT, 0, 0)

        rect2 = lv.obj(scrn)
        rect2.set_size(10, 10)
        rect2.set_style_bg_color(lv.color_hex(0xaa0000), 0)
        rect2.set_style_border_color(lv.color_hex(0xffffff), 0)
        rect2.set_style_border_width(1, 0)
        rect2.set_style_radius(0, 0)
        rect2.align(lv.ALIGN.TOP_RIGHT, 0, 0)

        rect3 = lv.obj(scrn)
        rect3.set_size(10, 10)
        rect3.set_style_bg_color(lv.color_hex(0xaa00aa), 0)
        rect3.set_style_border_color(lv.color_hex(0xffffff), 0)
        rect3.set_style_border_width(1, 0)
        rect3.set_style_radius(0, 0)
        rect3.align(lv.ALIGN.BOTTOM_RIGHT, 0, 0)

        rect4 = lv.obj(scrn)
        rect4.set_size(10, 10)
        rect4.set_style_bg_color(lv.color_hex(0x0000aa), 0)
        rect4.set_style_border_color(lv.color_hex(0xffffff), 0)
        rect4.set_style_border_width(1, 0)
        rect4.set_style_radius(0, 0)
        rect4.align(lv.ALIGN.BOTTOM_LEFT, 0, 0)

        # Draw a circle
        circle = lv.obj(scrn)
        circle.set_size(50, 50)
        circle.set_style_bg_color(lv.color_hex(0x0000ff), 0)
        circle.set_style_border_color(lv.color_hex(0xff00ff), 0)
        circle.set_style_border_width(3, lv.STATE.DEFAULT)
        circle.set_style_radius(25, 0)  # Make it circular (radius = half of width/height)
        circle.align(lv.ALIGN.CENTER, 0, -10)

        import time

        lv.task_handler()
        # Show init text for a few seconds before starting the counter display
        time.sleep_ms(10000) 

        time_passed = 1000
        counter = 0

        while True:
            start_time = time.ticks_ms()
            time.sleep_ms(1)  # sleep for 1 ms
            lv.tick_inc(time_passed)
            lv.task_handler()

            end_time = time.ticks_ms()
            time_passed = time.ticks_diff(end_time, start_time)
            counter = counter + 1
            label.set_text(str(counter/1000))

