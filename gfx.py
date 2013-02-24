import os, sys
import fcntl, mmap, struct
from time import sleep



class Bitfield:
	def __init__(self, offset, length, msb_right):
		self.offset = offset
		self.length = length
		self.msb_right = msb_right

# http://www.pygame.org/docs/ref/rect.html
class Rect:
	def __init__(self, left, top, width, height):
		self.left = left
		self.top = top
		self.width = width
		self. height = height


# http://www.pygame.org/docs/ref/draw.html
class Draw:
	def __init__(self, fb):
		self.fb = fb

	def rect(self, color, rect, width=0):
		if (width==0):
			for y in range(rect.top, rect.top + rect.height):
				self.fb.hline(rect.left, y, rect.width, color)
		else:
			self.line(color, (rect.left, rect.top), (rect.left + rect.width, rect.top))
			self.line(color, (rect.left, rect.top + rect.height), (rect.left + rect.width, rect.top + rect.height))
			self.line(color, (rect.left, rect.top), (rect.left, rect.top + rect.height))
			self.line(color, (rect.left + rect.width, rect.top), (rect.left + rect.width, rect.top + rect.height))

	# line(rgb(32,0,0), (10,10), (50,50))
	def line(self, color, start_pos, end_pos, width=1):
#		if (start_pos[0] > end_pos[0]):
#			tmp = end_pos
#			end_pos = start_pos
#			start_pos = tmp

#		print "line(%s, %r, %r)" % (hex(color), start_pos, end_pos)

		# vertical ?
		if (end_pos[0] - start_pos[0]) == 0:
			for i in range(start_pos[1], end_pos[1]+1):
				self.fb.putpixel(start_pos[0], i, color)
			return
		
		# horizontal ?
		if (end_pos[1] - start_pos[1]) == 0:
			self.fb.hline(start_pos[0], start_pos[1], end_pos[0] - start_pos[0], color)
#			for i in range(start_pos[0], end_pos[0]+1):
#				self.fb.putpixel(i, start_pos[1], color)
			return
		
		m = (end_pos[1] - start_pos[1]) / float(end_pos[0] - start_pos[0])
		if (end_pos[0] == 0):
			b = end_pos[1]
		elif (end_pos[1] == 0):
			b = -m * end_pos[0]
		else:
			b = 1.0 * end_pos[1] / (m*end_pos[0])

#		print "%sx + %s = y" % (m,b)

		for i in range(start_pos[0], end_pos[0]+1):
			print "%s,%s" % (i, int(round(m*i+b)))
			self.fb.putpixel(i, \
			int(round(m*i+b)), \
			color)


# Kind of like a pygame Surface object, or not!
# http://www.pygame.org/docs/ref/surface.html
class BaseGFX:
	
	def putpixel(self, x, y, color):
#		print "\nputpixel(%s, %s, %r)" % (x,y,bin(color))
		if (x < 0 or x > self.xres-1):
			raise ValueError("Illegal x value: %r" % x)
		if (y < 0 or y > self.yres-1):
			raise ValueError("Illegal y value: %r" % y)

		if (self.bits_per_pixel == 1):
			bitoffset = x + (y * self.line_length * 8)
			byteoffset = bitoffset / 8

			self.fbp.seek(byteoffset)
			byte = struct.unpack("B", self.fbp.read_byte())[0]
#			print "  byteoffset: %r" % byteoffset
#			print "  byte: %r" % bin(byte)
			
			if (color == 0):
				byte &= ~(1 << (7-(bitoffset % 8)))
			else:
#				print "  bitoffset: %r" % bitoffset
#				print "  bit pos: %r"  % (7-(bitoffset % 8))
#				print "  bit mask: %r" % bin(1 << (7-(bitoffset % 8)))
				byte |= (1 << (7-(bitoffset % 8)))
			self.fbp.seek(byteoffset)
			self.fbp.write(struct.pack("B", byte))

		elif (self.bits_per_pixel == 16):
			offset = ((x + self.xoffset) * self.bytes_per_pixel
					+ (y + self.yoffset) * self.line_length)
			self.fbp.seek(offset)
			self.fbp.write(struct.pack("H", color))
		else:
			raise ValueError("%s bits per pixel is not supported" % self.bits_per_pixel)

	def hline(self, x, y, length, color):
		if (x < 0 or x > self.xres-1):
			raise ValueError("Illegal x value: %r" % x)
		if (y < 0 or y > self.yres-1):
			raise ValueError("Illegal y value: %r" % y)

#		if (self.bits_per_pixel == 1):
#			pass
#		elif (self.bits_per_pixel == 16):
		if (self.bits_per_pixel == 16):
			colstr = struct.pack("H", color)
			offset = ((x + self.xoffset) * self.bytes_per_pixel
					+ (y + self.yoffset) * self.line_length)
			self.fbp.seek(offset)
			for i in range(0, length):
				self.fbp.write(colstr)
		else:
			for i in range(x, x+length):
				self.putpixel(i, y, color)

	def fill(self, color):
		if (self.bits_per_pixel == 1):
			if (color == 0):
				buf = self.screensize*'\x00'
			else:
				buf = self.screensize*'\xFF'
			self.fbp.seek(0)
			self.fbp.write(buf)
		elif (self.bits_per_pixel == 16):
			colstr = struct.pack("H", color)
			buf = ''
			self.fbp.seek(0)
			for i in range(0, self.screensize/2):
				buf += colstr
			self.fbp.write(buf)
		else:
			for y in range(0, self.yres):
				self.hline(0, y, self.xres, color)

	def putchar(self, x, y, ascii, color, size=1):
		font = ascii_5x7_font(ascii)
		for dx in range(0,5):
			line = font[dx]
			for dy in range(0,8):
				if (line & 1):
					if (size == 1):
						self.putpixel(x+dx, y+dy, color)
					else:
						self.draw.rect(color, Rect(x+(dx*size), y+(dy*size), size, size), 0)
				line >>= 1
		return (x+(size*6), y)

	def putstr(self, x, y, str, color, size=1):
		if (x == -1):
			x = (self.xres - self.str_width(str)*size) / 2
		if (y == -1):
			y = (self.yres - 8*size) / 2
		for c in str:
			(x, y) = self.putchar(x, y, ord(c), color, size)

	def str_width(self, str, size=1):
		return len(str)*6*size

	def str_height(self, str, size=1):
		return 8*size

	def rgb(self, r, b, g):
		if (self.red.length == 0 and self.green.length == 0 and self.blue.length == 0):
			if (r == 0 and b == 0 and g == 0):
				return 0
			else:
				return 1
		else:
			return ((r & ((1 << self.red.length)-1)) << self.red.offset) | ((b & ((1 << self.green.length)-1)) << self.green.offset) | ((g & ((1 << self.blue.length)-1)) << self.blue.offset)





# Source: https://github.com/adafruit/Adafruit-GFX-Library/blob/master/glcdfont.c
def ascii_5x7_font(c):
	fontarray = [
	0x00, 0x00, 0x00, 0x00, 0x00, 
	0x3E, 0x5B, 0x4F, 0x5B, 0x3E, 
	0x3E, 0x6B, 0x4F, 0x6B, 0x3E, 
	0x1C, 0x3E, 0x7C, 0x3E, 0x1C, 
	0x18, 0x3C, 0x7E, 0x3C, 0x18, 
	0x1C, 0x57, 0x7D, 0x57, 0x1C, 
	0x1C, 0x5E, 0x7F, 0x5E, 0x1C, 
	0x00, 0x18, 0x3C, 0x18, 0x00, 
	0xFF, 0xE7, 0xC3, 0xE7, 0xFF, 
	0x00, 0x18, 0x24, 0x18, 0x00, 
	0xFF, 0xE7, 0xDB, 0xE7, 0xFF, 
	0x30, 0x48, 0x3A, 0x06, 0x0E, 
	0x26, 0x29, 0x79, 0x29, 0x26, 
	0x40, 0x7F, 0x05, 0x05, 0x07, 
	0x40, 0x7F, 0x05, 0x25, 0x3F, 
	0x5A, 0x3C, 0xE7, 0x3C, 0x5A, 
	0x7F, 0x3E, 0x1C, 0x1C, 0x08, 
	0x08, 0x1C, 0x1C, 0x3E, 0x7F, 
	0x14, 0x22, 0x7F, 0x22, 0x14, 
	0x5F, 0x5F, 0x00, 0x5F, 0x5F, 
	0x06, 0x09, 0x7F, 0x01, 0x7F, 
	0x00, 0x66, 0x89, 0x95, 0x6A, 
	0x60, 0x60, 0x60, 0x60, 0x60, 
	0x94, 0xA2, 0xFF, 0xA2, 0x94, 
	0x08, 0x04, 0x7E, 0x04, 0x08, 
	0x10, 0x20, 0x7E, 0x20, 0x10, 
	0x08, 0x08, 0x2A, 0x1C, 0x08, 
	0x08, 0x1C, 0x2A, 0x08, 0x08, 
	0x1E, 0x10, 0x10, 0x10, 0x10, 
	0x0C, 0x1E, 0x0C, 0x1E, 0x0C, 
	0x30, 0x38, 0x3E, 0x38, 0x30, 
	0x06, 0x0E, 0x3E, 0x0E, 0x06, 
	0x00, 0x00, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x5F, 0x00, 0x00, 
	0x00, 0x07, 0x00, 0x07, 0x00, 
	0x14, 0x7F, 0x14, 0x7F, 0x14, 
	0x24, 0x2A, 0x7F, 0x2A, 0x12, 
	0x23, 0x13, 0x08, 0x64, 0x62, 
	0x36, 0x49, 0x56, 0x20, 0x50, 
	0x00, 0x08, 0x07, 0x03, 0x00, 
	0x00, 0x1C, 0x22, 0x41, 0x00, 
	0x00, 0x41, 0x22, 0x1C, 0x00, 
	0x2A, 0x1C, 0x7F, 0x1C, 0x2A, 
	0x08, 0x08, 0x3E, 0x08, 0x08, 
	0x00, 0x80, 0x70, 0x30, 0x00, 
	0x08, 0x08, 0x08, 0x08, 0x08, 
	0x00, 0x00, 0x60, 0x60, 0x00, 
	0x20, 0x10, 0x08, 0x04, 0x02, 
	0x3E, 0x51, 0x49, 0x45, 0x3E, 
	0x00, 0x42, 0x7F, 0x40, 0x00, 
	0x72, 0x49, 0x49, 0x49, 0x46, 
	0x21, 0x41, 0x49, 0x4D, 0x33, 
	0x18, 0x14, 0x12, 0x7F, 0x10, 
	0x27, 0x45, 0x45, 0x45, 0x39, 
	0x3C, 0x4A, 0x49, 0x49, 0x31, 
	0x41, 0x21, 0x11, 0x09, 0x07, 
	0x36, 0x49, 0x49, 0x49, 0x36, 
	0x46, 0x49, 0x49, 0x29, 0x1E, 
	0x00, 0x00, 0x14, 0x00, 0x00, 
	0x00, 0x40, 0x34, 0x00, 0x00, 
	0x00, 0x08, 0x14, 0x22, 0x41, 
	0x14, 0x14, 0x14, 0x14, 0x14, 
	0x00, 0x41, 0x22, 0x14, 0x08, 
	0x02, 0x01, 0x59, 0x09, 0x06, 
	0x3E, 0x41, 0x5D, 0x59, 0x4E, 
	0x7C, 0x12, 0x11, 0x12, 0x7C, 
	0x7F, 0x49, 0x49, 0x49, 0x36, 
	0x3E, 0x41, 0x41, 0x41, 0x22, 
	0x7F, 0x41, 0x41, 0x41, 0x3E, 
	0x7F, 0x49, 0x49, 0x49, 0x41, 
	0x7F, 0x09, 0x09, 0x09, 0x01, 
	0x3E, 0x41, 0x41, 0x51, 0x73, 
	0x7F, 0x08, 0x08, 0x08, 0x7F, 
	0x00, 0x41, 0x7F, 0x41, 0x00, 
	0x20, 0x40, 0x41, 0x3F, 0x01, 
	0x7F, 0x08, 0x14, 0x22, 0x41, 
	0x7F, 0x40, 0x40, 0x40, 0x40, 
	0x7F, 0x02, 0x1C, 0x02, 0x7F, 
	0x7F, 0x04, 0x08, 0x10, 0x7F, 
	0x3E, 0x41, 0x41, 0x41, 0x3E, 
	0x7F, 0x09, 0x09, 0x09, 0x06, 
	0x3E, 0x41, 0x51, 0x21, 0x5E, 
	0x7F, 0x09, 0x19, 0x29, 0x46, 
	0x26, 0x49, 0x49, 0x49, 0x32, 
	0x03, 0x01, 0x7F, 0x01, 0x03, 
	0x3F, 0x40, 0x40, 0x40, 0x3F, 
	0x1F, 0x20, 0x40, 0x20, 0x1F, 
	0x3F, 0x40, 0x38, 0x40, 0x3F, 
	0x63, 0x14, 0x08, 0x14, 0x63, 
	0x03, 0x04, 0x78, 0x04, 0x03, 
	0x61, 0x59, 0x49, 0x4D, 0x43, 
	0x00, 0x7F, 0x41, 0x41, 0x41, 
	0x02, 0x04, 0x08, 0x10, 0x20, 
	0x00, 0x41, 0x41, 0x41, 0x7F, 
	0x04, 0x02, 0x01, 0x02, 0x04, 
	0x40, 0x40, 0x40, 0x40, 0x40, 
	0x00, 0x03, 0x07, 0x08, 0x00, 
	0x20, 0x54, 0x54, 0x78, 0x40, 
	0x7F, 0x28, 0x44, 0x44, 0x38, 
	0x38, 0x44, 0x44, 0x44, 0x28, 
	0x38, 0x44, 0x44, 0x28, 0x7F, 
	0x38, 0x54, 0x54, 0x54, 0x18, 
	0x00, 0x08, 0x7E, 0x09, 0x02, 
	0x18, 0xA4, 0xA4, 0x9C, 0x78, 
	0x7F, 0x08, 0x04, 0x04, 0x78, 
	0x00, 0x44, 0x7D, 0x40, 0x00, 
	0x20, 0x40, 0x40, 0x3D, 0x00, 
	0x7F, 0x10, 0x28, 0x44, 0x00, 
	0x00, 0x41, 0x7F, 0x40, 0x00, 
	0x7C, 0x04, 0x78, 0x04, 0x78, 
	0x7C, 0x08, 0x04, 0x04, 0x78, 
	0x38, 0x44, 0x44, 0x44, 0x38, 
	0xFC, 0x18, 0x24, 0x24, 0x18, 
	0x18, 0x24, 0x24, 0x18, 0xFC, 
	0x7C, 0x08, 0x04, 0x04, 0x08, 
	0x48, 0x54, 0x54, 0x54, 0x24, 
	0x04, 0x04, 0x3F, 0x44, 0x24, 
	0x3C, 0x40, 0x40, 0x20, 0x7C, 
	0x1C, 0x20, 0x40, 0x20, 0x1C, 
	0x3C, 0x40, 0x30, 0x40, 0x3C, 
	0x44, 0x28, 0x10, 0x28, 0x44, 
	0x4C, 0x90, 0x90, 0x90, 0x7C, 
	0x44, 0x64, 0x54, 0x4C, 0x44, 
	0x00, 0x08, 0x36, 0x41, 0x00, 
	0x00, 0x00, 0x77, 0x00, 0x00, 
	0x00, 0x41, 0x36, 0x08, 0x00, 
	0x02, 0x01, 0x02, 0x04, 0x02, 
	0x3C, 0x26, 0x23, 0x26, 0x3C, 
	0x1E, 0xA1, 0xA1, 0x61, 0x12, 
	0x3A, 0x40, 0x40, 0x20, 0x7A, 
	0x38, 0x54, 0x54, 0x55, 0x59, 
	0x21, 0x55, 0x55, 0x79, 0x41, 
	0x21, 0x54, 0x54, 0x78, 0x41, 
	0x21, 0x55, 0x54, 0x78, 0x40, 
	0x20, 0x54, 0x55, 0x79, 0x40, 
	0x0C, 0x1E, 0x52, 0x72, 0x12, 
	0x39, 0x55, 0x55, 0x55, 0x59, 
	0x39, 0x54, 0x54, 0x54, 0x59, 
	0x39, 0x55, 0x54, 0x54, 0x58, 
	0x00, 0x00, 0x45, 0x7C, 0x41, 
	0x00, 0x02, 0x45, 0x7D, 0x42, 
	0x00, 0x01, 0x45, 0x7C, 0x40, 
	0xF0, 0x29, 0x24, 0x29, 0xF0, 
	0xF0, 0x28, 0x25, 0x28, 0xF0, 
	0x7C, 0x54, 0x55, 0x45, 0x00, 
	0x20, 0x54, 0x54, 0x7C, 0x54, 
	0x7C, 0x0A, 0x09, 0x7F, 0x49, 
	0x32, 0x49, 0x49, 0x49, 0x32, 
	0x32, 0x48, 0x48, 0x48, 0x32, 
	0x32, 0x4A, 0x48, 0x48, 0x30, 
	0x3A, 0x41, 0x41, 0x21, 0x7A, 
	0x3A, 0x42, 0x40, 0x20, 0x78, 
	0x00, 0x9D, 0xA0, 0xA0, 0x7D, 
	0x39, 0x44, 0x44, 0x44, 0x39, 
	0x3D, 0x40, 0x40, 0x40, 0x3D, 
	0x3C, 0x24, 0xFF, 0x24, 0x24, 
	0x48, 0x7E, 0x49, 0x43, 0x66, 
	0x2B, 0x2F, 0xFC, 0x2F, 0x2B, 
	0xFF, 0x09, 0x29, 0xF6, 0x20, 
	0xC0, 0x88, 0x7E, 0x09, 0x03, 
	0x20, 0x54, 0x54, 0x79, 0x41, 
	0x00, 0x00, 0x44, 0x7D, 0x41, 
	0x30, 0x48, 0x48, 0x4A, 0x32, 
	0x38, 0x40, 0x40, 0x22, 0x7A, 
	0x00, 0x7A, 0x0A, 0x0A, 0x72, 
	0x7D, 0x0D, 0x19, 0x31, 0x7D, 
	0x26, 0x29, 0x29, 0x2F, 0x28, 
	0x26, 0x29, 0x29, 0x29, 0x26, 
	0x30, 0x48, 0x4D, 0x40, 0x20, 
	0x38, 0x08, 0x08, 0x08, 0x08, 
	0x08, 0x08, 0x08, 0x08, 0x38, 
	0x2F, 0x10, 0xC8, 0xAC, 0xBA, 
	0x2F, 0x10, 0x28, 0x34, 0xFA, 
	0x00, 0x00, 0x7B, 0x00, 0x00, 
	0x08, 0x14, 0x2A, 0x14, 0x22, 
	0x22, 0x14, 0x2A, 0x14, 0x08, 
	0xAA, 0x00, 0x55, 0x00, 0xAA, 
	0xAA, 0x55, 0xAA, 0x55, 0xAA, 
	0x00, 0x00, 0x00, 0xFF, 0x00, 
	0x10, 0x10, 0x10, 0xFF, 0x00, 
	0x14, 0x14, 0x14, 0xFF, 0x00, 
	0x10, 0x10, 0xFF, 0x00, 0xFF, 
	0x10, 0x10, 0xF0, 0x10, 0xF0, 
	0x14, 0x14, 0x14, 0xFC, 0x00, 
	0x14, 0x14, 0xF7, 0x00, 0xFF, 
	0x00, 0x00, 0xFF, 0x00, 0xFF, 
	0x14, 0x14, 0xF4, 0x04, 0xFC, 
	0x14, 0x14, 0x17, 0x10, 0x1F, 
	0x10, 0x10, 0x1F, 0x10, 0x1F, 
	0x14, 0x14, 0x14, 0x1F, 0x00, 
	0x10, 0x10, 0x10, 0xF0, 0x00, 
	0x00, 0x00, 0x00, 0x1F, 0x10, 
	0x10, 0x10, 0x10, 0x1F, 0x10, 
	0x10, 0x10, 0x10, 0xF0, 0x10, 
	0x00, 0x00, 0x00, 0xFF, 0x10, 
	0x10, 0x10, 0x10, 0x10, 0x10, 
	0x10, 0x10, 0x10, 0xFF, 0x10, 
	0x00, 0x00, 0x00, 0xFF, 0x14, 
	0x00, 0x00, 0xFF, 0x00, 0xFF, 
	0x00, 0x00, 0x1F, 0x10, 0x17, 
	0x00, 0x00, 0xFC, 0x04, 0xF4, 
	0x14, 0x14, 0x17, 0x10, 0x17, 
	0x14, 0x14, 0xF4, 0x04, 0xF4, 
	0x00, 0x00, 0xFF, 0x00, 0xF7, 
	0x14, 0x14, 0x14, 0x14, 0x14, 
	0x14, 0x14, 0xF7, 0x00, 0xF7, 
	0x14, 0x14, 0x14, 0x17, 0x14, 
	0x10, 0x10, 0x1F, 0x10, 0x1F, 
	0x14, 0x14, 0x14, 0xF4, 0x14, 
	0x10, 0x10, 0xF0, 0x10, 0xF0, 
	0x00, 0x00, 0x1F, 0x10, 0x1F, 
	0x00, 0x00, 0x00, 0x1F, 0x14, 
	0x00, 0x00, 0x00, 0xFC, 0x14, 
	0x00, 0x00, 0xF0, 0x10, 0xF0, 
	0x10, 0x10, 0xFF, 0x10, 0xFF, 
	0x14, 0x14, 0x14, 0xFF, 0x14, 
	0x10, 0x10, 0x10, 0x1F, 0x00, 
	0x00, 0x00, 0x00, 0xF0, 0x10, 
	0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 
	0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 
	0xFF, 0xFF, 0xFF, 0x00, 0x00, 
	0x00, 0x00, 0x00, 0xFF, 0xFF, 
	0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 
	0x38, 0x44, 0x44, 0x38, 0x44, 
	0x7C, 0x2A, 0x2A, 0x3E, 0x14, 
	0x7E, 0x02, 0x02, 0x06, 0x06, 
	0x02, 0x7E, 0x02, 0x7E, 0x02, 
	0x63, 0x55, 0x49, 0x41, 0x63, 
	0x38, 0x44, 0x44, 0x3C, 0x04, 
	0x40, 0x7E, 0x20, 0x1E, 0x20, 
	0x06, 0x02, 0x7E, 0x02, 0x02, 
	0x99, 0xA5, 0xE7, 0xA5, 0x99, 
	0x1C, 0x2A, 0x49, 0x2A, 0x1C, 
	0x4C, 0x72, 0x01, 0x72, 0x4C, 
	0x30, 0x4A, 0x4D, 0x4D, 0x30, 
	0x30, 0x48, 0x78, 0x48, 0x30, 
	0xBC, 0x62, 0x5A, 0x46, 0x3D, 
	0x3E, 0x49, 0x49, 0x49, 0x00, 
	0x7E, 0x01, 0x01, 0x01, 0x7E, 
	0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 
	0x44, 0x44, 0x5F, 0x44, 0x44, 
	0x40, 0x51, 0x4A, 0x44, 0x40, 
	0x40, 0x44, 0x4A, 0x51, 0x40, 
	0x00, 0x00, 0xFF, 0x01, 0x03, 
	0xE0, 0x80, 0xFF, 0x00, 0x00, 
	0x08, 0x08, 0x6B, 0x6B, 0x08,
	0x36, 0x12, 0x36, 0x24, 0x36, 
	0x06, 0x0F, 0x09, 0x0F, 0x06, 
	0x00, 0x00, 0x18, 0x18, 0x00, 
	0x00, 0x00, 0x10, 0x10, 0x00, 
	0x30, 0x40, 0xFF, 0x01, 0x01, 
	0x00, 0x1F, 0x01, 0x01, 0x1E, 
	0x00, 0x19, 0x1D, 0x17, 0x12, 
	0x00, 0x3C, 0x3C, 0x3C, 0x3C, 
	0x00, 0x00, 0x00, 0x00, 0x00, 
	]
	return fontarray[c*5:c*5+5]

