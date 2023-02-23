from dateutil.parser import parse
import pandas as pd
import numpy as np
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from src import application
from src.libs.func.cognito import get_cognito_user
from collections import Counter

dynamodb = boto3.resource('dynamodb')
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE']) 

s3client = boto3.client('s3')
s3_bucket_name = application.config['S3_PROCESSED_BUCKET']

sleep_time_recommendation = {
    'days' :   [{'1-15':16}],
    'months' : [{'3-5':14}, {'6-23':13.6}],
    'years' :  [{'2-3':12}, {'3-5':11.5}, {'5-9':11}, {'10-13':10}, {'14-18':8.5}, {'19-30':8}, {'33-45':7.5}, {'50-70':7}, {'70-80':6.5}]
}

#outofbedtime - bedtime need to change 
def is_five_hr_night(night):
    if 'WakeUpTime' in night:
        wakeuptime = parse(night['WakeUpTime'])
    else:
        wakeuptime = parse(night['SleepOffset'])      
    bedtime = parse(night['BedTime']) 
    if bedtime.hour >= 19 or bedtime.hour <= 6 :
        
        timeDiff = (wakeuptime - bedtime).seconds/3600  #in hour
        
        if  timeDiff > 4 :
           return True
    return False 
    
def custom_date_parser(date):
    # date parser to check -- in the string 
    if '--' in date :
       return parse("+".join(date.split("--")))
    else:
        return parse(date) 

def download_csv_file(url):
    try:
        #
        print (url)
        return pd.read_csv(url)
    except Exception as e:
        print ("error in csv",e)  


def get_multi_night_summary (multi_day_df):
    multi_night_summary = []
    
    filtered_df = multi_day_df
    filtered_df.replace(np.nan, 0)
    filtered_df['Efficiency'] = filtered_df['Efficiency'].apply(lambda eff : float(eff.split('%')[0]))
    
    multi_night_summary.append({'Metric':'TST','max': int(filtered_df['TST'].max()), 
                                 'min':int (filtered_df['TST'].min()), 'mean': int(filtered_df['TST'].mean())})
    multi_night_summary.append({'Metric':'REM Time','max': int(filtered_df['REMTime'].max()) , 
                                 'min': int(filtered_df['REMTime'].min()) , 'mean': int(filtered_df['REMTime'].mean()) })
    multi_night_summary.append({'Metric':'NREM Time','max':int(filtered_df['NREMTime'].max()) , 
                                 'min': int(filtered_df['NREMTime'].min()) , 'mean': int(filtered_df['NREMTime'].mean()) })
    multi_night_summary.append({'Metric':'Wake Time','max':int(filtered_df['WAKE'].max()) , 
                                 'min': int(filtered_df['WAKE'].min()) , 'mean': int(filtered_df['WAKE'].mean()) }) 
    multi_night_summary.append({'Metric':'TIB','max':int(filtered_df['TIB'].max()) , 
                                 'min': int(filtered_df['TIB'].min()) , 'mean': int(filtered_df['TIB'].mean()) })
    multi_night_summary.append({'Metric':'WASO','max':int(filtered_df['WASO'].max()) , 
                                 'min': int(filtered_df['WASO'].min()) , 'mean': int(filtered_df['WASO'].mean()) })
    multi_night_summary.append({'Metric':'Awakenings','max':int(filtered_df['Awakenings'].max()) , 
                                 'min': int(filtered_df['Awakenings'].min()) , 'mean': int(filtered_df['Awakenings'].mean()) })
    multi_night_summary.append({'Metric':'Sleep Latency','max':int(filtered_df['SleepLatency'].max()) , 
                                 'min': int(filtered_df['SleepLatency'].min()) , 'mean': int(filtered_df['SleepLatency'].mean()) })
    multi_night_summary.append({'Metric':'REM Latency','max':int(filtered_df['REMLatency'].max()) , 
                                 'min': int(filtered_df['REMLatency'].min()) , 'mean': int(filtered_df['REMLatency'].mean()) })
    multi_night_summary.append({'Metric':'Efficiency','max':float(filtered_df['Efficiency'].max()) , 
                                 'min': float(filtered_df['Efficiency'].min()) , 'mean': float("{0:.2f}".format(filtered_df['Efficiency'].mean())) })                                                                                                                                                                                                                                                                                                  
    return multi_night_summary

def get_fitbit_night_options(user_name):
    night_options = []
    response = db_table.query(
        IndexName='InvertedIndex',
        KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(user_name))) 
    user = response['Items'][0]
    fitbitid = user['fitbitid']
    night_options_df = pd.read_csv(s3_bucket_name +'fitbit/' +str(fitbitid)+ '/multi_day.csv')
    night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
    night_options_dict = night_options_df.to_dict('records')
    night_options_list = []
    for night in night_options_dict :
        if is_five_hr_night(night):
            night_options_list.append(night['DateTime'])
    #night_options_list = night_options_df['DateTime'].tolist()
    night_options_counter = dict(Counter(night_options_list))
    print (night_options_counter) 
    for night, value in night_options_counter.items():
        for x in range( value):
            if x == 0 :
                night_options.append({'label':custom_date_parser(night).strftime('%Y-%m-%d %H:%M:%S'),
                'value': "{}/{}".format(fitbitid ,night)  })
            else:
                night_options.append({'label':"{} _{}".format(custom_date_parser(night).strftime('%Y-%m-%d %H:%M:%S'), x),
                'value': "{}/{}/_{}".format(fitbitid ,night, x)})
                        
    return  night_options 

def get_apple_night_options(user_name):
    night_options = []
    night_options_df = pd.read_csv(s3_bucket_name +'apple/' +user_name+ '/multi_day.csv')
    night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
    night_options_dict = night_options_df.to_dict('records')
    night_options_list = []
    for night in night_options_dict :
        if is_five_hr_night(night):
            night_options_list.append(night['DateTime'])
    #night_options_list = night_options_df['DateTime'].tolist()
    night_options_counter = dict(Counter(night_options_list))
    for night, value in night_options_counter.items():
        for x in range(value):
            if x == 0 :
                night_options.append({'label':custom_date_parser(night).strftime('%Y-%m-%d %H:%M:%S'),
                        'value': "{}/{}".format('apple' , night ) })
            else:
                night_options.append({'label': "{} _{}".format(custom_date_parser(night).strftime('%Y-%m-%d %H:%M:%S'), x) ,
                    'value': "{}/{}/_{}".format('apple' ,night, x)})

    return  night_options

def get_uuid_night_options(user_name):
    night_options = []
    cognito_user = get_cognito_user(user_name)
    user_uuids = cognito_user[0]._data['custom:watchuuid']
    uuids_list = user_uuids.split(":")
    for uuid in uuids_list :
        try:
            night_options_df = pd.read_csv(s3_bucket_name  + uuid + '/multi_day.csv')
            night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
            all_night_options = night_options_df.to_dict('records') 
            for night in all_night_options :
                night_options.append({'label':custom_date_parser(night['DateTime']).strftime('%Y-%m-%d %H:%M:%S'),
                        'value': "{}/{}".format(uuid ,night['DateTime'])  })
        except Exception as e:
            pass

    return  night_options  

def get_file_names(extension = None ):
    file_names={}
    file_names['activity'] = 'activity.csv'
    file_names['heartrate'] = 'heartrate.csv'
    file_names['stage_prediction'] = '{}{}{}'.format('stage_prediction',extension,'.csv') if extension else 'stage_prediction.csv'
    file_names['stages_duration'] = '{}{}{}'.format('stages_duration',extension,'.csv') if extension else 'stages_duration.csv'
    file_names['sleep_metrics'] = '{}{}{}'.format('sleep_metrics',extension,'.csv') if extension else 'sleep_metrics.csv'
    file_names['epoch_time'] = '{}{}{}'.format('epoch_time',extension,'.csv') if extension else 'epoch_time.csv'
    file_names['awakenings'] = '{}{}{}'.format('awakenings',extension,'.csv') if extension else 'awakenings.csv'
    print (file_names)
    return file_names

def get_fitbit_data(user_name, night):

    fitbit_data ={}
    try:
        splited_night_str = night.split('/')       
        fitbitid = splited_night_str[0]
        night_folder = splited_night_str[1]
        extension = splited_night_str[2] if len(splited_night_str) == 3 else None
        file_names = get_file_names(extension)

        path_to_s3_processed = s3_bucket_name + 'fitbit/'+ fitbitid + '/' + night_folder
        fitbit_data['prediction'] = pd.read_csv(path_to_s3_processed + '/' + file_names['stage_prediction'])
        fitbit_data['sleep_metrics_df'] = pd.read_csv(path_to_s3_processed+ '/' + file_names['sleep_metrics'])
        fitbit_data['stages_duration_df'] = pd.read_csv(path_to_s3_processed+ '/' + file_names['stages_duration'])
        fitbit_data['hr'] =  pd.read_csv( path_to_s3_processed + '/' + file_names['heartrate'], header=None, skiprows=1)
        fitbit_data['activity'] = pd.read_csv(path_to_s3_processed+ '/'+ file_names['activity'], header=None,
                                skiprows=1)
        fitbit_data['epoch_time'] = pd.read_csv(path_to_s3_processed+ '/'+ file_names['epoch_time'], header=None,
                                    skiprows=1).values[:, 0]
        fitbit_data['awakeings'] = pd.read_csv(path_to_s3_processed+ '/' + file_names['awakenings'])
        fitbit_data['multi_day_df'] = pd.read_csv(s3_bucket_name + 'fitbit/'+ fitbitid + '/multi_day.csv').to_dict("rows")
        return fitbit_data                     
        
    except FileNotFoundError as e:
            print("Not found :", str(e))

def get_apple_data(user_name, night):

    apple_data ={}
    splited_night_str = night.split('/')
    night_folder = splited_night_str[1]
    extension = splited_night_str[2] if len(splited_night_str) == 3 else None
    file_names = get_file_names(extension)

    try:       
        path_to_s3_processed = s3_bucket_name + 'apple/'+ user_name + '/' + night_folder
        apple_data['prediction'] = pd.read_csv(path_to_s3_processed + '/' + file_names['stage_prediction'])
        apple_data['sleep_metrics_df'] = pd.read_csv(path_to_s3_processed+ '/' + file_names['sleep_metrics'])
        apple_data['stages_duration_df'] = pd.read_csv(path_to_s3_processed+ '/' + file_names['stages_duration'])
        apple_data['hr'] =  pd.read_csv( path_to_s3_processed + '/' + file_names['heartrate'], header=None, skiprows=1)
        apple_data['activity'] = pd.read_csv(path_to_s3_processed+ '/'+ file_names['activity'], header=None,
                                skiprows=1)
        apple_data['epoch_time'] = pd.read_csv(path_to_s3_processed+ '/'+ file_names['epoch_time'], header=None,
                                    skiprows=1).values[:, 0]
        apple_data['awakeings'] = pd.read_csv(path_to_s3_processed+ '/' + file_names['awakenings'])
        apple_data['multi_day_df'] = pd.read_csv(s3_bucket_name + 'apple/'+ user_name + '/multi_day.csv').to_dict("rows")
        return apple_data                     
        
    except FileNotFoundError as e:
            print("Not found :", str(e)) 

def get_uuid_data(user_name, night):

    uuid_data ={}
    uuid = night.split('/')[0]
    night_folder = night.split('/')[1]

    try:       
        path_to_s3_processed = s3_bucket_name + uuid + '/' + night_folder
        uuid_data['prediction'] = pd.read_csv(path_to_s3_processed + '/stage_prediction.csv')
        uuid_data['sleep_metrics_df'] = pd.read_csv(path_to_s3_processed+ '/sleep_metrics.csv')
        uuid_data['stages_duration_df'] = pd.read_csv(path_to_s3_processed+ '/stages_duration.csv')
        uuid_data['hr'] =  pd.read_csv( path_to_s3_processed + '/heartrate.csv', header=None, skiprows=1)
        uuid_data['activity'] = pd.read_csv(path_to_s3_processed+ '/activity.csv', header=None,
                                skiprows=1).values
        uuid_data['epoch_time'] = pd.read_csv(path_to_s3_processed+ '/epoch_time.csv', header=None,
                                    skiprows=1).values[:, 0]
        uuid_data['awakeings'] = pd.read_csv(path_to_s3_processed+ '/awakenings.csv')
        uuid_data['multi_day_df'] = pd.read_csv(s3_bucket_name + uuid + '/multi_day.csv').to_dict("rows")
        return uuid_data                     
        
    except FileNotFoundError as e:
            print("Not found :", str(e))                                     

def get_fitbit_multi_night_data(username, start_date, end_date):
    fitbit_data ={}
    response = db_table.query(
        IndexName='InvertedIndex',
        KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(username))) 
    user = response['Items'][0]
    fitbitid = user['fitbitid']
    path_to_s3_processed = s3_bucket_name + 'fitbit/'+ fitbitid
    profile_json  = pd.read_json(path_to_s3_processed + '/' + 'profile.json', typ='series')
    night_options_df = pd.read_csv(path_to_s3_processed + '/' + 'multi_day.csv')
    night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
    all_night_dict = night_options_df.replace(np.nan, 0).to_dict('records')
    nights_data = []
    for night in all_night_dict :
        night_date = custom_date_parser(night['DateTime']).date()
        if( start_date <= night_date <= end_date and is_five_hr_night(night)):
            nights_data.append(night)

    fitbit_data['nights_data'] = nights_data 
    fitbit_data['multi_night_summary'] = get_multi_night_summary(night_options_df, start_date, end_date)
    fitbit_data['profile_json'] = profile_json    

    resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix='fitbit/'+fitbitid+'/', Delimiter="/")
    
    folders = [x['Prefix'].split('/')[2] for x in resp['CommonPrefixes']]
    night_folders=[]
    for rec_folder in folders:
        try:
            recording_date = custom_date_parser(rec_folder).date()
            if( start_date <= recording_date <= end_date):
                night_folders.append({'path':path_to_s3_processed,'night':rec_folder})

        except Exception as e:
            print (e)

    fitbit_data['night_folders'] = night_folders
    return fitbit_data

def get_apple_multi_night_data(username, start_date, end_date):
    apple_data ={}
    path_to_s3_processed = s3_bucket_name + 'apple/'+ username
    profile_json  = pd.read_json(path_to_s3_processed + '/' + 'profile.json') 
    night_options_df = pd.read_csv(path_to_s3_processed + '/' + 'multi_day.csv')
    night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
    all_night_dict = night_options_df.replace(np.nan, 0).to_dict('records')
    nights_data = []
    for night in all_night_dict :
        night_date = custom_date_parser(night['DateTime']).date()
        if( start_date <= night_date <= end_date and is_five_hr_night(night)):
            nights_data.append(night)

    apple_data['nights_data'] = nights_data
    apple_data['multi_night_summary'] = get_multi_night_summary(night_options_df, start_date, end_date)
    apple_data['profile_json'] = profile_json    

    resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix='apple/'+username+'/', Delimiter="/")
    
    folders = [x['Prefix'].split('/')[2] for x in resp['CommonPrefixes']]
    night_folders=[]
    for rec_folder in folders:
        try:
            recording_date = custom_date_parser(rec_folder).date()
            if( start_date <= recording_date <= end_date):
                night_folders.append({'path':path_to_s3_processed,'night':rec_folder})

        except Exception as e:
            print (e)

    apple_data['night_folders'] = night_folders
    return apple_data 

def get_uuuid_multi_night_data(username, start_date, end_date):
    uuid_data ={}

    cognito_user = get_cognito_user(username)
    user_uuids = cognito_user[0]._data['custom:watchuuid']
    uuids_list = user_uuids.split(":")
    
    nights_data = []
    night_folders=[]
    for uuid in uuids_list:
        try:
            path_to_s3_processed = s3_bucket_name+ str(uuid)
            night_options_df = pd.read_csv(path_to_s3_processed+ '/multi_day.csv')
            night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
            all_night_dict = night_options_df.replace(np.nan, 0).to_dict('records')
            for night in all_night_dict :
                night_date = custom_date_parser(night['DateTime']).date()
                if( start_date <= night_date <= end_date and is_five_hr_night(night)):
                    nights_data.append(night)
            
            resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix=uuid+'/', Delimiter="/")
            folders = [x['Prefix'].split('/')[1] for x in resp['CommonPrefixes']]           
            for rec_folder in folders:
                try:
                    recording_date = custom_date_parser(rec_folder).date()
                    if( start_date <= recording_date <= end_date):
                        night_folders.append({'path':path_to_s3_processed,'night':rec_folder})

                except Exception as e:
                    print (e)     
       
        except Exception as e:
            print("Not found :", str(e))

    uuid_data['nights_data'] = nights_data 
    uuid_data['night_folders'] = night_folders 
    return uuid_data

def get_fitbit_narcolepsy_data(username, start_date, end_date):
    fitbit_data = {}
    response = db_table.query(
        IndexName='InvertedIndex',
        KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(username)))
    user = response['Items'][0]
    fitbitid = user['fitbitid']
    path_to_s3_processed = s3_bucket_name + 'fitbit/' + fitbitid
    night_options_df = pd.read_csv(path_to_s3_processed + '/' + 'multi_day.csv')
    night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
    all_night_dict = night_options_df.replace(np.nan, 0).to_dict('records')
    nights_data = []
    for night in all_night_dict:
        night_date = custom_date_parser(night['DateTime']).date()
        if (start_date <= night_date <= end_date):
            nights_data.append(night)

    fitbit_data['nights_data'] = nights_data

    resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix='fitbit/' + fitbitid + '/', Delimiter="/")

    folders = [x['Prefix'].split('/')[2] for x in resp['CommonPrefixes']]
    night_folders = []
    for rec_folder in folders:
        try:
            recording_date = custom_date_parser(rec_folder).date()
            if (start_date <= recording_date <= end_date):
                night_folders.append({'path': path_to_s3_processed, 'night': rec_folder})

        except Exception as e:
            print(e)

    fitbit_data['night_folders'] = night_folders
    return fitbit_data

def get_apple_narcolepsy_data(username, start_date, end_date):
    apple_data = {}
    path_to_s3_processed = s3_bucket_name + 'apple/' + username
    night_options_df = pd.read_csv(path_to_s3_processed + '/' + 'multi_day.csv')
    night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
    all_night_dict = night_options_df.replace(np.nan, 0).to_dict('records')
    nights_data = []
    for night in all_night_dict:
        night_date = custom_date_parser(night['DateTime']).date()
        if (start_date <= night_date <= end_date):
            nights_data.append(night)

    apple_data['nights_data'] = nights_data

    resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix='apple/' + username + '/', Delimiter="/")

    folders = [x['Prefix'].split('/')[2] for x in resp['CommonPrefixes']]
    night_folders = []
    for rec_folder in folders:
        try:
            recording_date = custom_date_parser(rec_folder).date()
            if (start_date <= recording_date <= end_date):
                night_folders.append({'path': path_to_s3_processed, 'night': rec_folder})

        except Exception as e:
            print(e)

    apple_data['night_folders'] = night_folders
    return apple_data

def get_uuuid_narcolepsy_data(username, start_date, end_date):
    uuid_data = {}

    cognito_user = get_cognito_user(username)
    user_uuids = cognito_user[0]._data['custom:watchuuid']
    uuids_list = user_uuids.split(":")

    nights_data = []
    night_folders = []
    for uuid in uuids_list:
        try:
            path_to_s3_processed = s3_bucket_name + str(uuid)
            night_options_df = pd.read_csv(path_to_s3_processed + '/multi_day.csv')
            night_options_df = night_options_df.drop_duplicates('BedTime', keep='last')
            all_night_dict = night_options_df.replace(np.nan, 0).to_dict('records')
            for night in all_night_dict:
                night_date = custom_date_parser(night['DateTime']).date()
                if (start_date <= night_date <= end_date):
                    nights_data.append(night)

            resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix=uuid + '/', Delimiter="/")
            folders = [x['Prefix'].split('/')[1] for x in resp['CommonPrefixes']]
            for rec_folder in folders:
                try:
                    recording_date = custom_date_parser(rec_folder).date()
                    if (start_date <= recording_date <= end_date):
                        night_folders.append({'path': path_to_s3_processed, 'night': rec_folder})

                except Exception as e:
                    print(e)

        except Exception as e:
            print("Not found :", str(e))

    uuid_data['nights_data'] = nights_data
    uuid_data['night_folders'] = night_folders
    return uuid_data

def get_night_recordings_from_folders(night_folders):
    all_labels = []
    all_times = []
    all_awakeings = []
    all_hr = []
    all_activity = []
    all_sleep=[]

    ngiht_recordings = {}

    for nights in night_folders :

        try:
            path_to_s3_processed = nights['path']+ '/' +nights['night']

            sleep = download_csv_file(path_to_s3_processed + '/sleep_wake.csv')
            if sleep is not None :
               all_sleep.append(sleep)
            activity = download_csv_file(path_to_s3_processed + '/activity.csv')
            if activity is not None :
               all_activity.append(activity)
            hr = download_csv_file(path_to_s3_processed + '/heartrate.csv')
            if hr is not None :
               all_hr.append(hr)

            next_label = True
            label_no = 0
            while  next_label:
                file_name = '/stage_prediction.csv' if label_no == 0 else '/stage_prediction_{}.csv'.format(label_no)
                labels = download_csv_file(path_to_s3_processed + file_name)

                if  labels is not None :
                    all_labels.append(labels['labels'])
                    label_no+=1
                else:
                    next_label = False

            next_time = True
            time_no = 0
            while  next_time:
                file_name = '/epoch_time.csv' if time_no == 0 else '/epoch_time_{}.csv'.format(time_no)
                times = download_csv_file(path_to_s3_processed + file_name)
                if times is not None :
                    all_times.append(times)
                    time_no+=1
                else:
                    next_time = False

            next_awakeing = True
            awakeing_no = 0
            while  next_awakeing:
                file_name = '/awakenings.csv' if awakeing_no == 0 else '/awakenings_{}.csv'.format(awakeing_no)
                awakeings = download_csv_file(path_to_s3_processed + file_name)
                if awakeings is not None :
                    all_awakeings.append(awakeings)
                    awakeing_no+=1
                else:
                    next_awakeing = False

        except Exception as e:
            print ("err in charts.py",e)

        ngiht_recordings['sleep'] = all_sleep
        ngiht_recordings['activity'] = all_activity
        ngiht_recordings['hr'] = all_hr
        ngiht_recordings['labels'] = all_labels
        ngiht_recordings['awakeings'] = all_awakeings
        ngiht_recordings['times'] = all_times

    return ngiht_recordings

def get_night_recordings_from_folders_time_zone(night_folders):
    all_labels = []
    all_times = []
    all_awakeings = []
    all_hr = []
    all_activity = []
    all_sleep=[]

    ngiht_recordings = {}

    for nights in night_folders :

        try:

            path_to_s3_processed = nights['path']+ '/' +nights['night']

            time_zone = int(nights['night'][-5] + str(int(nights['night'][-4:-2]) * 3600 + int(nights['night'][-2:]) * 60))

            sleep = download_csv_file(path_to_s3_processed + '/sleep_wake.csv')
            if sleep is not None :
               all_sleep.append({'sleep':sleep, 'time_zone':time_zone})
            activity = download_csv_file(path_to_s3_processed + '/activity.csv')
            if activity is not None :
               all_activity.append({'activity':activity, 'time_zone':time_zone})
            hr = download_csv_file(path_to_s3_processed + '/heartrate.csv')
            if hr is not None :
               all_hr.append({'hr':hr, 'time_zone':time_zone})
               

            next_label = True
            label_no = 0
            while  next_label:
                file_name = '/stage_prediction.csv' if label_no == 0 else '/stage_prediction_{}.csv'.format(label_no)
                labels = download_csv_file(path_to_s3_processed + file_name)

                if  labels is not None :
                    all_labels.append({'labels':labels['labels'], 'time_zone':time_zone})
                    label_no+=1
                else:
                    next_label = False

            next_time = True
            time_no = 0
            while  next_time:
                file_name = '/epoch_time.csv' if time_no == 0 else '/epoch_time_{}.csv'.format(time_no)
                times = download_csv_file(path_to_s3_processed + file_name)
                if times is not None :
                    all_times.append({'times':times, 'time_zone':time_zone})
                    time_no+=1
                else:
                    next_time = False

            next_awakeing = True
            awakeing_no = 0
            while  next_awakeing:
                file_name = '/awakenings.csv' if awakeing_no == 0 else '/awakenings_{}.csv'.format(awakeing_no)
                awakeings = download_csv_file(path_to_s3_processed + file_name)
                if awakeings is not None :
                    all_awakeings.append({'awakeings':awakeings, 'time_zone':time_zone})
                    awakeing_no+=1
                else:
                    next_awakeing = False

        except Exception as e:
            print ("err in charts.py",e)

        ngiht_recordings['sleep'] = all_sleep
        ngiht_recordings['activity'] = all_activity
        ngiht_recordings['hr'] = all_hr
        ngiht_recordings['labels'] = all_labels
        ngiht_recordings['awakeings'] = all_awakeings
        ngiht_recordings['times'] = all_times

    return ngiht_recordings
