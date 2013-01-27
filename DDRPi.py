__authors__ = ['Joel Wright','Mark McArdle']

import importlib
import os
import logging
import pygame
import sys
import yaml
from comms import FloorComms
from lib.layout import DisplayLayout
from lib.plugins_base import DDRPiPlugin, PluginRegistry
from pygame.locals import *

class DanceSurface(object):
	"""
	The class representing the drawable dance floor. This is a wrapper around
	an internal representation of the dance floor, so that plugins need only
	write images using (x,y) coordinates and don't have to worry about the
	configuration of dance floor tiles. The dance surface is passed to the
	display plugins, and reacts to any changes made by sending the the
	appropriate updates to the dance floor through the serial port.
	"""
	def __init__(self, config):
		super(DanceSurface, self).__init__()
		# Create the floor communication object
		self.comms = FloorComms(config.["system"].["tty"])
		# Create the layout object and calculate floor size
		self.layout = DisplayLayout(config.["modules"])
		(self.width, self.height) = self.layout.calculate_floor_size()
		self.total_pixels = self.width * self.height
		# Initialise all the pixels to black 
		self.pixels = [ 0 for n in range(0, 3*self.total_pixels) ]
		
	def hexToTuple(rgb_tuple):
		"""
		Convert an (R, G, B) tuple to hex #RRGGBB
		"""
		hex_colour = '#%02x%02x%02x' % rgb_tuple
		return hex_colour

	def tupleToHex(hex_colour):
		"""
		Convert hex #RRGGBB to an (R, G, B) tuple
		"""
		hex_colour = hex_colour.strip()
		if hex_colour[0] == '#':
			hex_colour = hex_colour[1:]
		if len(hex_colour) != 6:
			raise ValueError, "input #%s is not in #RRGGBB format" % hex_colour
		(rs,gs,bs) = hex_colour[:2], hex_colour[2:4], hex_colour[4:]
		r = int(rs, 16)
		g = int(gs, 16)
		b = int(bs, 16)
		return (r,g,b)

	def blit(self):
		"""
		Draw the updated floor to the serial port
		"""
		self.comms.send_data(self.pixels)

	def clear(self, colour)
		"""
		Clear the surface to a single colour
		"""
		# Make sure we never send a 1 by mistake and screw up the frames
		(r,g,b) = [ x if not x == 1 else 0 for x in self.hexToTuple(colour) ]
		for x in range(0,self.total_pixels):
			self.pixels[x*3:(x+1)*3] = [r,g,b]

	def draw_pixel(self, x, y, colour)
		"""
		Set the value of the pixel at (x,y) to colour
		"""
		# Make sure we never send a 1 by mistake and screw up the frames
		(r,g,b) = [ x if not x == 1 else 0 for x in self.hexToTuple(colour) ]
		mapped_pixel = 3 * self.layout.get_position(x,y)
		self.pixels[mapped_pixel:mapped_pixel+3] = [r,g,b]
		
	# TODO: More drawing primitives:
	# def draw_line
	# def draw_box
	# def fill_area


class DDRPi(object):
	"""
	The Main class - should load plugins and manage access to the DanceSurface object
	"""
	def __init__(self):
		"""
		Initialise the DDRPi Controller app.
		"""
		super(DDRPi, self).__init__()

		logging.info("DDRPi starting...")

		# Load the application config
		self.config = self.__load_config()

		# Set up plugin registry
		self.__registry__ = PluginRegistry()
		self.__register_plugins(self.config["system"]["plugin_dir"])

		# Create the dance floor surface
		self.dance_surface = DanceSurface(self.config)
		
		# Initialise pygame
		pygame.init()

	def __load_config(self):
		"""
		Load the config file into a dictionary.

		Returns:
			The dictionary resulting from loading the YAML config file.
		"""
		f = open('config.yaml')
		data = yaml.load(f)
		f.close()
		return data

	def __register_plugins(self, plugin_folder):
		"""
		Find the loadable plugins in the given plugin folder.
		
		The located plugins are then loaded into the plugin registry.
		"""
		logging.info("Searching for plugins in %s" % plugin_folder)
		
		for root, dirs, files in os.walk(plugin_folder):
			for fname in files:
				if fname.endswith(".py") and not fname.startswith("__"):
					fpath = os.path.join(root, fname)
					mname = fpath.rsplit('.', 1)[0].replace('/', '.').replace('\\', '.')
					importlib.import_module(mname)

			for plugin in DDRPiPlugin.__subclasses__():
				print("name: %s" % plugin.__name__)
				pinst = plugin()
				self.__registry__.register(pinst.__name__, pinst)

	def changed_layout(self):
		"""
		Called on layout change to redefine the DanceFloor size/shape
		
		** Not currently used **
		"""
		# Get the new size and shape
		(x,y) = self.layout.calculate_floor_size()

		# Create a new dance surface
		self.dance_surface = DanceSurface(x, y)

		# TODO: Reconfigure the running plugin (or reload the running plugin)
		#	   Need to create a layout changed event

	def main_loop(self):
		"""
		Enter main event loop and start drawing to the floor
		"""
		# TODO: Pick a display plugin from the registry
		#       (i.e. one of the games or visualisations)
		available_plugins = __registry__.get_names()
		if len(available_plugins) > 0:
			self.active_plugin = __registry__.get_plugin(available_plugins[0])
			self.active_plugin.configure(self.config, self.dance_surface)
			self.active_plugin.start()
		else:
			logging.error("No display plugins found")
			sys.exit(1)
		
		# Enter main event loop - each period handle events generated by the user 
		# and send those events to the active display plugin to make the
		# appropriate updates on the floor
		while(True):
			for e in pygame.event.get():
				# handle special events (e.g. plugin switch)
				
				# active plugin handle e
				logging.debug("Active plugin handling event: %s" % e)
				self.active_plugin.handle(e)
			
			# Update the display
			# We're just going as fast as the serial port will let us atm
			self.active_plugin.update_surface()

# Start the dance floor application
if __name__ == "__main__":
	dance_floor = DDRPi()
	dance_floor.main_loop()
