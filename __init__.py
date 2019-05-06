from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, MenuItem, User

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)
DB_NAME = 'sqlite:///catalog.db?check_same_thread=False'

# Connect to Database and create database session
engine = create_engine(DB_NAME)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine) 
session = DBSession()

###################
# LOGIN Routes
###################

# Google client_id
secret_file = json.loads(open('/var/www/FlaskApp/FlaskApp/client_secrets.json', 'r').read())
CLIENT_ID = secret_file['web']['client_id']
APPLICATION_NAME = "Item Catalog"

app.secret_key = 'my unobvious secret key'

# Connect to database
# engine = create_engine(DB_NAME)
engine = create_engine('postgresql://catalog:password@localhost/catalog')

Base.metadata.bind = engine

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token

# Login route, create anit-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)
@app.route('/login')

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    # print "access token received %s " % access_token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# CONNECT - Google login get token
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/FlaskApp/FlaskApp/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        # print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if not create new user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    # print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # reset the user's session
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # token given is invalid
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# User helper functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    print (login_session)
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            if 'gplus_id' in login_session:
                del login_session['gplus_id']
            if 'credentials' in login_session:
                del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        del login_session['provider']
        return redirect(url_for('showCategorys'))
    else:
        return redirect(url_for('showCategorys'))


####################
# JSON END POINTS
####################
#JSON endpoint to view all categories
@app.route('/category/json')
@app.route('/category/JSON')
def categoryListJSON():
    #query all categorys 
    categorys =  session.query(Category).all()
    return jsonify(categorys = [c.serialize for c in categorys])

#JSON endpoint to view all items corresponding to a specific category id
@app.route('/category/<int:category_id>/JSON')
@app.route('/category/<int:category_id>/json')
def categoryItemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(MenuItem).filter_by(
    category_id = category_id).all()
    #convert list of objects to json
    return jsonify(MenuItems = [i.serialize for i in items])
    
#JSON endpoint to view one specific item for a specific category
@app.route('/category/<int:category_id>/menu/<int:menu_id>/JSON')
@app.route('/category/<int:category_id>/menu/<int:menu_id>/json')
def menuItemJson(category_id, menu_id):
    MENU_ITEM = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Item = [MENU_ITEM.serialize])


####################
# HTML END POINTS
####################


#Shows all Category's
@app.route('/category')
@app.route('/')
def showCategorys():
    categorys = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return render_template('categoryList.html', categorys=categorys)
    else:
        return render_template('publicCategory.html', categorys=categorys)

# Create a new Category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCategorys'))
    else:
        return render_template('createCategory.html')


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(
            Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category_id. Please create your own Category in order to edit.');}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            return redirect(url_for('showCategorys'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCategorys', category_id=category_id))
    else:
        return render_template('deleteCategory.html', category=categoryToDelete)

#  Show all items for a specific category
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/menu/')
def showMenu(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(category.user_id)
    items = session.query(MenuItem).filter_by(
        category_id=category_id).all()
    if 'username' not in login_session:
        return render_template('publicmenu.html', items=items, category=category, creator=creator)
    else:
        return render_template('menu.html', items=items, category=category, creator=creator)


# Create a new item for a category
@app.route('/category/<int:category_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(category_id):
    if request.method == 'POST':  # get data from the form
        newItem = MenuItem(
        name=request.form['name'],
        description=request.form['description'],
        price=request.form['price'], 
        category_id=category_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showMenu', category_id=category_id))
    else:
        return render_template('newMenuItem.html', category_id=category_id)

# Edit a menu item
@app.route('/category/<int:category_id>/<int:menu_id>/edit',
           methods=['GET', 'POST'])
def editMenuItem(category_id, menu_id):
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showMenu', category_id=category_id))
    else:
        return render_template(
            'editMenuItem.html', category_id=category_id, menu_id=menu_id, item=editedItem)


#Delete menu item
@app.route('/category/<int:category_id>/<int:menu_id>/delete',
           methods=['GET', 'POST'])
def deleteMenuItem(category_id, menu_id):
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showMenu', category_id=category_id))
    else:
        return render_template('deletemenuitem.html', item=itemToDelete)

#START SERVER ON PORT 5000
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    #app.run(host='0.0.0.0', port=5000)
    app.run()
