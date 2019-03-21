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
User1 = User(name="test man", email="test@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

#category 1
catergory1 =  Category(user_id=1, name="Legs", id=1)
session.add(catergory1)
session.commit()

#items for category1
item1 = MenuItem(user_id=1, name="Squat Rack", description="Grow big legs witht this world class squat rack",
                    price="$750.00", category=catergory1)
session.add(item1)
session.commit()

item2 = MenuItem(user_id=1, name="Leg Press", description="Gain quad strength through pressing motions",
                    price="$250.00", category=catergory1)
session.add(item2)
session.commit()

#category 2
catergory2 =  Category(user_id=1, name="Chest", id=2)
session.add(catergory2)
session.commit()

#items for catgory 2
item1 = MenuItem(user_id =1 , name = "Bench Press", description= "Get pecs through pressing with your chest",
                            price="$350.00", category=catergory2)
session.add(item1)
session.commit()
item2 = MenuItem(user_id =1 , name = "Incline Press", description= "Get Upper pecs through pressing with your chest",
                            price="$370.00", category=catergory2)
session.add(item2)
session.commit()


print "added items!"
