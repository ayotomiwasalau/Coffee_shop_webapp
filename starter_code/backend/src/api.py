import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
#db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    '''
    GET /drinks
        it retrievves the list of drink and their shortened attributes
        it contains only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    try:
        data = Drink.query.all()
        
        if not data:
            abort(404)
        drinks = [drink.short() for drink in data]
        return jsonify({
                    'success': True,
                    'drinks': drinks
                }), 200
    except exc.SQLAlchemyError:
        abort(503)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details():
    '''
    GET /drinks-detail
        it retrieve list of drink and their detailed attributes
        it requires the 'get:drinks-detail' permission
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    try:
        all_drinks = Drink.query.all()
        #drinks = list(map(Drink.long, all_drinks))
        drinks = [drink.long() for drink in all_drinks]
           
        return jsonify({
            "success": True, 
            "drinks": drinks
        }), 200

    except Exception:
        abort(404)



@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks():
    '''
    POST /drinks
        it creates a new row in the drinks table
        it requires the 'post:drinks' permission
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
    '''
    new_drink_info = json.loads(request.data)
    if not new_drink_info:
        abort(422)

    try:
             
        title = new_drink_info['title']
        recipe = json.dumps(new_drink_info['recipe'])

        Drink(title=title, recipe=recipe).insert()
        drinks = list(map(Drink.long, Drink.query.all()))


        return jsonify({
            "success": True, 
            "drinks": drinks
        }), 200
    except Exception:
        abort(404)



@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(id):
    '''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it updates the corresponding row for drink's <id>
        it responds with a 404 error if <id> is
        it requires the 'patch:drinks' permission
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
    '''    
    update = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    
    if not drink:
        abort(404)

    try:
        update_title = update.get('title')
        update_recipe = update.get('recipe')
        if update_title:
            drink.title = update_title

        if update_recipe:
            drink.recipe = json.dumps(update['recipe'])

        drink.update()

        return jsonify({
                'success': True, 
                'drinks': [drink.long()]
                }), 200

    except BaseException:
        abort(400)

# def update_drinks(id):
#     try:
#         drink_info = json.loads(request.data)

#         select_drink = Drink.query.filter(Drink.id == id).one_or_none()

#         print(select_drink)

#         #print(drink_info)

#         if not select_drink:
#             abort(404)

#         #print()
#         if drink_info['title']:
#             title = drink_info['title']
#             select_drink.title = title

#         elif drink_info['recipe']:
#             receipe = drink_info['recipe']
#             select_drink.receipe = json.dumps(receipe)

#         select_drink.update()

#         #drink = drink.long()
#         drinks = list(map(drink.long(), drink))     

#         return jsonify({
#             "success": True, 
#             "drinks": drinks
#         }), 200
#     except exc.SQLAlchemyError:
#         abort(422)        
#     except Exception:
#         abort(404)

@app.route('/drinks/<id>', methods = ['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(id):
    '''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it deletes the corresponding row for the drink's <id>
    '''
    try:

        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if not drink:
            abort(404)
        else:
            drink.delete()
           
    # returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record or appropriate status code indicating reason for failure
        return jsonify({
            "success": True, 
            "delete": id
        }),200
    # respond with a 404 error if <id> is not found
    except Exception:
        abort(404)


'''
Error Handling
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404    



@app.errorhandler(401)
def unauthorized(error):
    
    return jsonify({
                    "success": False, 
                    "error": 401,
                    "message": "Unauthorized"
                    }), 401 

@app.errorhandler(400)
def bad_request(error):
    
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "Bad Request"
                    }), 400



@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code