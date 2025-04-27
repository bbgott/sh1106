# MicroPython SH1106 OLED Driver

A MicroPython driver for SH1106-based OLED displays, supporting both I2C and 4-wire SPI interfaces. This driver utilizes MicroPython's built-in `framebuf` library for efficient graphics drawing.

## Features

*   Supports SH1106 OLED controllers.
*   Implements drivers for I2C and 4-wire SPI communication.
*   Subclasses `framebuf.FrameBuffer` to provide standard graphics primitives (pixels, lines, rectangles, text, etc.).
*   Handles the SH1106's 132x64 GRAM size and automatically centers the display buffer (e.g., 128x64 or 64x48) within the GRAM.
*   Basic display control: power on/off, contrast adjustment, invert display.

## Requirements

*   A MicroPython-compatible microcontroller board (e.g., ESP32, ESP8266, Raspberry Pi Pico, Pyboard).
*   An SH1106-based OLED display module (common sizes: 128x64, 128x32, 64x48).
*   Appropriate physical connections (wiring) between the board and the display.
*   The provided driver code saved as a Python file on your board.

## Installation

1.  Save the provided Python code (everything from the beginning of this file up to the end) as a file named `sh1106.py` on your computer.
2.  Connect your MicroPython board to your computer.
3.  Use a tool like Thonny, rshell, or ampy to copy the `sh1106.py` file to the root directory of your MicroPython board's filesystem.

## Wiring

Connect your SH1106 display to your MicroPython board according to its pinout and whether you are using I2C or SPI.

**General I2C Wiring (Example Pins - Check your board's documentation):**

*   `VCC` -> `3.3V` or `5V` (check display requirements)
*   `GND` -> `GND`
*   `SCL` -> Board's I2C `SCL` pin
*   `SDA` -> Board's I2C `SDA` pin
*   (Optional `RES` pin may exist - connect to a GPIO and handle reset manually or leave unconnected if the module has auto-reset)

**General 4-Wire SPI Wiring (Example Pins - Check your board's documentation):**

*   `VCC` -> `3.3V` or `5V` (check display requirements)
*   `GND` -> `GND`
*   `SCK` -> Board's SPI `SCK` pin
*   `MOSI` (or `SDA`/`DIN`) -> Board's SPI `MOSI` pin
*   `RES` -> Board's GPIO pin (for hardware reset)
*   `DC` (or `A0`/`D/C`) -> Board's GPIO pin (Data/Command select)
*   `CS` -> Board's GPIO pin (Chip Select)
*   (`MISO` -> Leave unconnected as SH1106 is write-only via SPI)

## Usage

After copying `sh1106.py` to your board, you can import and use the appropriate class (`SH1106_I2C` or `SH1106_SPI`).

Replace pin numbers and interface configurations with those specific to your board and wiring.

### I2C Example (128x64 Display)

```python
from machine import Pin, I2C
import sh1106
import time

# Display dimensions
oled_width = 128
oled_height = 64

# ESP32 / ESP8266 / RP2040 common I2C pins (check your specific board)
# ESP32: SCL=22, SDA=21 (often)
# ESP8266: SCL=5, SDA=4 (often)
# RP2040: Configure any two I2C-capable GPIOs
i2c_scl = Pin(22) # Replace with your SCL pin
i2c_sda = Pin(21) # Replace with your SDA pin

# I2C interface (adjust frequency if needed, default is 400000)
i2c = I2C(0, scl=i2c_scl, sda=i2c_sda, freq=400000)

# Common I2C addresses for SH1106 are 0x3C or 0x3D
# You can use i2c.scan() to find the address if unsure.
oled_addr = 0x3C # Replace with your display's address if needed

# external_vcc = True if your display is powered by an external 3.3V or 5V source,
#                False if powered by the charge pump (most common for small modules)
external_power = False # Set according to your hardware

# Initialize the SH1106 display via I2C
oled = sh1106.SH1106_I2C(oled_width, oled_height, i2c, addr=oled_addr, external_vcc=external_power)

# Example Usage:

# Clear the display buffer
oled.fill(0)

# Draw some graphics
oled.text("MicroPython", 0, 0, 1) # Text at (0,0), color 1 (white)
oled.text("SH1106 Test", 0, 10, 1)
oled.line(0, 20, oled_width - 1, 20, 1) # Horizontal line
oled.rect(10, 30, 50, 20, 1) # Rectangle at (10,30), size 50x20, color 1

# Draw text using FrameBuffer's text method (supports font scaling)
# Note: Only supports 8x8 font.
# To use larger fonts, you would typically import and use a font rendering library.
oled.text("Framebuf", 0, 45, 1) # Another text example

# Copy the buffer to the display RAM
oled.show()

# Keep display on for a few seconds
time.sleep(5)

# Example of basic control
oled.contrast(0x80) # Set contrast to mid-level
oled.show()
time.sleep(2)

oled.invert(1) # Invert colors
oled.show()
time.sleep(2)

oled.invert(0) # Back to normal
oled.show()
time.sleep(2)

oled.poweroff() # Turn off the display
time.sleep(2)

oled.poweron() # Turn on the display
oled.show()
time.sleep(2)

# Clear everything
oled.fill(0)
oled.show()
```

### SPI Example (128x64 Display, 4-Wire)

```python
from machine import Pin, SPI
import sh1106
import time

# Display dimensions
oled_width = 128
oled_height = 64

# SPI pins (check your specific board and wiring)
# ESP32: SPI(1 or 2), SCK=18, MOSI=23, MISO=19 (common VSPI pins, MISO not used for SH1106)
# ESP8266: SPI(1), SCK=14, MOSI=13, MISO=12
# RP2040: SPI(0 or 1), SCK=2, MOSI=3 (example pins)
spi_sck = Pin(18) # Replace with your SCK pin
spi_mosi = Pin(23) # Replace with your MOSI pin
# spi_miso = Pin(19) # MISO is not used for SH1106, but might need definition for SPI init on some boards

# Control pins (replace with your chosen GPIOs)
oled_res = Pin(4) # Reset pin
oled_dc = Pin(16) # Data/Command pin
oled_cs = Pin(17) # Chip Select pin

# SPI interface (adjust baudrate, polarity, phase if needed)
# SH1106 SPI is Mode 0 (CPOL=0, CPHA=0)
# Baudrate up to 10MHz is common
spi = SPI(1, baudrate=10000000, sck=spi_sck, mosi=spi_mosi, polarity=0, phase=0)
# If your board requires MISO defined:
# spi = SPI(1, baudrate=10000000, sck=spi_sck, mosi=spi_mosi, miso=spi_miso, polarity=0, phase=0)


# external_vcc = True if your display is powered by an external 3.3V or 5V source,
#                False if powered by the charge pump (most common for small modules)
external_power = False # Set according to your hardware

# Initialize the SH1106 display via SPI
oled = sh1106.SH1106_SPI(oled_width, oled_height, spi, oled_dc, oled_res, oled_cs, external_vcc=external_power)

# Example Usage (Same as I2C example - FrameBuffer methods are the same):

# Clear the display buffer
oled.fill(0)

# Draw some graphics
oled.text("MicroPython", 0, 0, 1) # Text at (0,0), color 1 (white)
oled.text("SH1106 Test", 0, 10, 1)
oled.line(0, 20, oled_width - 1, 20, 1) # Horizontal line
oled.rect(10, 30, 50, 20, 1) # Rectangle at (10,30), size 50x20, color 1

oled.text("Framebuf", 0, 45, 1) # Another text example

# Copy the buffer to the display RAM
oled.show()

# Keep display on for a few seconds
time.sleep(5)

# Example of basic control
oled.contrast(0x80) # Set contrast to mid-level
oled.show()
time.sleep(2)

oled.invert(1) # Invert colors
oled.show()
time.sleep(2)

oled.invert(0) # Back to normal
oled.show()
time.sleep(2)

oled.poweroff() # Turn off the display
time.sleep(2)

oled.poweron() # Turn on the display
oled.show()
time.sleep(2)

# Clear everything
oled.fill(0)
oled.show()
```

## API Reference

The `SH1106_I2C` and `SH1106_SPI` classes inherit from `SH1106`, which in turn inherits from `framebuf.FrameBuffer`.

**Methods Inherited/Available:**

*   `oled = SH1106_I2C(width, height, i2c, addr=0x3C, external_vcc=False)`: Initialize I2C driver.
    *   `width`, `height`: Display resolution in pixels (e.g., 128, 64).
    *   `i2c`: Configured `machine.I2C` object.
    *   `addr`: I2C address of the display (default is 0x3C).
    *   `external_vcc`: Set to `True` if the display's VCC is powered externally, `False` (default) if using the internal charge pump.
*   `oled = SH1106_SPI(width, height, spi, dc, res, cs, external_vcc=False)`: Initialize SPI driver.
    *   `width`, `height`: Display resolution in pixels.
    *   `spi`: Configured `machine.SPI` object.
    *   `dc`: `machine.Pin` object for the Data/Command (D/C) pin.
    *   `res`: `machine.Pin` object for the Reset (RES) pin.
    *   `cs`: `machine.Pin` object for the Chip Select (CS) pin.
    *   `external_vcc`: Same as I2C version.
*   `oled.show()`: Transfer the contents of the internal framebuffer to the display's GRAM to update the screen. **Must be called after drawing!**
*   `oled.poweroff()`: Turn the display off (low power mode).
*   `oled.poweron()`: Turn the display on.
*   `oled.contrast(contrast)`: Set the display contrast (0-255, where 255 is maximum).
*   `oled.invert(invert)`: Invert the display colors (`invert=0` for normal, `invert=1` for inverted).
*   **All `framebuf.FrameBuffer` methods:**
    *   `oled.fill(c)`: Fill the entire buffer with color `c` (0 for black, 1 for white).
    *   `oled.pixel(x, y, c)`: Set pixel at `(x, y)` to color `c`.
    *   `oled.hline(x, y, w, c)`: Draw a horizontal line.
    *   `oled.vline(x, y, h, c)`: Draw a vertical line.
    *   `oled.line(x1, y1, x2, y2, c)`: Draw a line between `(x1, y1)` and `(x2, y2)`.
    *   `oled.rect(x, y, w, h, c)`: Draw a rectangle outline.
    *   `oled.fill_rect(x, y, w, h, c)`: Draw a filled rectangle.
    *   `oled.text(string, x, y, c)`: Draw 8x8 pixel text.

## Notes and Limitations

*   The SH1106 controller has a GRAM resolution of 132x64. This driver automatically centers your specified `width` (e.g., 128) within the 132 columns during the `show()` operation.
*   The driver assumes a standard 64-pixel height for page calculations. While it allows instantiation with other heights (`height != SH1106_GRAM_HEIGHT`), the mapping of pages in the `show()` method is optimized for the common case where the display height matches the number of used pages (e.g., 64 height = 8 pages). For displays with height significantly different from 64 (e.g., 32), the current `show()` logic might need slight adjustments to correctly map the framebuffer pages to the required GRAM pages and column offsets.
*   The `framebuf` used is `MONO_VLSB`.
*   The SPI interface requires 4 wires (SCK, MOSI, DC, CS) plus power and ground. A Reset pin is also required by this driver's initialization sequence.
