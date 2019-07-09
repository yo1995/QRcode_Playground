from PIL import Image
from PIL import ImageEnhance
from PIL import ImageSequence
import qrcode
import imageio
import multiprocessing


def color_replace(image, color):
    """Replace black with other color

    :color: custom color (r,g,b,a)
    :image: image to replace color
    :returns: TODO

    """
    pixels = image.load()
    size = image.size[0]
    for width in range(size):
        for height in range(size):
            r, g, b, a = pixels[width, height]
            if (r, g, b, a) == (0,0,0,255):
                pixels[width,height] = color
            else:
                pixels[width,height] = (r,g,b,color[3])


def decode_video_file(filename, crop=False, crop_box=None):
    """

    :param filename: video filename
    :param crop: either crop or not
    :param crop_box: the crop rectangle defined in PIL format
    :return: list of images
    """
    image_stack = []
    i = 0
    vid = imageio.get_reader(filename, 'ffmpeg')
    for img in enumerate(vid):
        i = i + 1
        img = Image.fromarray(img[1])
        img = img.convert('RGBA')
        if crop:
            img = img.crop(crop_box)
        image_stack.append(img)
    if i > 120:
        info_str = 'total frames is: ' + str(i) + ', you might want to change max_frames setting.'
    else:
        info_str = 'total frames is: ' + str(i)
    print(info_str)

    if image_stack[0].size[0] > 2000 or image_stack[0].size[1] > 2000:
        print('input dimension too large for GIF! either crop or resize. abort.')
        exit(-1)
    return image_stack


def produce(txt,img,ver=5,err_crt = qrcode.constants.ERROR_CORRECT_H,bri = 1.0, cont = 1.0,\
        colourful = False, rgba = (0,0,0,255),pixelate = False, padding=12):
    """Produce QR code

    :txt: QR text
    :img: Image path / Image object
    :ver: QR version
    :err_crt: QR error correct
    :bri: Brightness enhance
    :cont: Contrast enhance
    :colourful: If colourful mode
    :rgba: color to replace black
    :pixelate: pixelate
    :returns: list of produced image

    """
    if type(img) is Image.Image:
        pass
    elif type(img) is str:
        if '.mp4' in img or '.mov' in img:
            img = decode_video_file(img)  # video file
        else:
            img = Image.open(img)  # GIF file or single frame image
    else:
        return []

    frame_count = 0
    for _ in ImageSequence.Iterator(img):
        frame_count += 1

    # if there are not too many images, just linear block process
    if frame_count < 5:
        frames = [produce_impl(txt, frame.copy(), ver, err_crt, bri, cont, colourful, rgba, pixelate, padding) for frame in ImageSequence.Iterator(img)]
        return frames

    # else to create a pool
    pool1 = multiprocessing.Pool(processes=multiprocessing.cpu_count())  # use up all the cores.
    procs = [None] * frame_count
    frames = [None] * frame_count

    i = 0
    for frame in ImageSequence.Iterator(img):
        procs[i] = pool1.apply_async(produce_impl, args=(txt, frame.copy(), ver, err_crt, bri, cont, colourful, rgba, pixelate, padding))
        i += 1
        print('Frame ', str(i), ' added to pool.')
    # wait until all frames are done
    pool1.close()
    pool1.join()

    for i in range(frame_count):
        frames[i] = procs[i].get()

    return frames


def produce_impl(txt, img, ver=5, err_crt=qrcode.constants.ERROR_CORRECT_H, bri=1.0, cont=1.0, colourful=False, rgba=(0,0,0,255), pixelate=False, padding=12, animated=False):
    """Produce QR code

    :txt: QR text
    :img: Image object
    :ver: QR version
    :err_crt: QR error correct
    :bri: Brightness enhance
    :cont: Contrast enhance
    :colourful: If colourful mode
    :rgba: color to replace black
    :pixelate: pixelate
    :returns: Produced image

    """
    qr = qrcode.QRCode(version=ver, error_correction=err_crt, box_size=3)
    qr.add_data(txt)
    qr.make(fit=True)
    img_qr = qr.make_image().convert('RGBA')
    if colourful and (rgba != (0, 0, 0, 255)):
        color_replace(img_qr, rgba)
    if animated:
        img_img = img.convert('RGB').convert('RGBA')  # the notorious Pilow GIF RGBA conversion bug. one workaround is in my emoticon generator
    else:
        img_img = img.convert('RGBA')

    img_img_size = None
    img_size = img_qr.size[0] - padding * 2
    if img_img.size[0] < img_img.size[1]:
        img_img_size = img_img.size[0]
    else:
        img_img_size = img_img.size[1]

    img_enh = img_img.crop((0, 0, img_img_size, img_img_size))
    enh = ImageEnhance.Contrast(img_enh)
    img_enh = enh.enhance(cont)
    enh = ImageEnhance.Brightness(img_enh)
    img_enh = enh.enhance(bri)
    if not colourful:
        if pixelate:
            img_enh = img_enh.convert('1').convert('RGBA')
        else:
            img_enh = img_enh.convert('L').convert('RGBA')
    img_frame = img_qr
    img_enh = img_enh.resize((img_size * 10, img_size * 10))
    img_enh_l = img_enh.convert("L").resize((img_size, img_size))
    img_frame_l = img_frame.convert("L")

    comp_pad = 12 - padding
    # fill in not important pixels with image background
    for x in range(0, img_size):
        for y in range(0, img_size):
            if comp_pad <= x < 21 + comp_pad and (comp_pad <= y < 21 + comp_pad or img_size - comp_pad > y > img_size - 22 - comp_pad):
                continue
            if img_size - comp_pad > x > img_size - 22 - comp_pad and (comp_pad <= y < 21 + comp_pad):
                continue
            if (x % 3 == 1 and y % 3 == 1):
                if (img_frame_l.getpixel((x + padding, y + padding)) > 70 and img_enh_l.getpixel((x, y)) < 185) \
                        or (img_frame_l.getpixel((x + padding, y + padding)) < 185 and img_enh_l.getpixel((x, y)) > 70):
                    continue
            img_frame.putpixel((x + padding, y + padding), (0, 0, 0, 0))
    pos = qrcode.util.pattern_position(qr.version)
    img_qr2 = qr.make_image().convert("RGBA")

    # the lower right locate box
    if colourful and (rgba != (0, 0, 0, 0)):
        color_replace(img_qr2, rgba)
    for i in pos:
        for j in pos:
            if (i == 6 and j == pos[-1]) or (j == 6 and i == pos[-1]) \
                    or (i == 6 and j == 6):
                continue
            else:
                rect = (3 * (i - 2) + 12, 3 * (j - 2) + 12, 3 * (i + 3) + 12, 3 * (j + 3) + 12)
                img_tmp = img_qr2.crop(rect)
                img_frame.paste(img_tmp, rect)

    img_res = Image.new("RGBA", (img_frame.size[0] * 10, img_frame.size[1] * 10), (255, 255, 255, 255))
    img_res.paste(img_enh, (padding * 10, padding * 10), img_enh)
    img_frame = img_frame.resize((img_frame.size[0] * 10, img_frame.size[1] * 10))
    img_res.paste(img_frame, (0, 0), img_frame)
    img_res = img_res.convert('RGB')
    if pixelate:
        return img_res.resize(img_qr.size).resize((img_img_size, img_img_size))
    return img_res


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Combine your QR code with custom picture")
    parser.add_argument("image")
    parser.add_argument("text", help="QRcode Text.")
    parser.add_argument("-o", "--output", help="Name of output file.")
    parser.add_argument("-v", "--version", type=int, help="QR version.In range of [1-40]")
    parser.add_argument("-e", "--errorcorrect", choices={"L","M","Q","H"}, help="Error correct")
    parser.add_argument("-b", "--brightness", type=float, help="Brightness enhance")
    parser.add_argument("-c", "--contrast", type=float, help="Contrast enhance")
    parser.add_argument("-C", "--colourful", action="store_true",help="colourful mode")
    parser.add_argument("-r", "--rgba", nargs=4, metavar=('R','G','B','A'),type = int, help="color to replace black")
    parser.add_argument("-p", "--pixelate", action="store_true",help="pixelate")
    args = parser.parse_args()

    img = args.image
    txt = args.text
    output = args.output if args.output else 'qr.png'
    ec = qrcode.constants.ERROR_CORRECT_H
    if args.errorcorrect:
        ec_raw = args.errorcorrect
        if ec_raw == 'L':
            ec = qrcode.constants.ERROR_CORRECT_L
        if ec_raw == 'M':
            ec = qrcode.constants.ERROR_CORRECT_M
        if ec_raw == 'Q':
            ec = qrcode.constants.ERROR_CORRECT_Q
    ver = 5
    if args.version:
        if args.version >= 1 and args.version <= 40:
            ver = args.version
    cont = args.contrast if args.contrast else 1.0
    bri = args.brightness if args.brightness else 1.0
    colr = True if args.colourful else False
    pixelate = True if args.pixelate else False
    if colr :
        if args.rgba:
          rgba = tuple(args.rgba)
        else:
            rgba = (0,0,0,255)
    else:
        rgba = (0,0,0,255)
    frames = produce(txt,img,ver,ec,bri, cont ,colourful = colr,rgba=rgba,pixelate = pixelate)
    if len(frames) == 1 or output.upper()[-3:] != "GIF":
        frames[0].save(output)
    elif len(frames) > 1:
        frames[0].save(output,save_all=True,append_images=frames[1:],duration=100,optimize=True)

if __name__ == "__main__":
    main()
