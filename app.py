from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database_setup import Restaurant, MenuItem, User
from session_manager import SessionManager
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

db = SessionManager()

client_secret = 'client_secret.json'
CLIENT_ID = json.loads(
    open(client_secret, 'r').read())['web']['client_id']
APPLICATION_NAME = "menu-site"


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    db.session.add(newUser)
    db.session.commit()
    user = db.session.query(User).filter_by(email=login_session['email'].one())
    return user.id


def getUserInfo(user_id):
    user = db.session.query(User).filter_by(id=user_id).one()
    return user


def getUserId(email):
    try:
        user = db.session.query(User).filter_by(email=email).one
        return user
    except:
        return None


# Login Page


@app.route('/login', methods=['GET', 'POST'])
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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
        oauth_flow = flow_from_clientsecrets(client_secret, scope='')
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

        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])

    return output


@app.route('/gdisconnect')
def gdisconnect():
    if 'username' not in login_session:
        return redirect('/login')
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Sucessfully logged out")
        return redirect(url_for('allRestaurants'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# List of All Restaurants
@app.route('/')
@app.route('/restaurant')
@app.route('/restaurants')
@app.route('/restaurant/all')
@app.route('/restaurants/all')
def allRestaurants():
    restaurants = db.session.query(Restaurant).all()
    if 'username' not in login_session:
        return render_template('publicRestaurants.html', login_session=login_session, restaurants=restaurants)
    else:
        return render_template('privateRestaurants.html', login_session=login_session, restaurants=restaurants)


# Adds a New Restaurant Entry
@app.route('/restaurant/new', methods=['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session:
            return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            newItem = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
            db.session.add(newItem)
            db.session.commit()
            flash("new restaurant menu successfully created")
            return redirect(url_for('allRestaurants'))
    else:
        return render_template('newRestaurant.html')


# Edits a Restaurant Entry
# Input: restaurant_id
@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    editItem = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    username = getUserInfo(editItem.user_id)
    username = getUserInfo(editItem.user_id)

    if username != login_session['username']:
        flash("You are not authorized to delete this restaurant as you don't own it")
        return redirect(url_for('allRestaurants'))

    if username != login_session['username']:
        return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        editItem.name = request.form['name']
        db.session.commit()
        flash("restaurant %s successfully edited" % editItem.name)
        return redirect(url_for('allRestaurants'))
    else:
        return render_template('editRestaurant.html', restaurant_id=restaurant_id)


# Delete a Restaurant
# Input: restaurant_id
@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = db.session.query(Restaurant).filter_by(id=restaurant_id).one()

    if request.method == 'POST':
        db.session.delete(deleteItem)
        db.session.commit()
        flash("restaurant %s successfully deleted" % deleteItem.name)
        return redirect(url_for('allRestaurants'))
    else:
        return render_template('deleteRestaurant.html', item=deleteItem)


# Menu of a Specific Restaurant
# Input: restaurant_id
@app.route('/restaurant/<int:restaurant_id>/')
def showRestaurantMenu(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('showRestaurantMenu.html', restaurant=restaurant, items=items)


# New Menu Item in a Specific Restaurant
# Input: restaurant_id
@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], restaurant_id=restaurant_id)
        db.session.add(newItem)
        db.session.commit()
        flash("new item successfully added")
        return redirect(url_for('showRestaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newMenuItem.html', restaurant_id=restaurant_id)


# Edit a Menu Item in a Specific Restaurant
# Input: restaurant_id, menu_id
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == "POST":
        editItem = db.session.query(MenuItem).filter_by(id=menu_id).one()
        editItem.name = request.form['name']
        db.session.commit()
        flash("menu item successfully edited")
        return redirect(url_for('showRestaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id)


# Delete a Menu Item in a Specific Restaurant
# Input: restaurant_id, menu_id
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = db.session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == "POST":
        db.session.delete(deleteItem)
        db.session.commit()
        flash("menu item successfully deleted")
        return redirect(url_for('showRestaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deleteMenuItem.html', item=deleteItem)

# Return a JSON object of the Menu in a Specific Restaurant
# Input: restaurant_id
@app.route('/restaurant/<int:restaurant_id>/menu/json/')
def restaurantMenuJson(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return jsonify(MenuItems=[i.serialize for i in items])



if __name__ == '__main__':
    app.secret_key = "tatta"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
