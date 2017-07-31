from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine('sqlite:///itemize.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


class SessionManager(object):
    def __init__(self):
        self.session = DBSession()
