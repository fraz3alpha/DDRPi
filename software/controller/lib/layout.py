__authors__ = ['Joel Wright']

import logging


class DisplayLayout(object):
    logger = logging.getLogger(__name__)

    def __init__(self, config):
        # super(DisplayLayout, self).__init__()
        self.load_config(config)

    def load_config(self, config):
        self.module_config = config["modules"]

        # Get the floor rotation from the config
        self.rotation = 0
        try:
            # Rotation cycles round after 3, with 4==0, so take the mod
            self.rotation = int(config["system"]["floor_rotation"]) % 4
            self.logger.info("Floor rotation found in config, set to %d" % self.rotation)
        except (AttributeError, ValueError, KeyError) as e:
            pass

        (self.size_x, self.size_y) = self.calculate_floor_size()
        self.calculate_mapping()
        self.rotate_layout(self.rotation)

    def rotate_layout(self, rotation):
        # Incrementing rotation by 1 rotates the floor by 90 degrees.
        # The size stays the same, just the axes move around, so return the right combo

        # If the rotation is not 0, then we should shift the layout mapping around
        if self.rotation > 0:

            # Set the new size
            original_size_x = self.size_x
            original_size_y = self.size_y
            if self.rotation % 2 == 1:
                self.size_x = original_size_y
                self.size_y = original_size_x

            for i in range(self.rotation):
                self.logger.info("Rotate Layout - %d" % i)
                # Very cunning, this. I found it on the internet
                self.layout_mapping = zip(*self.layout_mapping[::-1])

            self.logger.info("Floor is now of size %d, %d" % (self.size_x, self.size_y))

    def draw_layout(self):
        """
        Draw the modules layout to the console. This method draws the
        described layout onto the display, labelling the pixels with their
        dance floor address.
        """
        s = ""
        for y in range(0, self.size_y):
            for x in range(0, self.size_x):
                s += "%04s " % self.layout_mapping[x][y]
            s += "\n"
        return s

    """
    Return an ordered list of (x,y) coordinates
    Outputing data in this order will be correct for the defined dance floor
    """

    def get_converter(self):
        order = dict()
        for y in range(0, self.size_y):
            for x in range(0, self.size_x):
                order[self.layout_mapping[x][y]] = (x, y)

        ordered_list = []
        for pixel in sorted(order):
            ordered_list.append(order[pixel])

        return ordered_list

    def get_position(self, x, y):
        if x < 0 or y < 0 or x >= self.size_x or y >= self.size_y:
            return None
        else:
            return self.layout_mapping[x][y]

    def add_north(self, height, width, pos_x, pos_y):
        for y in range(pos_y, pos_y + height):
            for x in range(pos_x, pos_x + width):
                if self.layout_mapping[x][y] is not None:
                    self.logger.error("The config appears to contain overlapping tiles")
                self.layout_mapping[x][y] = self.pixel_count
                self.pixel_count += 1

    def add_east(self, height, width, pos_x, pos_y):
        for x in range(pos_x, pos_x + height):
            for y in reversed(range(pos_y, pos_y + width)):
                if self.layout_mapping[x][y] is not None:
                    self.logger.error("The config appears to contain overlapping tiles")
                self.layout_mapping[x][y] = self.pixel_count
                self.pixel_count += 1

    def add_south(self, height, width, pos_x, pos_y):
        for y in reversed(range(pos_y, pos_y + height)):
            for x in reversed(range(pos_x, pos_x + width)):
                if self.layout_mapping[x][y] is not None:
                    self.logger.error("The config appears to contain overlapping tiles")
                self.layout_mapping[x][y] = self.pixel_count
                self.pixel_count += 1
        return True

    def add_west(self, height, width, pos_x, pos_y):
        for x in reversed(range(pos_x, pos_x + height)):
            for y in range(pos_y, pos_y + width):
                if self.layout_mapping[x][y] is not None:
                    self.logger.error("The config appears to contain overlapping tiles")
                self.layout_mapping[x][y] = self.pixel_count
                self.pixel_count += 1
        return True


    def calculate_mapping(self):
        """
        Calculate the mapping from (x,y) dance floor coordinate to dance floor
        serial position.
        """
        # Create a list of lists filled with None, then we can populate with
        # the serial location if present
        self.layout_mapping = [[None for y in range(0, self.size_y)] for x in range(0, self.size_x)]
        self.pixel_count = 0

        for module in sorted(self.module_config.keys()):
            module_data = self.module_config[module]
            module_orientation = module_data["orientation"]
            module_height = module_data["height"]
            module_width = module_data["width"]

            if module_orientation == 'N':
                self.add_north(module_data["height"],
                               module_data["width"],
                               module_data["x_position"],
                               module_data["y_position"])
            elif module_orientation == 'E':
                self.add_east(module_data["height"],
                              module_data["width"],
                              module_data["x_position"],
                              module_data["y_position"])
            elif module_orientation == 'S':
                self.add_south(module_data["height"],
                               module_data["width"],
                               module_data["x_position"],
                               module_data["y_position"])
            elif module_orientation == 'W':
                self.add_west(module_data["height"],
                              module_data["width"],
                              module_data["x_position"],
                              module_data["y_position"])
            else:
                self.logger.error("The orientation of a tile in the config was not recognised")


    def calculate_floor_size(self):
        """
        Calculate the total size in pixels described by the config file. Note
        that we do not guarantee that all pixels will be used, this simply
        returns the max x and y coordinates described.

        We will deal with overlapping boards and gaps later.

        Returns:
                A pair containing the maximum x and y coordinated required by the
                dance floor
        """
        x_extent = 0
        y_extent = 0

        for module in sorted(self.module_config.keys()):
            module_data = self.module_config[module]
            module_orientation = module_data["orientation"]
            module_height = module_data["height"]
            module_width = module_data["width"]

            max_x, max_y = {
            'N': (module_width + module_data["x_position"], module_height + module_data["y_position"]),
            'E': (module_height + module_data["x_position"], module_width + module_data["y_position"]),
            'S': (module_width + module_data["x_position"], module_height + module_data["y_position"]),
            'W': (module_height + module_data["x_position"], module_width + module_data["y_position"]),
            }[module_orientation]

            if (max_x > x_extent):
                x_extent = max_x
            if (max_y > y_extent):
                y_extent = max_y

        return (x_extent, y_extent)

		
