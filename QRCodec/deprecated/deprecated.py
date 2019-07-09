# def encode_as_bytes(input_file_path: str, output_gif_path: str):
#     """
#     The practical encoder with optimized GIF assembler and multiprocessing acceleration.
#
#     :param input_file_path: input file path
#     :param output_gif_path: output gif file path
#     :param chunk_string_length: the length of base64 string for each frame
#     :return: None
#     """
#
#     # open the file to encode
#     def bytes_from_file(filename, size):
#         with open(filename, "rb") as fb:
#             while True:
#                 chunk = fb.read(size)
#                 if chunk:
#                     yield chunk
#                 else:
#                     break
#
#     string_list = []
#     for c in bytes_from_file(input_file_path, self.chuck_length):
#         string_list.append([c])
#
#     # init the QRCode generator
#     # current can only set box_size to 1 due to QR matrix's format
#     qr = qrcode.QRCode(version=self.qr_version, error_correction=self.err_crt, box_size=1, border=2)
#     qr.add_data(string_list[0])
#     qr.make(fit=True)
#
#     # extract the first frame as a reference frame, to generate following frames with same dimensions
#     frames_template = qr.make_image().convert(mode='L', palette='ADAPTIVE', colors=2)
#
#     # make the drawing canvas
#     (width, height) = (frames_template.width, frames_template.height)
#     surface = GIFSurface.GIFSurface(width, height, bg_color=0)
#     # other colors to choose from - 78, 205, 196,   161,35,6,   150, 200, 100,   161, 35, 6,   255, 255, 255
#     surface.set_palette([0, 0, 0, 255, 255, 255])
#
#     # the colormap for QRCode. map True to white
#     cmap = {True: 0, False: 1}  # Black -> True -> (0, 0, 0)
#     mcl = 2  # related to LZW compression alg, 2-10
#     render = GIFSurface.Render(cmap, mcl)
#     delay = self.GIF_delay
#     trans_index = None
#
#     # assuming all frames share same delay
#     control = GIFencoder.graphics_control_block(delay, trans_index)
#     # create an array to store multiprocessing results
#     frames = [None] * len(string_list)
#     # create a pool to dispatch frames encoding
#     pool1 = multiprocessing.Pool(processes=multiprocessing.cpu_count())  # use up all the cores.
#
#     for i, s in enumerate(string_list):
#         frames[i] = pool1.apply_async(self.gen_qr_render_frame, args=(qr, s, width, height, render,))
#
#     # join the pool
#     pool1.close()
#     pool1.join()
#
#     for i in range(len(string_list)):
#         surface.write(control + frames[i].get())
#
#     surface.save(output_gif_path)
#     surface.close()
#     return
#
#
# @staticmethod
#     def decode_from_bytes(input_gif_path, output_file_path):
#         """
#         Decode the GIF to recover its binary file entity.
#
#         :param input_gif_path: input GIF file
#         :param output_file_path: output binary file, use extension to decide file type.
#         :return: None
#         """
#         if type(input_gif_path) is str:
#             img = Image.open(input_gif_path)  # GIF file
#         else:
#             return
#
#         decoded_string = b''
#         frame_count = 0
#         for frame in ImageSequence.Iterator(img):
#             frame_count += 1
#             if frame_count < 2:
#                 continue  # skip the first black frame
#             # the decode CV lib relies on the dimensions, 1px width cannot be recognized
#             (width, height) = (frame.width * 2, frame.height * 2)
#             im_resized = frame.resize((width, height))
#             decoded = QRdecode(im_resized)
#             decoded_string += decoded[0].data
#
#         print('total frame count is', str(frame_count))
#         file_bin = decoded_string
#         with open(output_file_path, 'wb') as f:
#             f.write(file_bin)
#         f.close()
#         return