from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///itemize.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


User1 = User(
        name="Ali Hussain",
        email="ali.s1995@live.com"
)

User2 = User(
        name="Dane Jones",
        email="danejones@danejones.com"
)

User3 = User(
        name="Jane Doe",
        email="jane@doe.com"
)

session.add(User1, User2, User3)

session.commit()

Category1 = Category(
            name="Shoes",
            user_id=1
)

Category2 = Category(
            name="Shirts",
            user_id=1
)

Category3 = Category(
            name="Jackets",
            user_id=1
)

session.add(Category1, Category2, Category3)
session.commit()


Item1 = Item(
        name="Nike Tanjun",
        description="Nike's basic running/walking",
        category_id=1,
        user_id=1
)

Item2 = Item(
        name="Adidas Runner",
        description="Adidas's basic running/walking",
        category_id=1,
        user_id=1
)

Item3 = Item(
        name="Puma Poom",
        description="Puma's basic running/walking",
        category_id=1,
        user_id=1
)

session.add(Item1, Item2, Item3)
session.commit()
