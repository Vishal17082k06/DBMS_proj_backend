from flask import Blueprint
from app.controllers.main_controller import home

main_bp = Blueprint('main', __name__)

main_bp.route('/', methods=['GET'])(home)
