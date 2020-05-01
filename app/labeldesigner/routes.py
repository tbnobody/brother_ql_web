import os

from flask import current_app, render_template, request, make_response
from PIL import Image, ImageDraw, ImageFont

from brother_ql.devicedependent import label_type_specs, label_sizes
from brother_ql.devicedependent import ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL
from brother_ql import BrotherQLRaster, create_label

from app.labeldesigner import bp
from app.utils import convert_image_to_bw, pdffile_to_image, imgfile_to_image, image_to_png_bytes
from app import BACKEND_CLASS, FONTS

import qrcode

LINE_SPACINGS = (100, 150, 200, 250, 300)

# Don't change as brother_ql is using this DPI value
DEFAULT_DPI = 300

LABEL_SIZES = [(
    name,
    label_type_specs[name]['name'],
    (label_type_specs[name]['kind'] in (
        ROUND_DIE_CUT_LABEL,))  # True if round label
) for name in label_sizes]


@bp.route('/')
def index():
    return render_template('labeldesigner.html',
                           font_family_names=FONTS.fontlist(),
                           label_sizes=LABEL_SIZES,
                           default_label_size=current_app.config['LABEL_DEFAULT_SIZE'],
                           default_font_size=current_app.config['LABEL_DEFAULT_SIZE'],
                           default_orientation=current_app.config['LABEL_DEFAULT_ORIENTATION'],
                           default_qr_size=current_app.config['LABEL_DEFAULT_QR_SIZE'],
                           default_font_family=current_app.config['LABEL_DEFAULT_FONT_FAMILY'],
                           line_spacings=LINE_SPACINGS,
                           default_line_spacing=current_app.config['LABEL_DEFAULT_LINE_SPACING'],
                           default_dpi=DEFAULT_DPI
                           )


@bp.route('/api/font/styles', methods=['POST', 'GET'])
def get_font_styles():
    font = request.values.get(
        'font', current_app.config['LABEL_DEFAULT_FONT_FAMILY'])
    return FONTS.fonts[font]


@bp.route('/api/preview', methods=['POST', 'GET'])
def get_preview_from_image():
    context = get_label_context(request)
    im = create_label_im(**context)

    return_format = request.values.get('return_format', 'png')

    if return_format == 'base64':
        import base64
        response = make_response(base64.b64encode(image_to_png_bytes(im)))
        response.headers.set('Content-type', 'text/plain')
        return response
    else:
        response = make_response(image_to_png_bytes(im))
        response.headers.set('Content-type', 'image/png')
        return response


@bp.route('/api/print', methods=['POST', 'GET'])
def print_text():
    """
    API to print a label

    returns: JSON

    Ideas for additional URL parameters:
    - alignment
    """

    return_dict = {'success': False}

    try:
        context = get_label_context(request)
    except LookupError as e:
        return_dict['error'] = e.msg
        return return_dict

    if context['text'] is None:
        return_dict['error'] = 'Please provide the text for the label'
        return return_dict

    im = create_label_im(**context)
    if current_app.config['DEBUG']:
        im.save('sample-out.png')

    if context['kind'] == ENDLESS_LABEL:
        rotate = 0 if context['orientation'] == 'standard' else 90
    elif context['kind'] in (ROUND_DIE_CUT_LABEL, DIE_CUT_LABEL):
        rotate = 'auto'

    qlr = BrotherQLRaster(current_app.config['PRINTER_MODEL'])
    red = False
    if 'red' in context['label_size']:
        red = True

    for cnt in range(1, context['print_count']+1):
        if context['cut_once'] == False:
            cut = True
        elif context['cut_once'] == True and cnt == context['print_count']:
            cut = True
        else:
            cut = False

        create_label(
            qlr,
            im,
            context['label_size'],
            red=red,
            threshold=context['threshold'],
            cut=cut,
            rotate=rotate)

    if not current_app.config['DEBUG']:
        try:
            be = BACKEND_CLASS(current_app.config['PRINTER_PRINTER'])
            be.write(qlr.data)
            be.dispose()
            del be
        except Exception as e:
            return_dict['message'] = str(e)
            current_app.logger.warning('Exception happened: %s', e)
            return return_dict

    return_dict['success'] = True
    if current_app.config['DEBUG']:
        return_dict['data'] = str(qlr.data)
    return return_dict


def get_label_context(request):
    """ might raise LookupError() """

    d = request.values  # UTF-8 decoded form data

    context = {
        'text':          d.get('text', None),
        'font_size': int(d.get('font_size', 100)),
        'font_family':   d.get('font_family'),
        'font_style':    d.get('font_style'),
        'label_size':    d.get('label_size', "62"),
        'kind':          label_type_specs[d.get('label_size', "62")]['kind'],
        'margin':    int(d.get('margin', 10)),
        'threshold': int(d.get('threshold', 70)),
        'align':         d.get('align', 'center'),
        'orientation':   d.get('orientation', 'standard'),
        'margin_top':    float(d.get('margin_top',    24))/100.,
        'margin_bottom': float(d.get('margin_bottom', 45))/100.,
        'margin_left':   float(d.get('margin_left',   35))/100.,
        'margin_right':  float(d.get('margin_right',  35))/100.,
        'print_type':    d.get('print_type', 'text'),
        'qrcode_size':   int(d.get('qrcode_size', 10)),
        'qrcode_correction': d.get('qrcode_correction', 'L'),
        'print_count':       int(d.get('print_count', 1)),
        'print_color':       d.get('print_color', 'black'),
        'line_spacing':      int(d.get('line_spacing', 100)),
        'cut_once':          int(d.get('cut_once', 0)),
    }
    context['margin_top'] = int(context['font_size']*context['margin_top'])
    context['margin_bottom'] = int(
        context['font_size']*context['margin_bottom'])
    context['margin_left'] = int(context['font_size']*context['margin_left'])
    context['margin_right'] = int(context['font_size']*context['margin_right'])

    context['fill_color'] = (
        255, 0, 0) if 'red' in context['label_size'] and context['print_color'] == 'red' else (0, 0, 0)

    context['cut_once'] = True if context['cut_once'] == 1 else False

    qrSwitch = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H
    }
    context['qrcode_correction'] = qrSwitch.get(
        context['qrcode_correction'], qrcode.constants.ERROR_CORRECT_L)

    def get_uploaded_image(image):
        try:
            name, ext = os.path.splitext(image.filename)
            if ext.lower() in ('.png', '.jpg', '.jpeg'):
                image = imgfile_to_image(image)
                return convert_image_to_bw(image, 200)
            elif ext.lower() in ('.pdf'):
                image = pdffile_to_image(image, DEFAULT_DPI)
                return convert_image_to_bw(image, 200)
            else:
                return None
        except AttributeError:
            return None

    context['upload_image'] = get_uploaded_image(
        request.files.get('image', None))

    def get_font_path(font_family_name, font_style_name):
        try:
            if font_family_name is None or font_style_name is None:
                font_family_name = current_app.config['LABEL_DEFAULT_FONT_FAMILY']
                font_style_name = current_app.config['LABEL_DEFAULT_FONT_STYLE']
            font_path = FONTS.fonts[font_family_name][font_style_name]
        except KeyError:
            raise LookupError("Couln't find the font & style")
        return font_path

    context['font_path'] = get_font_path(
        context['font_family'], context['font_style'])

    def get_label_dimensions(label_size):
        try:
            ls = label_type_specs[context['label_size']]
        except KeyError:
            raise LookupError("Unknown label_size")
        return ls['dots_printable']

    width, height = get_label_dimensions(context['label_size'])
    if height > width:
        width, height = height, width
    if context['orientation'] == 'rotated':
        height, width = width, height
    context['width'], context['height'] = width, height

    return context


def create_qr_code(text, size, correction, fill_color):
    qr = qrcode.QRCode(
        version=1,
        error_correction=correction,
        box_size=size,
        border=0,
    )
    qr.add_data(text)
    qr.make(fit=True)
    qr_img = qr.make_image(
        fill_color='red' if (255, 0, 0) == fill_color else 'black',
        back_color="white")
    return qr_img


def create_label_im(text, **kwargs):
    if kwargs['print_type'] == 'qrcode' or kwargs['print_type'] == 'qrcode_text':
        img = create_qr_code(
            text,
            kwargs['qrcode_size'],
            kwargs['qrcode_correction'],
            kwargs['fill_color']
        )
    elif kwargs['print_type'] == 'image':
        img = kwargs['upload_image']
    else:
        img = None

    if kwargs['print_type'] == 'qrcode':
        return assemble_label_im(text, img, False, **kwargs)
    elif kwargs['print_type'] == 'qrcode_text':
        return assemble_label_im(text, img, True, **kwargs)
    elif kwargs['print_type'] == 'image':
        return assemble_label_im(text, img, False, **kwargs)
    else:
        return assemble_label_im(text, None, True, **kwargs)


def assemble_label_im(text, image, include_text, **kwargs):
    if image is not None:
        image_width, image_height = image.size
    else:
        image_width, image_height = (0, 0)

    label_type = kwargs['kind']

    if include_text:
        im_font = ImageFont.truetype(kwargs['font_path'], kwargs['font_size'])
        im = Image.new('L', (20, 20), 'white')
        draw = ImageDraw.Draw(im)
        # workaround for a bug in multiline_textsize()
        # when there are empty lines in the text:
        lines = []
        for line in text.split('\n'):
            if line == '':
                line = ' '
            lines.append(line)
        text = '\n'.join(lines)
        textsize = draw.multiline_textsize(text, font=im_font, spacing=int(
            kwargs['font_size']*((kwargs['line_spacing'] - 100) / 100)))
    else:
        textsize = (0, 0)

    width, height = kwargs['width'], kwargs['height']
    if kwargs['orientation'] == 'standard':
        if label_type in (ENDLESS_LABEL,):
            height = image_height + \
                textsize[1] + kwargs['margin_top'] + kwargs['margin_bottom']
    elif kwargs['orientation'] == 'rotated':
        if label_type in (ENDLESS_LABEL,):
            width = image_width + \
                textsize[0] + kwargs['margin_left'] + kwargs['margin_right']

    if kwargs['orientation'] == 'standard':
        if label_type in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
            vertical_offset = (height - image_height - textsize[1])//2
            vertical_offset += (kwargs['margin_top'] -
                                kwargs['margin_bottom'])//2
        else:
            vertical_offset = kwargs['margin_top']

        vertical_offset += image_height
        horizontal_offset = max((width - textsize[0])//2, 0)
        horizontal_offset_image = (width - image_width)//2
        vertical_offset_image = kwargs['margin_top']

    elif kwargs['orientation'] == 'rotated':
        vertical_offset = (height - textsize[1])//2
        vertical_offset += (kwargs['margin_top'] - kwargs['margin_bottom'])//2
        if label_type in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
            horizontal_offset = max((width - image_width - textsize[0])//2, 0)
        else:
            horizontal_offset = kwargs['margin_left']
        horizontal_offset += image_width
        horizontal_offset_image = kwargs['margin_left']
        vertical_offset_image = (height - image_height)//2

    offset = horizontal_offset, vertical_offset
    image_offset = horizontal_offset_image, vertical_offset_image

    im = Image.new('RGB', (width, height), 'white')

    if image is not None:
        im.paste(image, image_offset)

    if include_text:
        draw = ImageDraw.Draw(im)
        draw.multiline_text(
            offset,
            text,
            kwargs['fill_color'],
            font=im_font,
            align=kwargs['align'],
            spacing=int(kwargs['font_size']*((kwargs['line_spacing'] - 100) / 100)))

    return im
