from io import BytesIO
from PIL import Image
from functools import partial
import GIFencoder as encoder


class GIFSurface(object):
    """
    A GIFSurface is an object on which the animations are drawn,
    and which can be saved as GIF images.
    Each instance opens a BytesIO file in memory once it's created.
    The frames are temporarily written to this in-memory file for speed.
    When the animation is finished one should call the `close()` method
    to close the io.
    """
    def __init__(self, width, height, loop=0, bg_color=None):
        """
        ----------
        Parameters
        width, height: size of the image in pixels.
        loop: number of loops of the image.
        bg_color: background color index.
        """
        self.width = width
        self.height = height
        self.loop = loop
        self.palette = None
        self._io = BytesIO()

        if bg_color is not None:
            self.write(encoder.rectangle(0, 0, width, height, bg_color))

    @classmethod
    def from_image(cls, img_file, loop=0):
        """
        Create a surface from a given image file.
        The size of the returned surface is the same with the image's.
        The image is then painted as the background.
        """
        # the image file usually contains more than 256 colors
        # so we need to convert it to gif format first.
        with BytesIO() as temp_io:
            Image.open(img_file).convert('RGB').save(temp_io, format='gif')
            img = Image.open(temp_io).convert('RGB')
            surface = cls(img.size[0], img.size[1], loop=loop)
            surface.write(encoder.parse_image(img))
        return surface

    def write(self, data):
        self._io.write(data)

    def set_palette(self, palette):
        """
        Set the global color table of the GIF image.
        The user must specify at least one rgb color in it.
        `palette` must be a 1-d list of integers between 0-255.
        """
        try:
            palette = bytearray(palette)
        except:
            raise ValueError('A 1-d list of integers in range 0-255 is expected.')

        if len(palette) < 3:
            raise ValueError('At least one (r, g, b) triple is required.')

        nbits = (len(palette) // 3).bit_length() - 1
        nbits = min(max(nbits, 1), 8)
        valid_len = 3 * (1 << nbits)
        if len(palette) > valid_len:
            palette = palette[:valid_len]
        else:
            palette.extend([0] * (valid_len - len(palette)))

        self.palette = palette

    @property
    def _gif_header(self):
        """
        Get the `logical screen descriptor`, `global color table`
        and `loop control block`.
        """
        if self.palette is None:
            raise ValueError('Missing global color table.')

        color_depth = (len(self.palette) // 3).bit_length() - 1
        screen = encoder.screen_descriptor(self.width, self.height, color_depth)
        loop = encoder.loop_control_block(self.loop)
        return screen + self.palette + loop

    def save(self, filename):
        """
        Save the animation to a .gif file, note the 'wb' mode here!
        """
        with open(filename, 'wb') as f:
            f.write(self._gif_header)
            f.write(self._io.getvalue())
            f.write(bytearray([0x3B]))

    def close(self):
        self._io.close()


class Render(object):
    """
    This class encodes the region specified by the `frame_box` attribute of a maze
    into one frame in the GIF image.
    """
    def __init__(self, cmap, mcl):
        """
        cmap: a dict that maps the value of the cells to their color indices.
        mcl: the minimum code length for the LZW compression.
        A default dict is initialized so that one can set the colormap by
        just specifying what needs to be specified.
        """
        self.colormap = {i: i for i in range(1 << mcl)}
        if cmap:
            self.colormap.update(cmap)
        self.compress = partial(encoder.lzw_compress, mcl=mcl)

    def __call__(self, width, height, mat):
        """
        Encode current maze into one frame and return the encoded data.
        Note the graphics control block is not added here.
        """
        # the image descriptor
        left, top = 0, 0
        descriptor = encoder.image_descriptor(left, top, width, height)

        pixels = [self.colormap[mat[x][y]]
                  for x in range(width)
                  for y in range(height)]

        # the compressed image data of this frame
        data = self.compress(pixels)

        return descriptor + data
