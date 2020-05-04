import os

from flask import current_app, render_template, request, make_response

from brother_ql.devicedependent import label_type_specs, label_sizes
from brother_ql.devicedependent import ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL

from app.labeldesigner import bp
from app.utils import convert_image_to_bw, pdffile_to_image, imgfile_to_image, image_to_png_bytes
from app import FONTS

from .label import SimpleLabel, LabelContent, LabelOrientation, LabelType
from .printer import PrinterQueue

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
    label = create_label_from_request(request)
    im = label.generate()

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
        printer = create_printer_from_request(request)
        label = create_label_from_request(request)
        print_count = int(request.values.get('print_count', 1))
        cut_once = int(request.values.get('cut_once', 0)) == 1
    except Exception as e:
        return_dict['message'] = str(e)
        current_app.logger.error('Exception happened: %s', e)
        return return_dict

    printer.add_label_to_queue(label, print_count, cut_once)

    try:
        printer.process_queue()
    except Exception as e:
        return_dict['message'] = str(e)
        current_app.logger.error('Exception happened: %s', e)
        return return_dict

    return_dict['success'] = True
    return return_dict


def create_printer_from_request(request):
    d = request.values
    context = {
        'label_size': d.get('label_size', '62')
    }

    return PrinterQueue(
        model = current_app.config['PRINTER_MODEL'],
        device_specifier = current_app.config['PRINTER_PRINTER'],
        label_size = context['label_size']
    )


def create_label_from_request(request):
    d=request.values
    context={
        'label_size': d.get('label_size', '62'),
        'print_type': d.get('print_type', 'text'),
        'label_orientation': d.get('orientation', 'standard'),
        'kind': label_type_specs[d.get('label_size', "62")]['kind'],
        'margin_top': float(d.get('margin_top', 24))/100.,
        'margin_bottom': float(d.get('margin_bottom', 45))/100.,
        'margin_left': float(d.get('margin_left', 35))/100.,
        'margin_right': float(d.get('margin_right', 35))/100.,
        'text': d.get('text', None),
        'align': d.get('align', 'center'),
        'qrcode_size': int(d.get('qrcode_size', 10)),
        'qrcode_correction': d.get('qrcode_correction', 'L'),
        'font_size': int(d.get('font_size', 100)),
        'line_spacing': int(d.get('line_spacing', 100)),
        'font_family': d.get('font_family'),
        'font_style': d.get('font_style'),
        'print_color': d.get('print_color', 'black'),
    }

    def get_label_dimensions(label_size):
        try:
            ls = label_type_specs[context['label_size']]
        except KeyError:
            raise LookupError("Unknown label_size")
        return ls['dots_printable']

    def get_font_path(font_family_name, font_style_name):
        try:
            if font_family_name is None or font_style_name is None:
                font_family_name = current_app.config['LABEL_DEFAULT_FONT_FAMILY']
                font_style_name = current_app.config['LABEL_DEFAULT_FONT_STYLE']
            font_path = FONTS.fonts[font_family_name][font_style_name]
        except KeyError:
            raise LookupError("Couln't find the font & style")
        return font_path

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

    if context['print_type'] == 'text':
        label_content = LabelContent.TEXT_ONLY
    elif context['print_type'] == 'qrcode':
        label_content = LabelContent.QRCODE_ONLY
    elif context['print_type'] == 'qrcode_text':
        label_content = LabelContent.TEXT_QRCODE
    else:
        label_content = LabelContent.IMAGE

    if context['label_orientation'] == 'rotated':
        label_orientation = LabelOrientation.ROTATED
    else:
        label_orientation = LabelOrientation.STANDARD

    if context['kind'] == ENDLESS_LABEL:
        label_type = LabelType.ENDLESS_LABEL
    elif context['kind'] == DIE_CUT_LABEL:
        label_type = LabelType.DIE_CUT_LABEL
    else:
        label_type = LabelType.ROUND_DIE_CUT_LABEL

    width, height = get_label_dimensions(context['label_size'])
    if height > width:
        width, height = height, width
    if label_orientation == LabelOrientation.ROTATED:
        height, width = width, height

    return SimpleLabel(
        width=width,
        height=height,
        label_content=label_content,
        label_orientation=label_orientation,
        label_type=label_type,
        label_margin=(
            int(context['font_size']*context['margin_left']),
            int(context['font_size']*context['margin_right']),
            int(context['font_size']*context['margin_top']),
            int(context['font_size']*context['margin_bottom'])
        ),
        fore_color=
            (255, 0, 0) if 'red' in context['label_size'] and context['print_color'] == 'red'
            else (0, 0, 0),
        text=context['text'],
        text_align=context['align'],
        qr_size=context['qrcode_size'],
        qr_correction=context['qrcode_correction'],
        image=get_uploaded_image(request.files.get('image', None)),
        font_path=get_font_path(context['font_family'], context['font_style']),
        font_size=context['font_size'],
        line_spacing=context['line_spacing']
    )
