# itemize

Itemize provides a web interface along with JSON endpoints that allow you to group items into categories. Users can edit or delete items they've creating. Adding items, deleteing items and editing items requiring logging in with their Google account.

## Instructions

### Cloning the setting up the repository

1. Clone with HTTPS: `git clone https://github.com/alisaleemh/itemize.git`
2. cd into `itemize`

### Setting up the database
1. In the root directory, run `python dbSetup.py` to set a sqlite database with the defined schema
2. In the root directory, run `python loadDb.py` to load test data

### Running the application
1. Run `python app.py`


### Open in a webpage
1. Now you can open in a webpage by going to either:
    http://0.0.0.0:5000
    http://localhost:5000
