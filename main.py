import pandas as pd
from datetime  import datetime as dt,timedelta                                    # Not important
import mysql.connector
from flask import Flask, request,jsonify,make_response,render_template,Response
from faker import Faker
from functools import wraps
import random
import pyfloat
import jwt
import bcrypt
import time
import datetime
import logging




app = Flask(__name__)


# Create a MySQL connection
mydb = mysql.connector.connect(
    host='db-mysql-blr1-96314-do-user-14717504-0.c.db.ondigitalocean.com',
    port=25060,
    user='doadmin',
    password="AVNS_rXzTVM_hFFdqiggEMqX",
    database='fitness',
    )




logging.getLogger("openblas").setLevel(logging.WARNING)




app.config['SECRET_KEY']='AbdullahFawazMahmoud'
my_cursor = mydb.cursor()
fake=Faker()




@app.route('/get_records/<table_name>')
def get_records(table_name):
    try:
        

        # Create the SELECT query
        query = f"SELECT * FROM {table_name}"

        # Execute the query
        my_cursor.execute(query)

        # Fetch all rows
        rows = my_cursor.fetchall()

        # Get column names
        column_names = [desc[0] for desc in my_cursor.description]

        # Prepare the result as a list of dictionaries
        records = []
        for row in rows:
            record = {}
            for i in range(len(column_names)):
                record[column_names[i]] = row[i]
            records.append(record)



        if records:
            return jsonify(records)
        else:
            return 'No records found'
    except mysql.connector.Error as error:
        print(f"Failed to get records from table {table_name}: {error}")
        return 'Failed to get records'




@app.route('/search', methods=['GET'])
def search_exercises():
    # Get the query parameters from the URL
    field_value_pairs = request.args

    # Create a cursor to interact with the database

    # Build the search query dynamically based on the provided field-value pairs
    query = "SELECT * FROM exercise WHERE "
    params = []
    conditions = []
    for field, value in field_value_pairs.items():
        conditions.append(f"{field} = %s")
        params.append(value)
    query += " AND ".join(conditions)

    my_cursor.execute(query, params)
    results = my_cursor.fetchall()

    if not results:
        return jsonify({'message': 'No matching exercises found.'}), 404

    exercises = []
    for exercise in results:
        exercise_data = {
            'id': exercise[0],
            'title': exercise[1],
            'descr': exercise[2],
            'type': exercise[3],
            'bodypart': exercise[4],
            'equipment': exercise[5],
            'level': exercise[6],
            'rating': exercise[7],
            'ratingdesc': exercise[8]
        }
        exercises.append(exercise_data)

    return jsonify(exercises)

    
@app.route('/')
def printExersiceTable():
    name = request.args['name']
    now = dt.now()
    now1 = now.strftime("%m/%d/%Y, %H:%M:%S")
    return HELLO_HTML.format(name, now1)


HELLO_HTML = """
    <html><body>
        <h1>Hello, {0}!</h1>
        The time is {1}.
    </body></html>"""


@app.route('/getUnique')
def getUnique():
    unique_column = request.args.get('column', default=None)
    sql = ['use fitness', f'SELECT DISTINCT {unique_column} from exercise']
    for i in sql:
        my_cursor.execute(i)

    cursor_data = my_cursor.fetchall()
    data_frame = pd.DataFrame(cursor_data)
    data_frame.rename(columns={0: f'{unique_column}'}, inplace=True)
    result = data_frame.to_html(header="true", table_id="table")
    return result




@app.route('/insert_users')
def insert_users():
      
     characters = "01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ&*(){}[]|/\?!@#$%^abcdefghijklmnopqrstuvwxyz"
     fake = Faker('en_US')
     gender = ["M", "F"]
     profile = fake.simple_profile(sex=gender[random.randint(0, 1)])
     name = profile['name']
     sex = profile['sex']
     username = profile['username']
     password = "".join(random.sample(characters, random.randint(8, 20)))
     email = profile['mail']
     birthdate = fake.date_of_birth(minimum_age=17, maximum_age=60)
    
    # Calculate the age based on the current date
     age = (dt.now().date() - birthdate).days // 365
     weight = random.randint(50, 120)
     height = random.uniform(1.5, 1.9)
     bmi = weight / (height * height)

    # Define the SQL query to insert the object data into a table
     values = ( name, age, weight, height, bmi, sex, username, password, email)
     sql = "INSERT into user ( name, age, weight, height, bmi, sex, username, password, email) " \
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
     try:
        # Execute the SQL query
        my_cursor.execute(sql, values)
        # Commit the changes to the database
        mydb.commit()
        return "User data inserted successfully."
     except Exception as e:
        # Rollback the changes if an error occurs
        mydb.rollback()
        return "Error inserting user data: " + str(e)



@app.route('/login', methods=['POST'])
def login():
    # Get user data from request
    email = request.json['email']
    password = request.json['password']

    # Create a cursor to interact with the database

    # Check if the user exists and the password is correct
    my_cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
    user = my_cursor.fetchone()

    if not user:
        # User does not exist or password is incorrect
        return jsonify({'message': 'Invalid email or password'})

    existing_token = None
    # Check if the user already has a token
    if 'token' in user:
        existing_token = user[1]  # Assuming the token is stored in the 'token' field of the user dictionary

    if existing_token is not None:
        existing_token = existing_token.encode('utf-8')  # Encode the token as bytes
        try:
            # Verify the existing token
            existing_payload = jwt.decode(existing_token, 'AbdullahFawazMahmoud')

            # Extend the expiration time by 30 minutes
            existing_payload['exp'] = dt.utcnow() + datetime.timedelta(hours=24)

            # Encode the updated payload with the secret key
            token = jwt.encode(existing_payload, 'AbdullahFawazMahmoud')
        except jwt.ExpiredSignatureError:
            # Existing token has expired, generate a new token as usual
            token_payload = {
                'user_id': user[0],  # Assuming the user id is stored in the 'user_id' field of the user dictionary
                'exp': dt.utcnow() + datetime.timedelta(hours=24)
            }
            token = jwt.encode(token_payload, 'AbdullahFawazMahmoud')
    else:
        # Generate a new token as usual
        token_payload = {
            'user_id': user[0],  # Assuming the user id is stored in the 'user_id' field of the user dictionary
            'exp': dt.utcnow() + datetime.timedelta(minutes=30)
        }
        token = jwt.encode(token_payload, 'AbdullahFawazMahmoud')

    # Update the token in the user table
    my_cursor.execute("UPDATE user SET token = %s WHERE user_id = %s", (token, user[0]))  # Assuming the user id is stored in the 'user_id' field of the user dictionary
    mydb.commit()

    return jsonify({'token': token})

       


@app.route('/register', methods=['POST'])
def register():
    # Get user email and password from the request body
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if email already exists
    sql = "SELECT * FROM user WHERE email = %s"
    value = (email,)
    my_cursor.execute(sql, value)
    user = my_cursor.fetchone()
    if user:
        return jsonify({'message': 'Email already registered.'}), 409

    # Insert user into the database
    sql = "INSERT INTO user (email, password) VALUES (%s, %s)"
    values = (email, password)
    my_cursor.execute(sql, values)
    mydb.commit()

    return jsonify({'message': 'User registered successfully.'}), 201



@app.route('/user_info', methods=['POST'])
def create_user():
    try:
        # Get user data from the request body
        data = request.json
        email= data.get("email")
        sex = data.get('sex')
        date_of_birth = data.get('date_of_birth')
        weight = float(data.get('weight'))
        height = float(data.get('height'))

        # Check if height and weight are within the specified ranges
        if not (1.4 <= height <= 2.1):
            return jsonify({'error': 'Invalid height. Height should be between 1.4 and 2.1 meters.'}), 400

        if not (40 <= weight <= 180):
            return jsonify({'error': 'Invalid weight. Weight should be between 40 and 180 kilograms.'}), 400

        # Check if the sex field is valid
        if sex not in ('F', 'M'):
            return jsonify({'error': 'Invalid sex. Sex should be either "F" for female or "M" for male.'}), 400

        # Calculate age based on the provided date of birth
        dob = dt.strptime(date_of_birth, '%Y-%m-%d')
        today = dt.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # Calculate BMI
        bmi = weight / (height ** 2)

        # Insert user into the database
        sql_update = "UPDATE user SET sex = %s, age = %s, weight = %s, height = %s, bmi = %s WHERE email = %s"
        values = (sex, age, weight, height,bmi, email)
        my_cursor.execute(sql_update, values)
        mydb.commit()

        return jsonify({'message': 'User informations inserted successfully.'}), 201

    except mysql.connector.Error as error:
        return jsonify({'error': 'Database error: ' + str(error)}), 500

    except Exception as e:
        return jsonify({'error': 'An error occurred: ' + str(e)}), 500




@app.route('/reset_password', methods=['POST'])
def reset_password():
    # Get the user's ID, token, and new password from the request body
    data = request.json
    user_id = data.get('user_id')
    token = data.get('token')
    new_password = data.get('new_password')

    # Check if the user exists in the database
    my_cursor.execute("SELECT * FROM user WHERE user_id = %(user_id)s", {'user_id': user_id})
    user = my_cursor.fetchone()
    if user:
        # Check if the provided token matches the user's token in the database
        stored_token = user[1]  # Assuming the token field is at index 1
        if token == stored_token:
            # Update the user's password
            my_cursor.execute("UPDATE user SET password = %(new_password)s WHERE user_id = %(user_id)s", {'new_password': new_password, 'user_id': user_id})
            mydb.commit()
            return jsonify({'message': 'Password reset successful.'}), 200
        else:
            return jsonify({'message': 'Please check your email or password.'}), 401
    else:
        return jsonify({'message': 'User not found.'}), 404






def verify_token(token):
    # Check if the token exists in the user table
    sql = "SELECT user_id FROM user WHERE token = %s"
    my_cursor.execute(sql, (token,))
    result = my_cursor.fetchone()

    if result:
        return result[0]  # Return the user ID associated with the token
    else:
        return None





@app.route('/plan/exercises', methods=['POST'])
def add_exercises_to_plan():
    # Retrieve the token from the request's Authorization header
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'error': 'No token provided'}), 401

    try:
        # Remove the "Bearer" prefix from the token if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        # Verify and decode the token
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])
        # Extract user ID from the decoded token
        user_id = decoded_token['user_id']

        # Retrieve the exercise data, plan ID, level, and plan name from the request body
        request_data = request.get_json()

        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400

        exercise_data = request_data.get('exercises')
        plan_id = request_data.get('plan_id')
        level = request_data.get('level')
        plan_name = request_data.get('plan_name')

        if not exercise_data:
            return jsonify({'error': 'No exercise data provided'}), 400

        # Validate the level field
        valid_levels = ["Beginner", "Intermediate", "Advanced"]
        if level not in valid_levels:
            return jsonify({'error': 'Invalid level'}), 400

        if not plan_id:
            # If no plan ID provided, generate a new plan ID by inserting a new row into the plan table
            insert_plan_query = "INSERT INTO plan (user_user_id1, level, plan_name) VALUES (%s, %s, %s)"
            my_cursor.execute(insert_plan_query, (user_id, level, plan_name))
            mydb.commit()

            # Retrieve the auto-incremented plan ID generated by the database
            plan_id = my_cursor.lastrowid

        # Check if the provided plan ID belongs to the user
        check_query = "SELECT COUNT(*) FROM plan WHERE plan_id = %s AND user_user_id1 = %s"
        my_cursor.execute(check_query, (plan_id, user_id))
        count = my_cursor.fetchone()[0]

        if count == 0:
            return jsonify({'error': 'Invalid plan ID'}), 400

        # Update the level and plan name for the existing plan
        update_query = "UPDATE plan SET level = %s, plan_name = %s WHERE plan_id = %s"
        my_cursor.execute(update_query, (level, plan_name, plan_id))
        mydb.commit()

        # Insert the exercises into the planexerciseid table
        insert_query = "INSERT INTO planexerciseid (plan_plan_id, exercise_id) VALUES (%s, %s)"
        for exercise_id in exercise_data:
            my_cursor.execute(insert_query, (plan_id, exercise_id))
        mydb.commit()

        return jsonify({'message': 'Exercises added to the plan successfully', 'plan_id': plan_id}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Please login again to confirm your identity'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500


@app.route('/allWorkouts', methods=['GET'])
def get_user_allworkouts():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({'message': 'No token provided'}), 401

    auth_parts = auth_header.split('Bearer ')

    if len(auth_parts) != 2:
        return jsonify({'message': 'Invalid token format'}), 401

    token = auth_parts[1]

    try:
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])
        user_id = decoded_token['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

    sql_user = "SELECT name FROM user WHERE user_id = %s"
    my_cursor.execute(sql_user, (user_id,))
    user = my_cursor.fetchone()

    if not user:
        return jsonify({'message': 'User not found'})

    name = user[0]

    sql_plans = """
        SELECT p.plan_id, p.level, p.plan_name
        FROM plan p
        WHERE p.user_user_id1 = %s
    """
    my_cursor.execute(sql_plans, (user_id,))
    plans = my_cursor.fetchall()

    if not plans:
        response = {
            'name': name,
            'plans': []
        }
        return jsonify(response)

    plan_jsons = []
    for plan in plans:
        plan_json = {
            'plan_id': plan[0],
            'level': plan[1],
            'plan_name': plan[2]
        }
        plan_jsons.append(plan_json)

    response = {
        'name': name,
        'plans': plan_jsons
    }

    return jsonify(response)




@app.route('/workouts/<string:goal>', methods=['GET'])
def get_trainee_workouts(goal):
    # Get the token from the request headers or query parameters, whichever you're using
    auth_header = request.headers.get('Authorization')  # Assuming the token is passed in the Authorization header

    # Check if the Authorization header is present
    if not auth_header:
        return jsonify({'error': 'No token provided'}), 401

    # Split the auth header to extract the token value
    auth_parts = auth_header.split('Bearer ')

    # Check if the Authorization header has the correct format
    if len(auth_parts) != 2:
        return jsonify({'error': 'Invalid token format'}), 401

    token = auth_parts[1]

    # Extract the user ID from the token
    try:
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])
        user_id_from_token = decoded_token['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Please login again to confirm your identity'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500

    # Define the valid workout goals
    valid_goals = ["Gain muscles", "Improve fitness", "Loose weight"]

    # Check if the provided workout goal is valid
    if goal not in valid_goals:
        return jsonify({'error': 'Invalid workout goal'}), 400

    # Retrieve plan IDs and levels for the user based on the user ID and the specified workout goal
    sql = """
            SELECT plan_id, level
            FROM plan
            WHERE user_user_id1 = %s AND goal = %s
         """
    my_cursor.execute(sql, (user_id_from_token, goal))
    plan_data = my_cursor.fetchall()

    # Check if any plan data is found
    if not plan_data:
        return jsonify({'error': 'No plans found for the user with the specified goal.'}), 404

    results = []
    for plan in plan_data:
        plan_id = plan[0]
        level = plan[1]
        results.append({'plan_id': plan_id, 'level': level})

    return jsonify(results), 200




@app.route('/workout/<int:plan_id>', methods=['GET'])
def get_trainee_workout(plan_id):
    # Get the token from the request headers or query parameters, whichever you're using
    auth_header = request.headers.get('Authorization')  # Assuming the token is passed in the Authorization header

    # Check if the Authorization header is present
    if not auth_header:
        return jsonify({'error': 'No token provided'}), 401

    # Split the auth header to extract the token value
    auth_parts = auth_header.split('Bearer ')

    # Check if the Authorization header has the correct format
    if len(auth_parts) != 2:
        return jsonify({'error': 'Invalid token format'}), 401

    token = auth_parts[1]

    try:
        # Verify and decode the token
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])

        # Extract user ID from the token payload
        user_id_from_token = decoded_token['user_id']

        # Retrieve workouts for the trainee based on user ID from the token and plan ID from the route
        sql = """
                SELECT exercise.id, exercise.level, exercise.title
                FROM user 
                JOIN plan ON user.user_id = plan.user_user_id1
                JOIN planexerciseid ON plan.plan_id = planexerciseid.plan_plan_id
                JOIN exercise ON planexerciseid.exercise_id = exercise.id
                WHERE user.user_id = %s AND plan.plan_id = %s
             """
        my_cursor.execute(sql, (user_id_from_token, plan_id))
        workouts = my_cursor.fetchall()

        # Check if any workouts are found
        if not workouts:
            return jsonify({'error': 'No workouts found for the trainee.'}), 404

        # Format the response
        results = []
        for workout in workouts:
            workout_id = workout[0]
            level = workout[1]
            title = workout[2]
            workout_data = {'id': workout_id, 'level': level, 'title': title}
            results.append(workout_data)

        return jsonify(results), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Please login again to confirm your identity'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500


@app.route('/profile', methods=['GET'])
def get_user_profile():
    # Retrieve the token from the request's Authorization header
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'error': 'No token provided'}), 401

    try:
        # Remove the "Bearer" prefix from the token if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        # Verify and decode the token
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])
        # Extract user ID from the decoded token
        user_id = decoded_token['user_id']

        # Retrieve the user's name, height, weight, age, and goal from the user table
        select_query = "SELECT name, height, weight, age, goal FROM user WHERE user_id = %s"
        my_cursor.execute(select_query, (user_id,))
        result = my_cursor.fetchone()

        if not result:
            return jsonify({'error': 'User not found'}), 404

        # Extract the values from the database result
        name, height, weight, age, goal = result

        # Return the user profile information
        return jsonify({
            'name': name,
            'height': height,
            'weight': weight,
            'age': age,
            'goal':goal
            
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Please login again to confirm your identity'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500




@app.route('/deletePlan/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    # Get the token from the request headers or query parameters
    auth_header = request.headers.get('Authorization')  # Assuming the token is passed in the Authorization header

    if not auth_header:
        return jsonify({'message': 'No token provided'}), 401

    # Split the auth header to extract the token value
    auth_parts = auth_header.split('Bearer ')

    # Check if the Authorization header has the correct format
    if len(auth_parts) != 2:
        return jsonify({'message': 'Invalid token format'}), 401

    token = auth_parts[1]

    try:
        # Decode and verify the token
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])
        user_id = decoded_token['user_id']  # Assuming the user ID is stored in the 'user_id' claim
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

    # Check if the plan exists and belongs to the user
    sql_check_plan = "SELECT * FROM plan WHERE plan_id = %s AND user_user_id1 = %s"
    my_cursor.execute(sql_check_plan, (plan_id, user_id))
    plan = my_cursor.fetchone()

    if not plan:
        return jsonify({'message': 'Plan not found or does not belong to the user'}), 404

    try:
        # Start a transaction
        

        # Delete the associated exercise from the planexerciseid table
        sql_delete_exercise = "DELETE FROM planexerciseid WHERE plan_plan_id = %s"
        my_cursor.execute(sql_delete_exercise, (plan_id,))

        # Delete the plan from the plan table
        sql_delete_plan = "DELETE FROM plan WHERE plan_id = %s"
        my_cursor.execute(sql_delete_plan, (plan_id,))

        # Commit the transaction
        mydb.commit()

        return jsonify({'message': 'Plan and associated exercise deleted successfully'}), 200
    except Exception as e:
        # Rollback the transaction on error
        mydb.rollback()
        return jsonify({'message': 'Error deleting the plan and associated exercise', 'error': str(e)}), 500
    


@app.route('/calculateWaterNeed/<int:weight>', methods=['GET'])
def calculate_water_need(weight):
    water_need = weight * 0.033  # Assuming the water need is 33 milliliters per kilogram of body weight

    return jsonify({'water_need': water_need}), 200


@app.route('/AiMaker', methods=['GET'])
def fakeAi():
    try:
        # Retrieve the token from the request's Authorization header
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Missing token'}), 401

        # Remove the "Bearer" prefix from the token if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        # Verify and decode the token
        decoded_token = jwt.decode(token, 'AbdullahFawazMahmoud', algorithms=['HS256'])
        # Extract user ID from the decoded token
        user_id = decoded_token['user_id']

        # Convert the user ID to an integer
        user_id = int(user_id)

        # Retrieve the list of exercise IDs
        listOfNames = ['Abdominals', 'Adductors', 'Biceps',
                       'Calves', 'Lats', 'Triceps', 'Glutes',
                       'Chest', 'Shoulders', 'Quadriceps']

        exercise_ids = []

        for name in listOfNames:
            query = f"SELECT id FROM exercise WHERE bodypart='{name}'"
            my_cursor.execute(query)
            result = my_cursor.fetchall()
            if result:
                exercise_ids.append(result[0])

        # Create a new plan for the user in the "plan" table
        query = "INSERT INTO plan (user_user_id1) VALUES (%s)"
        values = (user_id,)
        my_cursor.execute(query, values)
        mydb.commit()

        # Retrieve the auto-generated plan ID from the last insert
        plan_id = my_cursor.lastrowid

        # Insert the exercise IDs into the "planexerciseid" table
        query = "INSERT INTO planexerciseid (plan_plan_id, exercise_id) VALUES (%s, %s)"
        values = [(plan_id, exercise_id) for exercise_id in exercise_ids]
        my_cursor.executemany(query, values)
        mydb.commit()

        return "Plan created!"

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Please login again to confirm your identity'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)