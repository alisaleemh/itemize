from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
from session_manager import SessionManager


db = SessionManager()

restaurantMenu_bp = Blueprint('restaurantMenu', __name__,
                        template_folder='templates')
@restaurantMenu_bp.route('/')
@restaurantMenu_bp.route('/restaurant/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('menu.html', restaurant=restaurant, items=items)
