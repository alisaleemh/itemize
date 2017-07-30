from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from session_manager import SessionManager


db = SessionManager()

categoryMenu_bp = Blueprint('categoryMenu', __name__,
                        template_folder='templates')
@categoryMenu_bp.route('/')
@categoryMenu_bp.route('/category/<int:category_id>/')
def categoryMenu(category_id):
    category = db.session.query(Category).filter_by(id=category_id).one()
    items = db.session.query(Item).filter_by(category_id=category.id)
    return render_template('menu.html', category=category, items=items)
