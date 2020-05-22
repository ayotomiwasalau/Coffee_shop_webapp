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
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
#db_drop_and_create_all()

## ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks')
def get_drinks():
    all_drinks = Drink.query.all()
    drinks = list(map(Drink.short, all_drinks))

    return jsonify({
        "success": True, 
        "drinks": drinks
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details():
    try:
        all_drinks = Drink.query.all()
        #drinks = list(map(Drink.long, all_drinks))
        drinks = [drink.long() for drink in all_drinks]
           
        return jsonify({
            "success": True, 
            "drinks": drinks
        }), 200

    except:
        abort(404)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods = ['POST'])
@requires_auth('post:drinks')
def post_drinks():
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
    except exc.SQLAlchemyError:
        abort(422)
    except Exception:
        abort(404)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(id):
    try:
        drink_info = json.loads(request.data)

        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if not drink:
            abort(404)

        title = drink_info.get('title')
        receipe = drink_info.get('recipe')

        if title:
            drink.title = title

        if receipe:
            drink.receipe = receipe

        drink.update()
        #drink = drink.long()
        drinks = list(map(drink.long(), drink))     

        return jsonify({
            "success": True, 
            "drinks": drinks
        }), 200
    except exc.SQLAlchemyError:
        abort(422)        
    except Exception:
        abort(404)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods = ['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(id):
    try:

        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if not drink:
            abort(404)
        else:
            drink.delete()
            

        return jsonify({
            "success": True, 
            "delete": id
        }),200
    except:
        abort(404)

## Error Handling
'''
Example error handling for unprocessable entity
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