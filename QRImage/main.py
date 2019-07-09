import CuteRMP as cr
import os
from PIL import Image


def main():
    text = '孙辰表示不服'
    # image = '../test_images/xhn.jpg'

    image = '../worship.gif'
    duration = Image.open(image).info.get('duration')

    # a series of image frames in PIL format
    # rgba = (100, 50, 100, 188)
    rgba = (0, 0, 0, 255)
    output = cr.produce(text, image, err_crt=1, rgba=rgba, colourful=True, padding=12)

    # single frame
    # output[0].save('../out.jpg')

    # animated
    transparency = 255
    output[0].save('../out_temp.gif', save_all=True, optimize=False, append_images=output[1:], disposal=2, version='GIF89a', loop=0, duration=duration)

    additional_args = ' --colors 64 --resize-width 320'
    os.system('gifsicle' + ' -O1' + additional_args + ' -i ' + '../out_temp.gif' + ' -o ' + '../out.gif')


if __name__ == '__main__':
    main()
