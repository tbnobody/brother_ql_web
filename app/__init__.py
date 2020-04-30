#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a web service to print labels on Brother QL label printers.
"""

import sys
import logging
import random
import json
import argparse

from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap

from brother_ql.devicedependent import models, label_sizes
from brother_ql.backends import backend_factory, guess_backend

from . import fonts


app = Flask(__name__)

logger = logging.getLogger(__name__)


try:
    with open('config.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)
except FileNotFoundError as e:
    with open('config.example.json', encoding='utf-8') as fh:
        CONFIG = json.load(fh)


@app.route('/')
def index():
    return redirect(url_for('labeldesigner.labeldesigner'))


def create_app():
    main()

    from app.labeldesigner import bp as labeldesigner_bp
    app.register_blueprint(labeldesigner_bp)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app


def main():
    global DEBUG, FONTS, BACKEND_CLASS, CONFIG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=False)
    parser.add_argument(
        '--loglevel', type=lambda x: getattr(logging, x.upper()), default=False)
    parser.add_argument('--font-folder', default=False,
                        help='folder for additional .ttf/.otf fonts')
    parser.add_argument('--default-label-size', default=False,
                        help='Label size inserted in your printer. Defaults to 62.')
    parser.add_argument('--default-orientation', default=False, choices=('standard', 'rotated'),
                        help='Label orientation, defaults to "standard". To turn your text by 90°, state "rotated".')
    parser.add_argument('--model', default=False, choices=models,
                        help='The model of your printer (default: QL-500)')
    parser.add_argument('printer',  nargs='?', default=False,
                        help='String descriptor for the printer to use (like tcp://192.168.0.23:9100 or file:///dev/usb/lp0)')
    args = parser.parse_args()

    if args.printer:
        CONFIG['PRINTER']['PRINTER'] = args.printer

    if args.port:
        PORT = args.port
    else:
        PORT = CONFIG['SERVER']['PORT']

    if args.loglevel:
        LOGLEVEL = args.loglevel
    else:
        LOGLEVEL = CONFIG['SERVER']['LOGLEVEL']

    if LOGLEVEL == 'DEBUG':
        DEBUG = True
    else:
        DEBUG = False

    if args.model:
        CONFIG['PRINTER']['MODEL'] = args.model

    if args.default_label_size:
        CONFIG['LABEL']['DEFAULT_SIZE'] = args.default_label_size

    if args.default_orientation:
        CONFIG['LABEL']['DEFAULT_ORIENTATION'] = args.default_orientation

    if args.font_folder:
        ADDITIONAL_FONT_FOLDER = args.font_folder
    else:
        ADDITIONAL_FONT_FOLDER = CONFIG['SERVER']['ADDITIONAL_FONT_FOLDER']

    logging.basicConfig(level=LOGLEVEL)

    try:
        selected_backend = guess_backend(CONFIG['PRINTER']['PRINTER'])
    except ValueError:
        parser.error(
            "Couln't guess the backend to use from the printer string descriptor")
    BACKEND_CLASS = backend_factory(selected_backend)['backend_class']

    if CONFIG['LABEL']['DEFAULT_SIZE'] not in label_sizes:
        parser.error(
            "Invalid --default-label-size. Please choose on of the following:\n:" + " ".join(label_sizes))

    FONTS = fonts.Fonts()
    FONTS.scan_global_fonts()
    if ADDITIONAL_FONT_FOLDER:
        FONTS.scan_fonts_folder(ADDITIONAL_FONT_FOLDER)

    if not FONTS.fonts_available():
        sys.stderr.write(
            "Not a single font was found on your system. Please install some or use the \"--font-folder\" argument.\n")
        sys.exit(2)

    for font in CONFIG['LABEL']['DEFAULT_FONTS']:
        if font['family'] in FONTS.fonts.keys() and font['style'] in FONTS.fonts[font['family']].keys():
            CONFIG['LABEL']['DEFAULT_FONTS'] = font
            logger.debug(
                "Selected the following default font: {}".format(font))
            break
        else:
            pass
    if CONFIG['LABEL']['DEFAULT_FONTS'] is None:
        sys.stderr.write(
            'Could not find any of the default fonts. Choosing a random one.\n')
        family = random.choice(list(FONTS.fonts.keys()))
        style = random.choice(list(FONTS.fonts[family].keys()))
        CONFIG['LABEL']['DEFAULT_FONTS'] = {'family': family, 'style': style}
        sys.stderr.write('The default font is now set to: {family} ({style})\n'.format(
            **CONFIG['LABEL']['DEFAULT_FONTS']))

    # initialize bootstrap
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    bootstrap = Bootstrap(app)

    app.config['SERVER_HOST'] = CONFIG['SERVER']['HOST']
    app.config['SERVER_PORT'] = PORT
    app.config['DEBUG'] = DEBUG
