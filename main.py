#imports
import json
from flask import Flask, jsonify, request, make_response
from firebase_admin import credentials, firestore, initialize_app
import smtplib
from email.message import EmailMessage
import threading
import datetime

app = Flask(__name__)
# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()

@app.route('/')
def home():
    return "Welcome to the API designed by Miriam Duke"

@app.route('/user', methods=['POST'])
def register_user():
    #get the data from the request made
    request_data = request.get_json() 
    # ensure at least the student id, first & last name, email, year group, residence status and major were provided
    if all(key in request_data for key in ('student_id','password','year_group', 'full_name', 'best_food', 'best_movie','email', 'major', 'residence_status','dob')) and request.method == 'POST':
        #create a new user from the data gotten 
        new_user = {
        'student_id': request_data['student_id'],
        'full_name': request_data['full_name'],
        'best_food': request_data['best_food'],
        'best_movie': request_data['best_movie'],
        'email': request_data['email'],
        'major': request_data['major'],
        'spirit_animal': request_data['spirit_animal'],
        'password': request_data['password'],
        'dob': request_data['dob'],
        'year_group': request_data['year_group'],
        'residence_status': request_data['residence_status']
        }
    
        # check if the user already exists
        is_existing_user = get_user_info(request_data['student_id'])
        if is_existing_user.status_code == 200:
            error_message = {
            'status' : 400,
            'message': 'User is already registered'
            }
            response = jsonify(error_message)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.status_code = 400 #its a bad request
            return response

        # save new user information into firestore
        doc_ref = db.collection(u'users').document(request_data['student_id'])
        doc_ref.set(new_user)

        response = jsonify(new_user)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 201 #new resource created
        return response
    error_message = {
    'status' : 400,
    'message': 'You MUST provide essential fields when creating a new user.'
    }
    response = jsonify(error_message)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 400 #its a bad request
    return response


@app.route('/user/<string:student_id>',methods=['GET'])
def get_user_info(student_id):
    #check file for users
    users_ref = db.collection(u'users')
    users = users_ref.stream()
    for user in users:
        if user.id == student_id:
            response = jsonify(user.to_dict())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.status_code = 200 #successful
            return response
    error_message = {
    'status' : 404,
    'message': 'User  does NOT EXIST'
    }
    response = jsonify(error_message)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 404 #Resource not found
    return response

@app.route('/user/<string:student_id>', methods=['PUT'])
def update_user(student_id):
    #first check if user exists
    is_existing_user= get_user_info(student_id)
    if is_existing_user.status_code == 404:
        error_message = {
        'status' : 404,
        'message': 'user does NOT exist. CANNOT UPDATE!'
        }
        response = jsonify(error_message)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 404 #resource does not exist
        return response
    
    valid_attributes = ['major', 'year_group', 'residence_status', 'dob', 'best_food', 'best_movie']
    request_data = request.get_json()
    invalid_attributes = [key for key in request_data.keys() if key not in valid_attributes]
    if invalid_attributes:
        error_message = {
            'status' : 422,
            'message': "There are invalid attributes in your update request"
        }
        response = jsonify(error_message)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 422  # Unprocessable Entity
        return response

    users_ref = db.collection('users')
    users_ref.document(student_id).update(request.json)
    response = make_response('')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 204  # No content
    return response

 
@app.route('/post', methods=['GET'])
def get_all_posts():
    posts_ref = db.collection(u'posts')
    posts = posts_ref.stream()
    posts_list = []
    for post in posts:
        posts_list.append(post.to_dict())
    if len(posts_list) == 0:
        response = make_response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 204  # No content
        return response
    
    response = jsonify(posts_list)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 200 #successful
    return response

@app.route('/tip', methods=['GET'])
def get_all_tips():
    tips_ref = db.collection(u'tips')
    tips = tips_ref.stream()
    tips_list = []
    for tip in tips:
        tips_list.append(tip.to_dict())
    if len(tips_list) == 0:
        response = make_response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 204  # No content
        return response
    
    response = jsonify(tips_list)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 200 #successful
    return response

@app.route('/sos', methods=['POST'])
def register_sos():
    #get the data from the request made
    request_data = request.get_json() 

    # ensure at least the student id was provided
    if 'student_id' in request_data and request.method == 'POST':
        
         #first check if user exists
        is_existing_user= get_user_info(request_data['student_id'])
        if is_existing_user.status_code == 404:
            error_message = {
            'status' : 404,
            'message': 'user does NOT exist. CANNOT REGISTER SOS!'
            }
            response = jsonify(error_message)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.status_code = 404 #resource does not exist
            return response
        
        #create a new sos from the data gotten 
        new_sos = {
        'student_id': request_data['student_id']
        }

        # save new user information into firestore
        doc_ref = db.collection(u'sos').document(request_data['student_id'])
        doc_ref.set(new_sos)

        response = jsonify(new_sos)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 201 #new resource created
        return response
    
    error_message = {
    'status' : 400,
    'message': 'You MUST provide essential fields when creating a new sos.'
    }
    response = jsonify(error_message)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 400 #its a bad request
    return response

@app.route('/post', methods=['POST'])
def make_post():
    # get the data from the request made
    request_data = request.get_json() 

    # first check if user exists
    is_existing_user = get_user_info(request_data['student_id'])
    if is_existing_user.status_code == 404:
        error_message = {
            'status': 404,
            'message': 'user does NOT exist. CANNOT POST'
        }
        response = jsonify(error_message)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 404 # resource does not exist
        return response
    
    # ensure at least the student id was provided
    if all(key in request_data for key in ('student_id', 'full_name', 'comment', 'email')) and request.method == 'POST':
        # create a new post from the data gotten 
        new_post = {
            'student_id': request_data['student_id'],
            'full_name': request_data['full_name'],
            'comment': request_data['comment'],
            'likes': 0,
            'posted_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        # save new post information into firestore
        doc_ref = db.collection(u'post').document()
        doc_ref.set(new_post)

        # Start a new thread to send the email
        t = threading.Thread(target=send_new_post_alerts, args=(request_data['full_name'],))
        t.start() # send email to each user alerting them of the post

        response = jsonify(new_post)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.status_code = 201 # new resource created
        return response
    
    error_message = {
        'status' : 400,
        'message': 'You MUST provide essential fields when creating a new post.'
    }
    response = jsonify(error_message)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 400 # it's a bad request
    return response


def send_new_post_alerts(full_name):
    users_ref = db.collection(u'users')
    users = users_ref.stream()
    for user in users:
        user_data = user.to_dict()
        email = user_data['email']
        new_post_alert(email, full_name)

def new_post_alert(receiver_address,full_name):
    sender_address = 'i.am.seen.are.you@gmail.com'
    password = 'jsqfwtijcenwdvsi'

    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
    #next step is to login into server
        smtp.login(sender_address,password)
    
        subject = 'Seen - New Post Alert'
        body = full_name + ' just made a new post, check it out!!\n\n---------- I am seen are you? ----------\n\nWith love,\nSeen xx'
    
        msg = f'Subject: {subject}\n\n\n{body}'
    
        smtp.sendmail(sender_address,receiver_address,msg) #SENDER,RECEIVER,msg

@app.route('/post/<string:post_id>', methods=['PUT'])
def like_post(post_id):
    posts_ref = db.collection('post')
    posts_ref.document(post_id).update({'likes': firestore.Increment(1)})
    response = make_response('')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 204  # No content
    return response

@app.errorhandler(404)
def error_handler(error):
    message = {
        'status': 404,
        'message': 'Resource not found: ' + request.url,
    }
    response = jsonify(message)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.status_code = 404
    return response

if __name__ == '__main__':    
    app.run()

