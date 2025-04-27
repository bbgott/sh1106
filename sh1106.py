# MicroPython SH1106 OLED driver, I2C and SPI interfaces

import framebuf
import time
from micropython import const

# SH1106 Commands
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20) # Sets addressing mode
# SH1106 uses Set Lower Column Address (00-0F) and Set Higher Column Address (10-1F)
# instead of Set Column Address range (21) used by SSD1306
SET_LOWER_COL_ADDR = const(0x00)
SET_HIGHER_COL_ADDR = const(0x10)
# SH1106 uses Set Page Address (B0-B7) instead of Set Page Address range (22)
SET_PAGE_ADDR = const(0xB0) # Use with OR | page_number (0-7)

SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0) # A0 = normal, A1 = remapped
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0) # C0 = normal, C8 = remapped
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

# SH1106 specific GRAM size
SH1106_GRAM_WIDTH = const(132)
SH1106_GRAM_HEIGHT = const(64) # Always 64 pages/height in GRAM

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SH1106(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        # SH1106 GRAM is always 132x64
        if self.height != SH1106_GRAM_HEIGHT:
             # Currently only supporting full 64-height panels, though width can vary
             # More complex logic needed for partial height displays.
             # For now, assume display height is always 64 for standard drivers
             # or that the framebuf height matches the portion of GRAM used.
             # For common 128x64 displays, this check passes.
             # If you have a e.g. 128x32 display with SH1106, this needs adjustment.
             print("Warning: SH1106 GRAM height is always 64. Display height may not match.")
             # We calculate pages based on display height, not GRAM height,
             # as framebuf is sized to display, not GRAM.
             # The show() method must correctly map pages to GRAM.
             # Assuming framebuf height is multiple of 8.
             pass # Allow non 64 height, but warn. show() logic needs page mapping review.

        self.external_vcc = external_vcc
        self.pages = self.height // 8 # Number of pages in the FrameBuffer
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        # SH1106 Initialization Sequence (adapted from SSD1306 and datasheet)
        # Datasheet commands match SSD1306 for the most part, except for addressing
        # which is handled in the show() method.
        for cmd in (
            SET_DISP | 0x00,  # 0xAE: off
            # address setting (Horizontal Addressing Mode is standard)
            SET_MEM_ADDR, 0x00, # 0x20, 0x00
            # resolution and layout
            SET_DISP_START_LINE | 0x00, # 0x40: start line 0
            # Set Segment Re-map (A0h or A1h) - A1h (0x01) is common for many modules, matches SSD1306 default
            SET_SEG_REMAP | 0x01, # 0xA1: column addr 127 mapped to SEG0 (matches many modules)
            # Set Multiplex Ratio (A8h) - parameter N-1 (64-1=63=0x3F for 64 height)
            SET_MUX_RATIO, self.height - 1, # 0xA8, height-1
            # Set COM Output Scan Direction (C0h or C8h) - C8h (0x08) is common for many modules, matches SSD1306 default
            SET_COM_OUT_DIR | 0x08, # 0xC8: scan from COM[N] to COM0 (matches many modules)
            # Set Display Offset (D3h)
            SET_DISP_OFFSET, 0x00, # 0xD3, 0x00
            # Set COM Pins Hardware Configuration (DAh) - Parameter varies (0x02 or 0x12)
            # Check logic from SSD1306 - 0x02 for 128x32, 0x12 for 128x64 or 96x16?
            # Datasheet suggests 0x02 for width > 2*height. This seems like a heuristic.
            # Common values are 0x02 (sequential COM) or 0x12 (alternative COM)
            # Let's stick to 0x12 as it's common for 128x64 panels
            SET_COM_PIN_CFG, 0x12, # 0xDA, 0x12 (Alternative COM pin configuration)

            # timing and driving scheme
            # Set Display Clock Divide Ratio / Oscillator Frequency (D5h)
            SET_DISP_CLK_DIV, 0x80, # 0xD5, 0x80 (Divide ratio 1, Fosc)
            # Set Pre-charge Period (D9h) - parameters depend on Vcc
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1, # 0xD9, 0x22 or 0xF1
            # Set VCOM Deselect Level (DBh)
            SET_VCOM_DESEL, 0x30,  # 0xDB, 0x30 (0.83*Vcc)

            # display
            SET_CONTRAST, 0xFF,  # 0x81, 0xFF (maximum contrast)
            SET_ENTIRE_ON,  # 0xA4: output follows RAM contents
            SET_NORM_INV,  # 0xA6: not inverted

            # charge pump
            # Set Charge Pump Setting (8Dh) - parameters depend on Vcc
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14, # 0x8D, 0x10 or 0x14

            SET_DISP | 0x01, # 0xAF: on
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        """Turn the display off."""
        self.write_cmd(SET_DISP | 0x00) # AEh

    def poweron(self):
        """Turn the display on."""
        self.write_cmd(SET_DISP | 0x01) # AFh

    def contrast(self, contrast):
        """Set the display contrast (0-255)."""
        self.write_cmd(SET_CONTRAST) # 81h
        self.write_cmd(contrast)     # 00h-FFh

    def invert(self, invert):
        """Invert the display (0=normal, 1=inverted)."""
        self.write_cmd(SET_NORM_INV | (invert & 1)) # A6h or A7h

    def show(self):
        """Copy the frame buffer to the display's GRAM."""
        # SH1106 GRAM is 132x64. Common displays are 128x64, 96x16, 64x48 etc.
        # We need to calculate the column offset to center the display buffer
        # within the 132 columns of the SH1106 GRAM.
        # Offset = (GRAM_WIDTH - DISPLAY_WIDTH) // 2
        col_offset = (SH1106_GRAM_WIDTH - self.width) // 2

        # SH1106 uses page-by-page addressing for data transfer in Horizontal Mode
        # Set Page Address (B0h to B7h for pages 0-7)
        # Set Lower Column Address (00h to 0Fh)
        # Set Higher Column Address (10h to 1Fh)
        # Then write the data for that page.
        for page in range(self.pages):
            # Set Page Address
            self.write_cmd(SET_PAGE_ADDR | page) # B0h | page
            # Set Starting Column Address
            # Lower 4 bits of start_col
            self.write_cmd(SET_LOWER_COL_ADDR | (col_offset & 0x0F)) # 00h | (offset & 0x0F)
            # Higher 4 bits of start_col, command is 10h + (higher bits)
            self.write_cmd(SET_HIGHER_COL_ADDR | (col_offset >> 4)) # 10h | (offset >> 4)

            # Write data for the current page (self.width bytes per page)
            # The data is contiguous in the buffer for the current page
            self.write_data(self.buffer[page * self.width : (page + 1) * self.width])


# I2C Interface
class SH1106_I2C(SH1106):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        # Buffer for sending command/data prefix + byte (I2C only)
        self.temp = bytearray(2)
        # List for writevto: [command_prefix, data_buffer]
        # Data write prefix: Co=0, D/C#=1 (0x40)
        self.write_list = [b"\x40", None]
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        """Write a single command byte over I2C."""
        # Command write prefix: Co=1, D/C#=0 (0x80) - Although datasheet says Co=1,
        # standard drivers often use Co=0 for single command byte transfer.
        # Let's use the common 0x00 prefix for commands (Co=0, D/C#=0).
        # If writing multiple commands, use 0x80 (Co=1, D/C#=0)
        # For simplicity and compatibility with many SSD1306 libraries, use 0x00 for single commands.
        # Datasheet page 13/14 seems to imply 0x00 (Co=0, D/C=0) for first byte, 0x80 (Co=1, D/C=0) for subsequent.
        # Let's stick to 0x00 for single commands as it's more widely compatible with existing codebases.
        self.temp[0] = 0x00 # Co=0, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        """Write a buffer of data bytes over I2C."""
        # Data write prefix: Co=0, D/C#=1 (0x40) - For multiple data bytes, Co=1 is more efficient (0xC0)
        # But standard framebuf data write is often preceded by 0x40 for simplicity.
        # Let's use 0x40 as it's common and works.
        self.write_list[1] = buf
        # writevto is more efficient for writing prefix + data buffer
        self.i2c.writevto(self.addr, self.write_list)


# SPI Interface (4-wire)
class SH1106_SPI(SH1106):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        # Recommended SPI baudrate (can be adjusted)
        self.rate = 10 * 1024 * 1024
        # Setup control pins (DC, RES, CS)
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)

        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs

        # Perform hardware reset sequence (as shown in datasheet p.32/33/44)
        self.res(1)
        time.sleep_ms(1) # t1 timing (min 10us)
        self.res(0)
        time.sleep_ms(10) # t2 timing (min 12us for low pulse width)
        self.res(1)
        time.sleep_ms(100) # t3 timing (about 100ms needed after reset before commands, see power-on sequence)

        # Initialize the display using the base class init_display
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        """Write a single command byte over SPI."""
        # Select SPI interface (CS low)
        self.cs(1) # Ensure high before selecting
        # Set DC low for command
        self.dc(0)
        self.cs(0) # Select chip
        # Initialize SPI with desired settings (baudrate, polarity, phase)
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        # Write the command byte
        self.spi.write(bytearray([cmd]))
        # Deselect SPI interface (CS high)
        self.cs(1)

    def write_data(self, buf):
        """Write a buffer of data bytes over SPI."""
        # Select SPI interface (CS low)
        self.cs(1) # Ensure high before selecting
        # Set DC high for data
        self.dc(1)
        self.cs(0) # Select chip
        # Initialize SPI with desired settings
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        # Write the data buffer
        self.spi.write(buf)
        # Deselect SPI interface (CS high)
        self.cs(1)