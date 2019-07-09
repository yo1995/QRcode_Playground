from PIL import Image
from PIL import ImageSequence
from pyzbar.pyzbar import decode as QRdecode
import qrcode
import multiprocessing
import base64
import GIFSurface
import GIFencoder
import time


class QRCodec:

    qr_version = 5  # commonly 1-10, check QR code docs, full 1-40
    err_crt = qrcode.constants.ERROR_CORRECT_L

    chuck_length = 134  # 134 at most for version 6, 2953 at most for version 40 base64

    GIF_version = 'GIF89a'
    GIF_delay = 100  # 200ms or 5 frames per second

    @staticmethod
    def gen_qr_render_frame(qr_obj, s: str, width, height, render_obj):
        """
        A wrapper function to run in multiprocessing.
        Generate QR code matrix from base64 string chunk and covert to rendered frame.

        :param qr_obj: the qr generator object
        :param s: the string to convert to QR code
        :param width: render frame width
        :param height: render frame height
        :param render_obj: the renderer object
        :return: frame rendered for the string
        """
        qr_obj.clear()
        qr_obj.add_data(s)
        mat = qr_obj.get_matrix()
        return render_obj(width, height, mat)

    def encode(self, input_file_path: str, output_gif_path: str, mode: str = 'b64'):
        """
        The practical encoder with optimized GIF assembler and multiprocessing acceleration.

        :param input_file_path: input file path
        :param output_gif_path: output gif file path
        :param mode: b64 for base64 encode, b32 for base32 encode
        :return: None
        """

        # open the file to encode
        with open(input_file_path, 'rb') as f:
            if mode == 'b64':
                encoded_string = base64.b64encode(f.read()).decode()
            if mode == 'b32':
                encoded_string = base64.b32encode(f.read()).decode()
                encoded_string = encoded_string.replace('=', '$')  # alphanumeric does not support equal sign
        f.close()

        # chunk the string into pieces of length = 120
        chunks, chunk_size = len(encoded_string), self.chuck_length  # len(encoded_string) // 120
        string_list = [encoded_string[i:i + chunk_size] for i in range(0, chunks, chunk_size)]

        # init the QRCode generator
        # current can only set box_size to 1 due to QR matrix's format
        qr = qrcode.QRCode(version=self.qr_version, error_correction=self.err_crt, box_size=1, border=2)
        qr.add_data(string_list[0])
        qr.make(fit=True)

        # extract the first frame as a reference frame, to generate following frames with same dimensions
        frames_template = qr.make_image().convert(mode='L', palette='ADAPTIVE', colors=2)

        # make the drawing canvas
        (width, height) = (frames_template.width, frames_template.height)
        surface = GIFSurface.GIFSurface(width, height, bg_color=0)
        # other colors to choose from - 78, 205, 196,   161,35,6,   150, 200, 100,   161, 35, 6,   255, 255, 255
        surface.set_palette([0, 0, 0, 255, 255, 255])

        # the colormap for QRCode. map True to white
        cmap = {True: 0, False: 1}  # Black -> True -> (0, 0, 0)
        mcl = 2  # related to LZW compression alg, 2-10
        render = GIFSurface.Render(cmap, mcl)
        delay = self.GIF_delay
        trans_index = None

        # assuming all frames share same delay
        control = GIFencoder.graphics_control_block(delay, trans_index)
        # create an array to store multiprocessing results
        frames = [None] * len(string_list)
        # create a pool to dispatch frames encoding
        pool1 = multiprocessing.Pool(processes=multiprocessing.cpu_count())  # use up all the cores.

        for i, s in enumerate(string_list):
            frames[i] = pool1.apply_async(self.gen_qr_render_frame, args=(qr, s, width, height, render, ))

        # join the pool
        pool1.close()
        pool1.join()

        for i in range(len(string_list)):
            surface.write(control + frames[i].get())

        surface.save(output_gif_path)
        surface.close()
        return

    def encode_without_mp(self, input_file_path: str, output_gif_path: str):
        """
        This is to use the optimized renderer without multiprocessing.
        Encode a 100KB file will take around 40 seconds.

        :param input_file_path: input file path
        :param output_gif_path: output gif file path
        :return: None
        """

        with open(input_file_path, 'rb') as f:
            encoded_string = base64.b64encode(f.read()).decode()
        f.close()

        chunks, chunk_size = len(encoded_string), 120
        string_list = [encoded_string[i:i + chunk_size] for i in range(0, chunks, chunk_size)]

        if len(string_list[-1]) < chunk_size:
            s = string_list[-1]
            s += (chunk_size - len(string_list[-1])) * '%'
            string_list[-1] = s

        qr = qrcode.QRCode(version=self.qr_version, error_correction=self.err_crt, box_size=1, border=2)  # current can only set box_size to 1
        qr.add_data(string_list[0])
        qr.make(fit=True)
        frames_template = qr.make_image().convert(mode='L', palette='ADAPTIVE', colors=2)
        (width, height) = (frames_template.width, frames_template.height)
        surface = GIFSurface.GIFSurface(width, height, bg_color=0)
        surface.set_palette([0, 0, 0, 255, 255, 255])

        cmap = {True: 0, False: 1}
        mcl = 2
        render = GIFSurface.Render(cmap, mcl)
        delay = self.GIF_delay
        trans_index = None

        for i, s in enumerate(string_list):
            qr.clear()
            qr.add_data(s)
            qr.make(fit=True)
            mat = qr.get_matrix()
            control = GIFencoder.graphics_control_block(delay, trans_index)
            surface.write(control + render(width, height, mat))

        surface.save(output_gif_path)
        surface.close()
        return

    def encode_huge_slow(self, input_file_path, output_gif_path):
        """
        This is to use the default file saver of PIL, which will generate a considerably huge not optimized GIF file.
        E.g. 16KB input file -> 400 KB GIF file.

        :param input_file_path: input file path
        :param output_gif_path: output gif file path
        :return: None
        """
        with open(input_file_path, 'rb') as f:
            encoded_string = base64.b64encode(f.read()).decode()
        f.close()

        chunks, chunk_size = len(encoded_string), 120
        string_list = [encoded_string[i:i + chunk_size] for i in range(0, chunks, chunk_size)]

        if len(string_list[-1]) < chunk_size:
            s = string_list[-1]
            s += (chunk_size - len(string_list[-1])) * '%'
            string_list[-1] = s

        qr = qrcode.QRCode(version=self.qr_version, error_correction=self.err_crt, box_size=1, border=2)
        frames = [None] * len(string_list)
        for i, s in enumerate(string_list):
            qr.clear()
            qr.add_data(s)
            qr.make(fit=True)
            frames[i] = qr.make_image().convert(mode='L', palette='ADAPTIVE', colors=2)
        frames[0].save(output_gif_path, save_all=True, optimize=True, append_images=frames[1:], disposal=2, version=self.GIF_version, loop=0, duration=self.GIF_delay)
        return

    @staticmethod
    def decode(input_gif_path, output_file_path, mode: str = 'b64'):
        """
        Decode the GIF to recover its binary file entity.

        :param input_gif_path: input GIF file
        :param output_file_path: output binary file, use extension to decide file type.
        :return: None
        """
        if type(input_gif_path) is str:
            img = Image.open(input_gif_path)  # GIF file
        else:
            return

        decoded_string = ''
        frame_count = 0
        for frame in ImageSequence.Iterator(img):
            frame_count += 1
            if frame_count < 2:
                continue  # skip the first black frame
            # the decode CV lib relies on the dimensions, 1px width cannot be recognized
            (width, height) = (frame.width * 2, frame.height * 2)
            im_resized = frame.resize((width, height))
            decoded = QRdecode(im_resized)
            decoded_string += decoded[0].data.decode('ascii')

        print('total frame count is', str(frame_count))
        decoded_string = decoded_string.replace('$', '=')  # recover padding

        file_bin = None
        if mode == 'b64':
            file_bin = base64.b64decode(decoded_string)
        if mode == 'b32':
            file_bin = base64.b32decode(decoded_string)
        with open(output_file_path, 'wb') as f:
            f.write(file_bin)
        f.close()
        return


def main():
    q = QRCodec()
    input_path = '../test_images/ECE564.png'
    save_path = '../test_images/temp_v6.gif'
    output_path = '../test_images/out2.png'

    print('encode')
    t = time.time()
    q.encode(input_file_path=input_path, output_gif_path=save_path)
    # q.encode_without_mp(input_file_path=input_path, output_gif_path=save_path)
    print("Encode benchmark", time.time() - t)
    print('decode')
    q.decode(save_path, output_path)
    return


def byte_test():
    q = QRCodec()
    q.chuck_length = 2953
    input_path = '../test_images/ECE564.png'
    save_path = '../test_images/b64_v40_2953.gif'
    output_path = '../test_images/face3.png'

    print('encode')
    t = time.time()
    q.encode(input_file_path=input_path, output_gif_path=save_path, mode='b64')
    print("Encode benchmark", time.time() - t)
    print('decode')
    q.decode(save_path, output_path, mode='b64')
    return


if __name__ == '__main__':
    # main()
    byte_test()
