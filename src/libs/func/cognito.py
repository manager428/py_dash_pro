from pycognito import Cognito
from src import application, login_manager
import jwt
from src.models.user import User
user_pool_id = application.config['COGNITO_USER_POOL_ID']
app_client_id = application.config['COGNITO_APP_CLIENT_ID']


@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


def do_cognito_login(username, password):
    user_without_email = username.split("@")[0]
    authenticate = Cognito(user_pool_id, app_client_id, username=user_without_email)
    try:
         u = authenticate.authenticate(password=password)
         jwtJSON = jwt.decode(authenticate.id_token, verify=False)
         var = jwtJSON['custom:watchuuid'] if "custom:watchuuid" in jwtJSON else ""
         return User(jwtJSON['cognito:username'], var, jwtJSON['cognito:groups'][0])
    except Exception as e:
         if type(e).__name__ ==    'NotAuthorizedException' :
            return "NotAuthorizedException"
         if type(e).__name__ == 'ForceChangePasswordException' :
            return "ForceChangePasswordException" 
         print('exception when authenticating ' + str(e))
         return None


def get_users():
    u = Cognito(user_pool_id, app_client_id)
    users = u.get_users(attr_map={"given_name": "first_name", "family_name": "last_name"})
    return users


def get_user_detail(username):
    user_without_email = username.split("@")[0]
    u = Cognito(user_pool_id, app_client_id)
    users = u.get_users()
    for x in users:
        if x._data['preferred_username'] == user_without_email:
            return x    


def get_user(username):
    user_without_email = username.split("@")[0]
    u = Cognito(user_pool_id, app_client_id)
    users = u.get_users(attr_map={"given_name": "first_name", "family_name": "last_name"})
    for x in users:
        if x._data.get('preferred_username') == user_without_email:
            var = x._data['custom:watchuuid'] if "custom:watchuuid" in x._data else ""
            return User(x._data['preferred_username'], x._data['preferred_username'], var)


def get_cognito_user(username):
    u = Cognito(user_pool_id, app_client_id, username=username)
    return  u.admin_get_user()  , u.admin_list_groups_for_user(username)         


def get_patient_list(user):
    u = Cognito(user_pool_id, app_client_id)
    patients = u.get_users(attr_map={"given_name": "first_name", "family_name": "last_name", "uuid": "custom:watchuuid"})
    if user.groups == 'admin':
        return patients
    elif user.groups == 'clinicians':
        return patients
    elif user.groups == "patient":
        return user

