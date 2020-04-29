from flask import Blueprint

bp = Blueprint('errors', __name__, template_folder = 'templates')

from app.errors import handlers