__authors__ = ['Andrew Taylor']

# For sending out serial data to the floor
import serial
# For the gui
import pygame
# For counting instances of output classes
from itertools import count



class Output(object):

	_ids = count(0)

	def __init__(self):
		self.set_name("%s-%d" % (self.__class__.__name__,next(self._ids)))
		pass

	def set_name(self, name):
		self.name = name

	def send_data(self, canvas):
		pass

	def clear(self):
		pass


class GuiOutput(Output):
	# This will provide an inbuilt windows showing the correct
	#  current state of the dance floor. This will be useful 
	#  when developing new plugins, and means we don't need to
	#  run a separate dance floor emulation process all the time
	def __init__(self):
		super(GuiOutput,self).__init__()
	
		self.playlist_model = None
		self.clock = pygame.time.Clock()

		# We assume that pygame has been initialised.

		self.gui = pygame.display.set_mode((400, 800))
		pygame.display.set_caption('DDRPi Gui Display')

	def get_nearest_cell(self, canvas, x, y):
		fractional_position = self.get_fractional_position(canvas, x,y)
		if fractional_position is None:
			return None

		# Get the sizes of the screen and the canvas (the floor)
		(width, height) = self.gui.get_size()
		(canvas_width, canvas_height) = canvas.get_size()

		# Work out how big the square would be in each direction and choose
		#  choose the smaller so that it fits in in both directions
		x_pixels_per_cell = width // canvas_width
		y_pixels_per_cell = height // canvas_height
		pixels_per_cell = min(x_pixels_per_cell, y_pixels_per_cell)

		fractional_x, fractional_y = fractional_position

		cell_position_x = fractional_x * canvas_width
		cell_position_y = fractional_y * canvas_height

		return (int(cell_position_x // 1), int(cell_position_y // 1))

	def get_fractional_position(self, canvas, x, y):

		# Get the sizes of the screen and the canvas (the floor)
		(width, height) = self.gui.get_size()
		(canvas_width, canvas_height) = canvas.get_size()

		# Work out how big the square would be in each direction and choose
		#  choose the smaller so that it fits in in both directions
		x_pixels_per_cell = width // canvas_width
		y_pixels_per_cell = height // canvas_height
		pixels_per_cell = min(x_pixels_per_cell, y_pixels_per_cell)

		# We are going to centre the dance floor representation in the
		#  GUI window, so there may be some padding around it, depending
		#  on the aspect ratio, work out the padding
		x_padding = width - (canvas_width * pixels_per_cell)
		y_padding = height - (canvas_height * pixels_per_cell)

		min_x = x_padding // 2.0
		max_x = width - x_padding // 2.0

		# Check for x out of bounds
		if (x < min_x or x > max_x):
			return None 

		min_y = y_padding // 2.0
		max_y = height - y_padding // 2.0

		# Check for y out of bounds
		if (y < min_y or y > max_y):
			return None

		x = x - min_x
		y = y - min_y

		fractional_x = x / float(pixels_per_cell * canvas_width)
		fractional_y = y / float(pixels_per_cell * canvas_height)

		return (fractional_x, fractional_y)
		

	def set_playlist_model(self, model):
		self.playlist_model = model
		return None

	def playlist_model_changed_event(self):
		print("Notified of change in the playlist model!")
		#self.redraw()
		return None


	def send_data(self, canvas):
		self.canvas = canvas
		self.redraw()
		
		return None

	def redraw(self):
		# Get an object we can draw on
		drawable = pygame.Surface(self.gui.get_size())
		drawable = drawable.convert()

		# Redraw the floor visualisation pattern
		self.update_floor_visualisation(drawable, self.canvas)

		# Draw the input controllers (if appropriate)
		self.draw_controllers(drawable)

		# Draw some visualisation playlist information
		self.draw_visualisation_playlist_info(drawable)

		# Copy, or 'blit' the drawable object onto the GUI and flip 
		#  the double buffer
		self.gui.blit(drawable, (0, 0))
		pygame.display.flip()

		self.clock.tick()

		return None

	def draw_visualisation_playlist_info(self, drawable):

		if self.playlist_model is None:
			return

		current_plugin = self.playlist_model.get_current_plugin()["name"]

		font = pygame.font.Font(None, 24)
		text = font.render(current_plugin, 1, (0xFF, 0xFF, 0xFF))
		textpos = text.get_rect()
		(size_width, size_height) = font.size(current_plugin)
		drawable.blit(text, (200 - size_width/2,320 - size_height))

		# Draw how long is remaining for this plugin
		# If this is the only plugin, and it is on loop, then it is going
		#  to run for an indefinite amount of time
		if (self.playlist_model.get_playlist_length() == 1 and 
			self.playlist_model.get_cycle_mode() == "LOOP"):
			remaining_time = ""
		else:
			remaining_time = "%d" % self.playlist_model.get_current_plugin_remaining_time()

		text = font.render(remaining_time, 1, (0xFF, 0xFF, 0xFF))
		textpos = text.get_rect()
		(size_width, size_height) = font.size(remaining_time)
		drawable.blit(text, (200 - size_width/2,350 - size_height))

		playlist_length = self.playlist_model.get_playlist_length()

		playlist_entries = self.playlist_model.get_playlist()
		playlist_index = self.playlist_model.get_current_plugin_index()
		for index,entry in enumerate(playlist_entries):
			playlist_entry_string = entry["name"]
			font = pygame.font.Font(None, 24)
			colour = (0xFF, 0xFF, 0xFF)
			if (playlist_index == index):
				colour = (0x80, 0x80, 0xFF)
			text = font.render(playlist_entry_string, 1, colour)
			textpos = text.get_rect()
			(size_width, size_height) = font.size(playlist_entry_string)
			drawable.blit(text, (20,500 + index * 20 - size_height))

		# Print an estimate of the FPS
		fps = self.clock.get_fps()
		fps_s = "%d" % fps

		font = pygame.font.Font(None, 24)
		text = font.render(fps_s, 1, (0xFF, 0xFF, 0xFF))
		textpos = text.get_rect()
		(size_width, size_height) = font.size(fps_s)
		padding = 5
		drawable.blit(text, (400 - size_width - padding,800 - size_height - padding))

		#print(textpos)

	def draw_controllers(self, drawable):
		self.draw_controller(drawable, (200-100,400))
		self.draw_controller(drawable, (200+100,400))

		return None

	#def draw_controller(self, drawable, (x,y), (width,height)):
	def draw_controller(self, drawable, centre):

		# Draw a SNES controller, with feedback as to whether
		#  buttons are being pressed or not
		# One or two controllers should be drawn depending on how 
		#  have been initialised, and we will need to know the state
		#  of the buttons somehow, so hook into a joystick event
		#  listener when we have one

		# Circles at either side are 60mm in diameter
		# Middle is only 53mm
		# Total width 142mm

		(centre_x, centre_y) = centre

		controller_width = 142
		controller_height = 60
		controller_waist = 53
		controller_button_radius = 7
		d_pad_diameter = 28
		d_pad_button_width = 10
		# Some helper dimensions
		circle_centre_x = (controller_width-controller_height)/2
		circle_radius = controller_height/2
		y_to_a = 30
		x_to_b = 24

		# A light gray
		controller_colour = (0xB0,0xB0,0xB0)
		lighter_controller_colour = (0xC0,0xC0,0xC0)
		x_colour_pressed = (0x00,0x00,0xFF)
		y_colour_pressed = (0x00,0xFF,0x00)
		a_colour_pressed = (0xFF,0x00,0x00)
		b_colour_pressed = (0xFF,0xFF,0x00)
		d_pad_unpressed = (0x00,0x00,0x00)

		#centre_x = 200
		#centre_y = 400

		# Draw the controller body
		pygame.draw.circle(drawable, controller_colour, (int(centre_x - circle_centre_x),centre_y), int(circle_radius), 0)
		pygame.draw.circle(drawable, controller_colour, (int(centre_x + circle_centre_x),centre_y), int(circle_radius), 0)

		pygame.draw.rect(drawable, 
				controller_colour, 
				(int(centre_x - circle_centre_x),
				int(centre_y - (controller_height/2)), 
				int(controller_width - controller_height), 
				int(controller_waist)), 
				0)

		pygame.draw.circle(drawable, lighter_controller_colour, (int(centre_x - circle_centre_x),centre_y), int(d_pad_diameter/2.0*1.4), 0)

		# Draw the coloured buttons (becoming brighter when pressed)
		pygame.draw.circle(drawable, x_colour_pressed, (int(centre_x + circle_centre_x), int(centre_y-(x_to_b/2))), controller_button_radius, 0)
		pygame.draw.circle(drawable, b_colour_pressed, (int(centre_x + circle_centre_x), int(centre_y+(x_to_b/2))), controller_button_radius, 0)
		pygame.draw.circle(drawable, y_colour_pressed, (int(centre_x + circle_centre_x-(y_to_a/2)), int(centre_y)), controller_button_radius, 0)
		pygame.draw.circle(drawable, a_colour_pressed, (int(centre_x + circle_centre_x+(y_to_a/2)), int(centre_y)), controller_button_radius, 0)

		# Draw the dpad
		pygame.draw.rect(drawable,
				d_pad_unpressed,
				(int(centre_x - circle_centre_x - d_pad_button_width/2.0),
				int(centre_y - d_pad_diameter/2.0),
				d_pad_button_width,
				d_pad_diameter),
				0)

		pygame.draw.rect(drawable,
				d_pad_unpressed,
				(int(centre_x - circle_centre_x - d_pad_diameter/2.0),
				int(centre_y - d_pad_button_width/2.0),
				d_pad_diameter,
				d_pad_button_width),
				0)
		

		return None


	def update_floor_visualisation(self, drawable, canvas):

		# Work out how many pixels square each cell will be, as we want to 
		#  maintain the aspect ratio (// rounds down). We will then pad
		#  the other axis so that the floor appears in the centre of the
		#  window.

		# Get the sizes of the screen and the canvas (the floor)
		(width, height) = self.gui.get_size()
		(canvas_width, canvas_height) = canvas.get_size()

		# Work out how big the square would be in each direction and choose
		#  choose the smaller so that it fits in in both directions
		x_pixels_per_cell = width // canvas_width
		y_pixels_per_cell = height // canvas_height
		pixels_per_cell = min(x_pixels_per_cell, y_pixels_per_cell)

		# We are going to centre the dance floor representation in the
		#  GUI window, so there may be some padding around it, depending
		#  on the aspect ratio, work out the padding
		x_padding = width - (canvas_width * pixels_per_cell)
		y_padding = height - (canvas_height * pixels_per_cell)
		y_padding = 10

		# Get the [x][y] array from the canvas object
		data = canvas.get_canvas_array()
	
		# Draw something that will be in the background so we can see where
		#  the floor ends in the case where there is a border and the floor
		#  is the same colour as the background. A basic X works nicely.
		pygame.draw.line(drawable, (0xFF,0xFF,0xFF),(0,0),(width,height),1)
		pygame.draw.line(drawable, (0xFF,0xFF,0xFF),(0,height),(width,0),1)

		# Draw the pixels of the floor canvas onto the drawable object
		# The position is determined based on the size of each cell and the padding
		#  amounts calculated previously
		for canvas_x in range(canvas_width):
			for canvas_y in range(canvas_height):
				rect_pos = (canvas_x*pixels_per_cell + x_padding, canvas_y*pixels_per_cell + y_padding)
				pygame.draw.rect(drawable, canvas.get_pixel_tuple(canvas_x,canvas_y), pygame.Rect(canvas_x*pixels_per_cell + x_padding//2, canvas_y*pixels_per_cell + y_padding//2,pixels_per_cell,pixels_per_cell), 0)
		
		return None

	def clear(self):
		pass

class SerialOutput(Output):
	
	def __init__(self, config):
		super(SerialOutput,self).__init__()
		self.converter = None
		# Open specified serial port with the correct
		#  parameters
		self.open_serial_port(config)
	
	def open_serial_port(self, config):
		self.tty = None
		self.baud = None
		self.timeout = 1
		if ("tty" in config):
			self.tty = config["tty"]
		if ("baud" in config):
			self.baud = config["baud"]
		if ("timeout" in config):
			self.timeout = config["timeout"]
		print("Creating serial port with tty=%s, baud=%s, timeout=%s" % (self.tty, self.baud, self.timeout))
		self.serial_port = serial.Serial(self.tty, self.baud, timeout=self.timeout)
		print("Hello, my name is %s" % self.name)

	def set_output_converter(self, converter):
		# The converter will be used to pick the 
		#  pixels out in the correct order. Note
		#  that some pixels might not even be output
		#  if the floor tiles form a non-rectangular 
		#  shape
		# 'converter' is an array of (x,y) tuples
		#  which, when iterated through, puts all the
		#  appropriate cells in the correct order
		self.converter = converter
		pass

	def send_data(self, canvas):
		# Write data to the serial port, terminate it
		#  with 0x01 to instigate a buffer flip.
		# Coerce 0xFF down to 0xFE to ensure that long 
		#  sequences of '1' bits aren't sent that might
		#  throw out the receivers 

		# First we need to convert the canvas into a buffer
		#  containing the bytes in the right order

		# Create one long string of all the bytes to send
		output_string = ""
		canvas_array = canvas.get_canvas_array()
		if self.converter == None:
			# Assume that pixels need to be sent in
			#  the order they are, (0,0), (1,0), (2,0)
			#  etc...
			# It is highly likely this is not what you 
			#  want, unless your output is only a single
			#  module

			for x in range(0,canvas.width):
				for y in range(0,canvas.height):
					rgb = canvas_array[x][y]
					output_string += self.form_pixel_data(rgb)
			pass
		else:
			# Iterate over the converter, picking up the right
			#  pixels in the right order
			for (x,y) in self.converter:
				rgb = canvas_array[x][y]
				output_string += self.form_pixel_data(rgb)

		# Add the sync pulse
		output_string += chr(1)
		# Send all the data
		self.serial_port.write(output_string)

	def form_pixel_data(self, rgb):

		output_string = ""

		# extract the components
		red   = (rgb >> 16) & 0xFF
		green = (rgb >> 8)  & 0xFF
		blue  =  rgb        & 0xFF
		# Make sure we don't send a 0x01, which is the 
		#  sync signal we only send at the end
		# Also, send 254 instead of 255 to make sure that
		#  we don't get interference that we've seen from
		#  really long sequences of 1 bits.
		if red == 1:
			red = 2
		elif red > 254:
			red = 254
		
		if green == 1:
			green = 2
		elif green > 254:
			green = 254

		if blue == 1:
			blue = 2
		elif blue > 254:
			blue = 254
			
		output_string += chr(red)
		output_string += chr(green)
		output_string += chr(blue)
		
		return output_string
	
	def clear(self):
		pass


class PipeOutput(Output):
	# This is similar, if not identical to the SerialOutput
	#  class as it's intended use is for replicating the 
	#  physical dancefloor in software
	def __init__(self):
		super(GuiOutput,self).__init__()

	def send_data(self,data_buffer):
		pass

	def clear(self):
		pass

