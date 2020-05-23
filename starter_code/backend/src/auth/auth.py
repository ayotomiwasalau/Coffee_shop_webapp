from os import environ
import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import ctypes
import sys


AUTH0_DOMAIN = 'coffeeshopauth.auth0.com'
ALGORITHMS = 'RS256'
API_AUDIENCE = 'coffee_shop_auth_api'

# AUTH0_DOMAIN = environ.get('AUTH0_DOMAIN', 'coffeeshopauth.auth0.com')
# ALGORITHMS = ['RS256']
# API_AUDIENCE = environ.get('API_AUDIENCE', 'coffee_shop_auth_api')


'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

def get_token_auth_header():
    '''
    Obtain the access token from the authorization header
    '''
    #attempt to get the header from the request
    auth = request.headers.get('Authorization', None)

    #raise an AuthError if no header is present
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
                }, 401)

    #attempt to split bearer and the token
    parts = auth.split()

    #raise an AuthError if the header is malformed return the token part of the header
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'            
    }, 401)

    elif len(parts)>2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
    }, 401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    '''
    Function for authenticating permission of the user
    input:
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    returns:
        Boolean (True)
    '''

    #raises an AuthError if permissions are not included in the payload
    if 'permissions' not in payload:
        
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT'
        }, 400)

    #raise an AuthError if the requested permission string is not in the payload permissions array return true otherwise    
    if permission not in payload['permissions']:
        
        raise AuthError({
            'code': 'forbidden',
            'description': 'Permission not found'
        }, 401)

    return True


def get_rsa_key(token):
    '''Checks jwks for an rsa key using a key ID in the token header.
    input:
        token (str):  The token string
    Returns:
        dict: The rsa key.
    '''
    
    try:

        jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')

        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        if 'kid' not in unverified_header:
            raise AuthError({
                'code': 'invalid_header',
                'description': '"kid" missing from token header.'
            }, 401)

        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
        if not rsa_key:
            raise AuthError({
                'code': 'invalid_key',
                'description': 'Unable to find the appropriate key.'
            }, 401)
        return rsa_key
    except Exception:
        raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to verify token header.'
            }, 401)


def verify_decode_jwt(token):
    '''Verifies and decodes the JWT token.
    input:
        token (str):  The token string
    Returns:
        dict: The token payload.
    '''
    rsa_key = get_rsa_key(token)
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError({
            'code': 'token_expired',
            'description': 'Token expired.'
        }, 401)
    except jwt.JWTClaimsError:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Incorrect claims. \
                            Please check the audience and issuer.'
        }, 401)
    except Exception:
        raise AuthError({
            'code': 'invalid_token',
            'description': 'Unable to decode token.'
        }, 400)


#----------------------------------------------
# def verify_decode_jwt(token):
#     # Get public key from Auth0
#     jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
#     jwks = json.loads(jsonurl.read())

#     # Get the data in the header
#     unverified_header = jwt.get_unverified_header(token)

#     # Auth0 token should have a key id
#     if 'kid' not in unverified_header:
#         raise AuthError({
#             'code': 'invalid_header',
#             'description': 'Authorization malformed'
#         }, 401)

#     rsa_key = {}

#     for key in jwks['keys']:
#         if key['kid'] == unverified_header['kid']:
#             rsa_key = {
#                 'kty': key['kty'],
#                 'kid': key['kid'],
#                 'use': key['use'],
#                 'n': key['n'],
#                 'e': key['e']
#             }
#             break
#         print(rsa_key, file=sys.stderr)    
#     # verify the token
#     if rsa_key:
#         try:
#             # Validate the token using the rsa_key

#             print(token, file=sys.stderr)

#             payload = jwt.decode(
#                 token,
#                 rsa_key,
#                 algorithms=ALGORITHMS,
#                 audience=API_AUDIENCE,
#                 issuer='https://' + AUTH0_DOMAIN + '/'
#             )

#             print(payload, file=sys.stderr)
#             return payload

#         except jwt.ExpiredSignatureError:

#             raise AuthError({
#                 'code': 'token_expired',
#                 'description': 'Token expired.'
#             }, 401)

#         except jwt.JWTClaimsError:

#             raise AuthError({
#                 'code': 'invalid_claims',
#                 'description': 'Incorrect claims. Please, '
#                 'check the audience and issuer.'
#             }, 401)

#         except Exception:
#             print(Exception)
#             raise AuthError({
#                 'code': 'invalid_header',
#                 'description': 'Unable to parse authentication token.'
#             }, 401)

#     raise AuthError({
#         'code': 'invalid_header',
#         'description': 'Unable to find the appropriate key.'
#     }, 400)

#----------------------------------------------------------

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)


            check_permissions(permission, payload)
            return f(*args, **kwargs)

        return wrapper
    return requires_auth_decorator