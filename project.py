from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, MenuItem, User

app = Flask(__name__)
DB_NAME = 'sqlite:///itemCatalog.db'

# Connect to Database and create database session
engine = create_engine(DB_NAME)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine) 
session = DBSession()
#potential error to solve: need to make the objects able to be used in different threds. 
#Right now if you reload the page or hit the endpoint again you get an error

####################
# JSON ENPOINTS
####################
#JSON endpoint to view all catergories
@app.route('/category/json')
@app.route('/category/JSON')
def categoryListJSON():
    #query all categorys 
    categorys =  session.query(Category).all()
    return jsonify(categorys = [c.serialize for c in categorys])

#JSON endpoint to view all items corresponding to a specific category id
@app.route('/category/<int:category_id>/menu/JSON')
@app.route('/category/<int:category_id>/menu/json')
def categoryItemsJSON(category_id):
    #query a specific category from the id taken in
    category = session.query(Category).filter_by(id=category_id).one()
    
    #in the items table query all items with this specific category id
    items = session.query(MenuItem).filter_by(
        category_id = category_id).all()
    #convert your list of objects to json
    return jsonify(MenuItems = [i.serialize for i in items])
    
    #Not working
#JSON endpoint to view one specific item for a specific category
@app.route('/category/<int:category_id>/menu/<int:menu_id>/JSON')
@app.route('/category/<int:category_id>/menu/<int:menu_id>/json')
def menuItemJson(category_id, menu_id):
    #query a specific menu item
    menu_item = session.query(MenuItem).filter_by(menu_id).one()
    return jsonify(a_menu_item = menu_item.serialize)


#START SERVER ON PORT 5000
if __name__ == '__main__':
    # app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
