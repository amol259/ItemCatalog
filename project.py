from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, MenuItem, User

app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///itemCatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


####################
# JSON ENPOINTS
####################
@app.route('/category/json')
@app.route('/category/JSON')
def catergoryListJSON():
    #query all categorys 
    catergorys =  session.query(Category).all()
    return jsonify(categorys = [c.serialize for c in catergorys])



# # JSON APIs to view Restaurant Information
# @app.route('/category/<int:category_id>/menu/JSON')
# def categoryListJSON(category_id):
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     items = session.query(MenuItem).filter_by(
#         restaurant_id=restaurant_id).all()
#     return jsonify(MenuItems=[i.serialize for i in items])


# @app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
# def menuItemJSON(restaurant_id, menu_id):
#     Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
#     return jsonify(Menu_Item=Menu_Item.serialize)


# @app.route('/restaurant/JSON')
# def restaurantsJSON():
#     restaurants = session.query(Restaurant).all()
#     return jsonify(restaurants=[r.serialize for r in restaurants])


# # Show all restaurants
# @app.route('/')
# @app.route('/restaurant/')
# def showRestaurants():
#     restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
#     # if 'username' not in login_session:
#     #     return render_template('publicrestaurants.html', restaurants=restaurants)
#     # else:
#     return render_template('restaurants.html', restaurants=restaurants)


# # JSON APIs to view Restaurant Information
# @app.route('/category/<int:category_id>/menu/JSON')
# def categoryListJSON(category_id):
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     items = session.query(MenuItem).filter_by(
#         restaurant_id=restaurant_id).all()
#     return jsonify(MenuItems=[i.serialize for i in items])


# @app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
# def menuItemJSON(restaurant_id, menu_id):
#     Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
#     return jsonify(Menu_Item=Menu_Item.serialize)


# @app.route('/restaurant/JSON')
# def restaurantsJSON():
#     restaurants = session.query(Restaurant).all()
#     return jsonify(restaurants=[r.serialize for r in restaurants])


# # Show all restaurants
# @app.route('/')
# @app.route('/restaurant/')
# def showRestaurants():
#     restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
#     # if 'username' not in login_session:
#     #     return render_template('publicrestaurants.html', restaurants=restaurants)
#     # else:
#     return render_template('restaurants.html', restaurants=restaurants)



#START SERVER ON PORT 5000
if __name__ == '__main__':
    # app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
