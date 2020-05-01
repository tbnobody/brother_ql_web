#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a web service to print labels on Brother QL label printers.
"""

import sys
import random

from flask import Flask
from flask_bootstrap import Bootstrap

from brother_ql.backends import backend_factory, guess_backend

from . import fonts
from config import Config

bootstrap = Bootstrap()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.config.from_pyfile('application.py', silent=True)

    app.logger.setLevel(app.config['LOG_LEVEL'])

    main(app)

    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    bootstrap.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.labeldesigner import bp as labeldesigner_bp
    app.register_blueprint(labeldesigner_bp, url_prefix='/labeldesigner')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app


def main(app):
    global FONTS, BACKEND_CLASS

    try:
        selected_backend = guess_backend(app.config['PRINTER_PRINTER'])
    except ValueError:
        app.logger.error(
            "Couln't guess the backend to use from the printer string descriptor")
    BACKEND_CLASS = backend_factory(selected_backend)['backend_class']

    FONTS = fonts.Fonts()
    FONTS.scan_global_fonts()
    if app.config['FONT_FOLDER']:
        FONTS.scan_fonts_folder(app.config['FONT_FOLDER'])

    if not FONTS.fonts_available():
        app.logger.error(
            "Not a single font was found on your system. Please install some.\n")
        sys.exit(2)

    if app.config['LABEL_DEFAULT_FONT_FAMILY'] in FONTS.fonts.keys() and app.config['LABEL_DEFAULT_FONT_STYLE'] in FONTS.fonts[app.config['LABEL_DEFAULT_FONT_FAMILY']].keys():
        app.logger.debug(
            "Selected the following default font: {}".format(app.config['LABEL_DEFAULT_FONT_FAMILY']))

    else:
        app.logger.warn(
            'Could not find any of the default fonts. Choosing a random one.\n')
        family = random.choice(list(FONTS.fonts.keys()))
        style = random.choice(list(FONTS.fonts[family].keys()))
        app.config['LABEL_DEFAULT_FONT_FAMILY'] = family
        app.config['LABEL_DEFAULT_FONT_STYLE'] = style
        app.logger.warn(
            'The default font is now set to: {} ({})\n'.format(family, style))
