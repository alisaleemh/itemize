from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database_setup import Category, Item, User
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
        return redirect(url_for('allCategories'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# List of All Categories
@app.route('/')
@app.route('/category')
def allCategories():
    categories = db.session.query(Category).all()
    if 'username' not in login_session:
        return render_template('publicCategory.html', login_session=login_session, categories=categories)
    else:
        return render_template('privateCategory.html', login_session=login_session, categories=categories)


# Adds a New Category
@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
            return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            newItem = Category(name=request.form['name'], user_id=login_session['user_id'])
            db.session.add(newItem)
            db.session.commit()
            flash("new category successfully created")
            return redirect(url_for('allCategories'))
    else:
        return render_template('newCategory.html')


# Edits a Category
# Input: category_id
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editItem = db.session.query(Category).filter_by(id=category_id).one()
    username = getUserInfo(editItem.user_id)
    username = getUserInfo(editItem.user_id)

    if username != login_session['username']:
        flash("You are not authorized to delete this category as you don't own it")
        return redirect(url_for('allCategories'))

    if request.method == 'POST':
        editItem.name = request.form['name']
        db.session.commit()
        flash("category %s successfully edited" % editItem.name)
        return redirect(url_for('allCategories'))
    else:
        return render_template('editCategory.html', category_id=category_id)


# Delete a Category
# Input: category_id
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = db.session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        db.session.delete(deleteItem)
        db.session.commit()
        flash("category %s successfully deleted" % deleteItem.name)
        return redirect(url_for('allCategories'))
    else:
        return render_template('deleteCategory.html', item=deleteItem)


# Menu of a Specific Category
# Input: category_id
@app.route('/category/<int:category_id>/')
def showCategoryMenu(category_id):
    category = db.session.query(Category).filter_by(id=category_id).one()
    items = db.session.query(Item).filter_by(category_id=category.id)
    return render_template('showCategoryMenu.html', category=category, items=items)


# New Item in a Specific Category
# Input: category_id
@app.route('/category/<int:category_id>/menu/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], category_id=category_id)
        db.session.add(newItem)
        db.session.commit()
        flash("new item successfully added")
        return redirect(url_for('showCategoryMenu', category_id=category_id))
    else:
        return render_template('newItem.html', category_id=category_id)


# Edit a Item in a Specific Category
# Input: category_id, item_id
@app.route('/category/<int:category_id>/menu/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == "POST":
        editItem = db.session.query(Item).filter_by(id=item_id).one()
        editItem.name = request.form['name']
        db.session.commit()
        flash("menu item successfully edited")
        return redirect(url_for('showCategoryMenu', category_id=category_id))
    else:
        return render_template('editItem.html', category_id=category_id, item_id=item_id)


# Delete a Item in a Specific Category
# Input: category_id, item_id
@app.route('/category/<int:category_id>/menu/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = db.session.query(Item).filter_by(id=item_id).one()
    if request.method == "POST":
        db.session.delete(deleteItem)
        db.session.commit()
        flash("menu item successfully deleted")
        return redirect(url_for('showCategoryMenu', category_id=category_id))
    else:
        return render_template('deleteItem.html', item=deleteItem)

# Return a JSON object of the Menu in a Specific Category
# Input: category_id
@app.route('/category/<int:category_id>/menu/json/')
def categoryMenuJson(category_id):
    category = db.session.query(Category).filter_by(id=category_id).one()
    items = db.session.query(Item).filter_by(category_id=category.id)
    return jsonify(Items=[i.serialize for i in items])



if __name__ == '__main__':
    app.secret_key = "tatta"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
