from flask import request, jsonify, Blueprint,request, session,render_template, flash, redirect
from flask_login import  login_required
from src.libs.func.cognito import get_users , get_cognito_user
from src import application
from .forms import AddUserForm , UpdateUserForm
from src.libs.func.cognito import user_pool_id, app_client_id
from pycognito import Cognito
import boto3
from boto3.dynamodb.conditions import Key
import zlib
import cbor2
from functools import wraps


def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_group = session.get('group')
        if user_group != 'admin' :
            return render_template('admin/unauthorized.html', title='Unauthorized')
        return func(*args, **kwargs)
    return wrapper


dynamodb = boto3.resource('dynamodb')
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE'])

s3client = boto3.client('s3')
s3_bucket_name = application.config['S3_DATA_STORE_BUCKET_NAME']



@application.route('/admin')
@login_required
def admin_view():
    user_group = session.get('group') 
    if user_group == 'admin' :
       all_users = []
       users = get_users()
       for user in users:
           all_users.append(user._data)    
       return render_template('admin/admin.html', users= all_users)
    return render_template('admin/unauthorized.html', title='Unauthorized')


@application.route("/admin/add_user",methods=['GET', 'POST'])
@login_required
@admin_only
def admin_add_user():
    clinicians = ['Clinician ..']
    all_db_rows =db_table.scan()
    for row in all_db_rows['Items'] :
        if "USER#" in row['PK'] and  '#METADATA#' in row['SK'] :
            clinicians.append(row['PK'].split("#")[1])
    form = AddUserForm(clinician=clinicians)
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        middle_name = form.middle_name.data
        full_name = first_name + " " + last_name
        dob = form.dob.data
        bmi = form.bmi.data
        group = form.group.data
        gender = form.gender.data
        clinician = form.clinician.data
        temp_password = form.temp_password.data
        cognito = Cognito(user_pool_id, app_client_id)
        try :
            result = cognito.admin_create_user(username, temporary_password=temp_password, email = email,
                given_name = first_name, family_name = last_name, middle_name = middle_name,  name = full_name, 
                gender=gender, preferred_username= username ) 
            if result.get('User'):
                cognito.admin_add_user_to_group(username, group)
                item = { 
                    "PK" :  "USER#{}".format(username), 
                    "SK" : "#METADATA#{}".format(username),
                    "dob" : dob,
                    "bmi" : bmi,
                    "gender": gender,
                    "email": email,
                    "fname": first_name,
                    "lname": last_name,
                    "mname": middle_name,
                    "name": full_name,

                } 
                in_res = db_table.put_item(Item = item)
                if clinician != '0':
                    clinicianItem = { 
                        "PK" :  "USER#{}".format(username), 
                        "SK" : "#CLINICIAN#{}".format(clinicians[int(clinician)]),
                        "clinician" : clinicians[int(clinician)],
                        } 
                    clinician_add_res = db_table.put_item(Item = clinicianItem)
                flash("User Saved Successfully!", "success")
                return redirect("/admin")
        except Exception as e :
            if type(e).__name__ ==  'UsernameExistsException' :
                flash("Username Already exist !!", "danger")
            #import pdb; pdb.set_trace()
            #flash(str(e), "danger")
            return render_template('admin/add_user.html', title='Add User', form=form)

    return render_template('admin/add_user.html', title='Add User', form=form)    


@application.route("/admin/edit/<username>",methods=['GET', 'POST'])
@login_required
@admin_only
def admin_update_user(username):
    selected_db_user = None
    selected_clinician = None
    clinicians = ['Clinician ..']
    db_rows =db_table.scan()
    for row in db_rows['Items'] :
        if row['SK'] == "#METADATA#{}".format(username):
            selected_db_user = row
        if row['PK'] == "USER#{}".format(username) and  '#CLINICIAN#' in row['SK']:
            selected_clinician = row    
        if "USER#" in row['PK'] and  '#METADATA#' in row['SK']: 
            clinicians.append(row['PK'].split("#")[1])
     
    cognito_user, cognito_user_group = get_cognito_user(username) 

    form = UpdateUserForm(clinician=clinicians )

    if request.method == 'GET':
        first_name = cognito_user._data['name'].split(" ")[0] 
        last_name = cognito_user._data['name'].split(" ")[1]   
        form.first_name.data =first_name
        form.last_name.data =last_name
        form.middle_name.data =cognito_user._data.get("middle_name")
        form.dob.data = selected_db_user.get('dob')
        form.bmi.data = selected_db_user.get('bmi')
        form.group.data = cognito_user_group[0]
        form.gender.data = cognito_user._data.get('gender')
        form.fitbitid.data = selected_db_user.get('fitbitid')
        if selected_clinician :
            form.clinician.data = str(clinicians.index(selected_clinician["SK"].split("#")[2]))
        return render_template('admin/update_user.html', title='update User', form=form)    
   

    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        middle_name = form.middle_name.data
        full_name = first_name + " " + last_name
        dob = form.dob.data
        bmi = form.bmi.data
        group = form.group.data
        gender = form.gender.data
        fitbitid = form.fitbitid.data
        clinician = form.clinician.data

        cognito = Cognito(user_pool_id, app_client_id,username=username)

        try :
            result = cognito.admin_update_profile(attrs={'name' : full_name, 'gender': gender,'given_name': first_name,
                    'family_name':last_name, 'middle_name' : middle_name } )
            if group != cognito_user_group[0]:
                cognito.admin_remove_user_from_group(username, cognito_user_group[0])
                cognito.admin_add_user_to_group(username, group)
                
            response = db_table.query(
                IndexName='InvertedIndex',
                KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(username))
            )
            item = response['Items'][0]
            item['bmi'] = bmi
            item['dob'] = dob
            item['gender'] = gender
            item['fname'] = first_name
            item['lname'] = last_name
            item['mname'] = middle_name
            item['name'] = full_name
            item['fitbitid'] = fitbitid

            db_table.put_item(Item=item)
        
            if selected_clinician :
                prev_clinician_index = str(clinicians.index(selected_clinician["SK"].split("#")[2]))
                if clinician!= '0' and clinician != prev_clinician_index :
                    db_table.delete_item(Key={
                        "PK" :  "USER#{}".format(username), 
                        "SK" : "#CLINICIAN#{}".format(clinicians[int(prev_clinician_index)]),
                    })
                    
                    new_clinicianItem = { 
                        "PK" :  "USER#{}".format(username), 
                        "SK" : "#CLINICIAN#{}".format(clinicians[int(clinician)]),
                        "clinician" : clinicians[int(clinician)],
                        } 
                    db_table.put_item(Item=new_clinicianItem)

                if clinician == '0' :
                    db_table.delete_item(Key={
                        "PK" :  "USER#{}".format(username), 
                        "SK" : "#CLINICIAN#{}".format(clinicians[int(prev_clinician_index)]),
                    },) 

            else:
                if clinician != '0':
                    clinicianItem = { 
                        "PK" :  "USER#{}".format(username), 
                        "SK" : "#CLINICIAN#{}".format(clinicians[int(clinician)]),
                        "clinician" : clinicians[int(clinician)],
                        } 
                    clinician_add_res = db_table.put_item(Item = clinicianItem)

            flash("User Updated Successfully!", "success")
            return redirect("/admin")
        except Exception as e :
            print (e)
            if type(e).__name__ ==  'UsernameExistsException' :
                flash("Username Already exist !!", "danger")
        
            flash(str(e), "danger")
            return render_template('admin/update_user.html', title='update User', form=form)

    return render_template('admin/update_user.html', title='update User', form=form)    

@application.route("/admin/s3_files", methods=['GET'])
@login_required
@admin_only
def admin_s3_files():
    
    after = request.args.get('after', '')
    after_list = after.split("/")
    #after_list.insert(0, after_list.pop())
    after_list.pop()
    link_list = []
    temp = ''
    for idx, val in enumerate(after_list):
        temp +=  val+"/"
        link_list.append({'label':str(val),'link':temp})
        
    link_list.insert(0, {'label':s3_bucket_name,'link':''})        

    folders= []
    files = []
    response = s3client.list_objects_v2(
        Bucket=s3_bucket_name, 
        Prefix=after, Delimiter="/")  
    if 'CommonPrefixes' in  response:
        folders.extend([x['Prefix'] for x in response['CommonPrefixes']])  

    if 'Contents' in  response:  
        files.extend([x for x in response['Contents']])

    return render_template('admin/s3_files.html', folders=folders,files = files, link_list= link_list) 


@application.route("/admin/s3_view_file", methods=['GET'])
@login_required
@admin_only
def admin_s3_view_file():
    key = request.args.get('key', '')
    file_name = key.split("/")[-1]
    obj = s3client.get_object(Bucket=s3_bucket_name, Key=key)
    contents = obj['Body'].read() 
    if 'fitbit' in key:
        str_content = cbor2.loads(contents)
        count = len(str_content)
    else:
        str_object = zlib.decompress(contents, -zlib.MAX_WBITS) 
        str_content = str_object.decode("utf-8")
        count = len(str_content.split('\r\n'))  

    return render_template('admin/s3_file_view.html', file_name=file_name ,count = count, contents=str_content)