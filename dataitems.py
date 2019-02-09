from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, MenuItem, User

engine = create_engine('sqlite:///itemCatalog.db')
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


# Create dummy user
User1 = User(name="test man", email="test@udacity.com")
session.add(User1)
session.commit()

#category 1
catergory1 =  Category(user_id=1, name="Arms")
session.add(catergory1)
session.commit()


#category 2
catergory2 =  Category(user_id=1, name="Legs")
session.add(catergory2)
session.commit()

print "added items!"
