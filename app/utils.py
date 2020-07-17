# -*- coding: utf-8 -*-

from PIL import Image
from io import BytesIO
from pdf2image import convert_from_bytes


def convert_image_to_bw(image, threshold):
    fn = lambda x : 255 if x > threshold else 0
    return image.convert('L').point(fn, mode='1') # convert to black and white

def convert_image_to_grayscale(image):
    return image.convert('L') # convert to greyscale

def imgfile_to_image(file):
    s = BytesIO()
    file.save(s)
    im = Image.open(s)
    return im


def pdffile_to_image(file, dpi):
    s = BytesIO()
    file.save(s)
    s.seek(0)
    im = convert_from_bytes(
        s.read(),
        dpi = dpi
    )[0]
    return im


def image_to_png_bytes(im):
    image_buffer = BytesIO()
    im.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return image_buffer.read()