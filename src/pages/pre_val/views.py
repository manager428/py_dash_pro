from dateutil.parser import parse
from flask import request, jsonify, request, session, render_template, flash, redirect
from flask_login import  login_required

import pandas as pd
import numpy as np
import json 
import plotly
from dateutil.parser import parse
import datetime
import boto3
from boto3.dynamodb.conditions import Key

from src import application
from src.libs.utils import download_csv_file, sleep_time_recommendation, get_night_recordings_from_folders
from src.libs.charts import generate_circadian_rhythms

from .hypnogram_tab_1 import Hypnogram
from .hypnogram_tab_4 import MsltHypnogram
from .epoch_by_epoch_analysis import main
from .pre_val_utils import *     
from .circadian_rhythms_tab_2 import CircanianRhythms
from .circadian_rhythms_tab_4 import MsltCircanianRhythms

dynamodb = boto3.resource('dynamodb')

users_data =   's3://'+application.config['S3_DATA_STORE_BUCKET_NAME']+ '/psg/psg-apple-fitbit.xlsx'
users_tat2_table_data =   's3://'+application.config['S3_DATA_STORE_BUCKET_NAME']+ '/psg/pre-val-2021-usable-nights.xlsx'
s3_bucket_name = application.config['S3_PROCESSED_BUCKET']
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE']) 

def get_device_id(device):
    if device == 'Apple':
        return 'ID'
    if device == 'Fitbit':
        return 'FitbitID'        

@application.route('/pre_val')
@login_required
def pre_val():
    tab = request.args.get('tab', 1)
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')
    user_options = df['ID'].to_list()
    cohort_options = set(df['Cohort'].to_list())
    total_patients = len(df)
    sleep_time_rec = json.dumps(sleep_time_recommendation)
    df['Start'] = df['Start'].dt.strftime('%Y%m%d')
    df['End'] = df['End'].dt.strftime('%Y%m%d')
    print(df)
    df = df.fillna("NaN")
    user_nights = df[['ID','Start','End']].to_dict('records')
    return render_template('pre_val/group_analysis_{}.html'.format(tab), title='Pre Val',
                    user_options=user_options,cohort_options=cohort_options,
                    total_patients=total_patients, sleep_time_rec = sleep_time_rec,
                    user_nights = json.dumps(user_nights))

@application.route('/pre_val1_group_data')
@login_required
def pre_val1_data():
    selected_users = request.args.get('selected_users')
    selected_device = request.args.get('selected_device')
    selected_cohort = request.args.get('selected_cohort')
    selected_age = request.args.get('selected_age')
    selected_gender = request.args.get('selected_gender')
    users = []
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl') 
    df['age'] = df.apply(lambda row: get_user_age(row), axis=1)
    df['gender'] = df.apply(lambda row: get_user_gender(row), axis=1)
    if selected_users:
        df = df[df['ID'].isin(selected_users.split(','))]
    if selected_cohort and selected_cohort != '0' :
        df = df[df['Cohort'] == selected_cohort] 
    if selected_age and selected_age not in ['0', 'all']:
        age_range = selected_age.split('-')
        df = df[ df['age'].isnull() | (df['age'] >= float(age_range[0])) & (df['age'] <= float(age_range[1]))]
    if selected_gender and selected_gender !='0':
        df = df[df['gender'] == selected_gender] 
    print (df)        
    # get time from any apple or fitbit folder string 
    # convert timezone from 5 last characters of night name to seconds. '-0800' --> -28800 seconds
    folder_str = df['Apple'].values[0]
    time_zone = int(folder_str[-5] + str(int(folder_str[-4:-2]) * 3600 + int(folder_str[-2:]) * 60))
    
    users_dict = df.to_dict('records')
    for user in users_dict:
        device_folder = user[selected_device]
        try:
            sleep_metrics = download_csv_file(s3_bucket_name + selected_device.lower() + '/' +user[get_device_id(selected_device)]+ '/' + device_folder +  '/sleep_metrics.csv')
            stage_prediction = download_csv_file(s3_bucket_name + selected_device.lower() + '/' +user[get_device_id(selected_device)]+ '/' + device_folder +  '/stage_prediction.csv')
            psg_stage_prediction = download_csv_file(s3_bucket_name + "psg" + '/' +user['OSMIID']+ '/stage_prediction.csv')
            epoch_time = download_csv_file(s3_bucket_name + selected_device.lower() + '/' +user[get_device_id(selected_device)]+ '/' + device_folder +  '/epoch_time.csv')
            psg_epoch_time = download_csv_file(s3_bucket_name + "psg" + '/' +user['OSMIID']+ '/epoch_time.csv')
            
            user['stage_prediction'] = stage_prediction
            user['psg_stage_prediction'] = psg_stage_prediction
            # if epoch_time is not None:  
            #    epoch_time['time'] = epoch_time.apply(lambda row: row['time']+time_zone, axis=1)
            user['epoch_time'] = epoch_time
            user['psg_epoch_time'] = psg_epoch_time
            if sleep_metrics is not None: 
                sleep_metrics= df_efficiency_to_int(sleep_metrics)
                user['sleep_metrics'] = sleep_metrics
            users.append(user) 
        except Exception as e:
            print (e)

    jsonResponse = {}

    user_dict_eval = {}
    for user in users:
        if all(df is not None for df in (user['psg_epoch_time'],user['psg_stage_prediction'],user['epoch_time'], user['stage_prediction'])):
            user_dict_eval[user['ID']]= [pd.DataFrame({'time': user['psg_epoch_time']['time'].values,'stage':user['psg_stage_prediction']['labels'].values}), 
                              pd.DataFrame({'time': user['epoch_time']['time'].values,'stage':user['stage_prediction']['labels'].values})]
    try: 
        result_intersection, result_union = main (user_dict_eval)
        result_intersection.drop('Device', axis=1, inplace=True)
        result_intersection = result_intersection.fillna("NaN")
        result_intersection = result_intersection.set_index('Stage').transpose()

        result_union.drop('Device', axis=1, inplace=True)
        result_union = result_union.fillna("NaN")
        result_union = result_union.set_index('Stage').transpose()

        jsonResponse['eval_statics_intersection'] = result_intersection.to_html(classes = 'table table-striped' , justify = 'unset', border =0)
        jsonResponse['eval_statics_union'] = result_union.to_html(classes = 'table table-striped' , justify = 'unset', border =0)

    except Exception as e :
        print (e)  
    
    users_dfs = [user['sleep_metrics']  for user in users if  'sleep_metrics' in user]                       
    gruop_by_df= pd.concat( users_dfs , axis=0).dropna(axis=1).groupby('Metric')
    statics_df = pd.DataFrame({'Metric': gruop_by_df.groups.keys(),
                              'mean': gruop_by_df.mean()['Value'].values,
                              'max': gruop_by_df.max()['Value'].values,
                              'min': gruop_by_df.min()['Value'].values,
                              'std': gruop_by_df.std()['Value'].values, 
                             })
    statics_df = statics_df.fillna(0)
    statics_df=statics_df.round(2)                        
    statics_dict = statics_df.to_dict('records')
    jsonResponse['statics_dict'] = statics_dict
    jsonResponse['total_users'] = len(users_dfs)
    return jsonify(jsonResponse)


@application.route('/pre_val1_individual_data')
@login_required
def pre_val1_individual_data():  
    selected_user = request.args.get('selected_user')
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')
    
    user_row = df.loc[df['ID'] == selected_user]
    apple_folder = user_row['Apple'].values[0]
    fitbit_folder = user_row['Fitbit'].values[0]
    fitbitID = user_row['FitbitID'].values[0]
    PSGID = user_row['PSG'].values[0]
    apple_night_folder = []
    fitbit_night_folder = []
    psg_night_folder = []
    # convert timezone from 5 last characters of night name to seconds. '-0800' --> -28800 seconds
    time_zone = int(apple_folder[-5] + str(int(apple_folder[-4:-2]) * 3600 + int(apple_folder[-2:]) * 60))

    apple_night_folder.append({'path':s3_bucket_name+'apple'+'/'+selected_user,'night':apple_folder})
    fitbit_night_folder.append({'path':s3_bucket_name+'fitbit'+'/'+fitbitID,'night':fitbit_folder})
    psg_night_folder.append({'path':s3_bucket_name+'psg','night':PSGID})
    psg_lables = pd.read_csv(psg_night_folder[0]['path'] + '/' + psg_night_folder[0]['night'] + '/'+ 'stage_prediction.csv')
    psg_awakeings = pd.read_csv(psg_night_folder[0]['path'] + '/' + psg_night_folder[0]['night'] + '/'+ 'awakenings.csv')
    psg_epoch = pd.read_csv(psg_night_folder[0]['path'] + '/' + psg_night_folder[0]['night'] + '/'+ 'epoch_time.csv')
    psg_hr = pd.read_csv(psg_night_folder[0]['path'] + '/' + psg_night_folder[0]['night'] +'/'+  'heartrate.csv')
    hypnogram_fig = Hypnogram.plotly_display(psg_lables, psg_awakeings, 3,int(time_zone),time=psg_epoch['time'].values, heart_rate=psg_hr ,classifier_name='ensemble')
    jsonResponse = {}
    jsonResponse['quality_issues'] = {}

    try:
        apple_multi_day_csv= pd.read_csv(apple_night_folder[0]['path'] +  '/multi_day.csv')
        issue = apple_multi_day_csv[apple_multi_day_csv['DateTime']==apple_folder]['Quality Issues'].values[0]
        jsonResponse['quality_issues']['apple'] = str(issue)
    except Exception as e :
        pass

    try:
        fitbit_multi_day_csv= pd.read_csv(fitbit_night_folder[0]['path'] +  '/multi_day.csv')
        issue = fitbit_multi_day_csv[fitbit_multi_day_csv['DateTime']==fitbit_folder]['Quality Issues'].values[0]
        jsonResponse['quality_issues']['fitbit'] = str(issue)
    except Exception as e :
        pass

    try:
        apple_lables = pd.read_csv(apple_night_folder[0]['path'] + '/' + apple_night_folder[0]['night'] + '/'+ 'stage_prediction.csv')
        apple_epoch = pd.read_csv(apple_night_folder[0]['path'] + '/' + apple_night_folder[0]['night'] + '/'+ 'epoch_time.csv')
        fitbit_lables = pd.read_csv(fitbit_night_folder[0]['path'] + '/' + fitbit_night_folder[0]['night'] + '/'+ 'stage_prediction.csv')
        fitbit_epoch = pd.read_csv(fitbit_night_folder[0]['path'] + '/' + fitbit_night_folder[0]['night'] + '/'+ 'epoch_time.csv')
        user_dict_apple ={}
        user_dict_fitbit ={}
        user_dict_apple[selected_user]= [pd.DataFrame({'time': psg_epoch['time'].values,'stage':psg_lables['labels'].values}), 
                            pd.DataFrame({'time': apple_epoch['time'].values,'stage':apple_lables['labels'].values})]
        user_dict_fitbit[selected_user]= [pd.DataFrame({'time': psg_epoch['time'].values,'stage':psg_lables['labels'].values}), 
                            pd.DataFrame({'time': fitbit_epoch['time'].values,'stage':fitbit_lables['labels'].values})]
                            
        result_apple_intersection, result_apple_union = main (user_dict_apple)
        
        result_apple_intersection.drop('Device', axis=1, inplace=True)
        result_apple_intersection = result_apple_intersection.fillna("NaN")
        result_apple_intersection = result_apple_intersection.set_index('Stage').transpose()

        result_apple_union.drop('Device', axis=1, inplace=True)
        result_apple_union = result_apple_union.fillna("NaN")
        result_apple_union = result_apple_union.set_index('Stage').transpose()

        result_fitbit_intersection , result_fitbit_union = main (user_dict_fitbit)

        result_fitbit_intersection.drop('Device', axis=1, inplace=True)
        result_fitbit_intersection = result_fitbit_intersection.fillna("NaN")
        result_fitbit_intersection = result_fitbit_intersection.set_index('Stage').transpose()

        result_fitbit_union.drop('Device', axis=1, inplace=True)
        result_fitbit_union = result_fitbit_union.fillna("NaN")
        result_fitbit_union = result_fitbit_union.set_index('Stage').transpose()

        jsonResponse['eval_statics_apple_intersection'] = result_apple_intersection.to_html(classes = 'table table-striped' , justify = 'unset', border =0)
        jsonResponse['eval_statics_apple_union'] = result_apple_union.to_html(classes = 'table table-striped' , justify = 'unset', border =0)

        jsonResponse['eval_statics_fitbit_intersection'] = result_fitbit_intersection.to_html(classes = 'table table-striped' , justify = 'unset', border =0)
        jsonResponse['eval_statics_fitbit_union'] = result_fitbit_union.to_html(classes = 'table table-striped' , justify = 'unset', border =0)
        
    except Exception as e :
        print (e)

    jsonResponse['circadian_rhythms_apple_graphJSON'] = json.dumps(generate_circadian_rhythms(apple_night_folder, height_of_subplot=250), cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['circadian_rhythms_fitbit_graphJSON'] = json.dumps(generate_circadian_rhythms(fitbit_night_folder, height_of_subplot=250), cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['circadian_rhythms_psg_graphJSON'] = json.dumps(hypnogram_fig, cls=plotly.utils.PlotlyJSONEncoder)

    apple_metrics_df = pd.read_csv(s3_bucket_name+'apple'+'/'+selected_user+ '/' +apple_folder +'/'+ 'sleep_metrics.csv')
    fitbit_metrics_df = pd.read_csv(s3_bucket_name+'fitbit'+'/'+fitbitID+ '/' +fitbit_folder+'/'+'sleep_metrics.csv')
    psg_metrics_df = pd.read_csv(s3_bucket_name+'psg'+'/'+PSGID+ '/' + 'sleep_metrics.csv')
    apple_sleep_metrics_data = apple_metrics_df.replace(np.nan, 0).to_dict("rows")
    fitbit_sleep_metrics_data = fitbit_metrics_df.replace(np.nan, 0).to_dict("rows")
    psg_sleep_metrics_data = psg_metrics_df.replace(np.nan, 0).to_dict("rows")

    jsonResponse['apple_sleep_metrics_data']  = apple_sleep_metrics_data
    jsonResponse['fitbit_sleep_metrics_data']  = fitbit_sleep_metrics_data
    jsonResponse['psg_sleep_metrics_data']  = psg_sleep_metrics_data

    jsonResponse['user_details'] = get_user_details(selected_user)
    jsonResponse['user_que_ans'] = get_user_que_ans(selected_user)

    return jsonify(jsonResponse)

@application.route('/pre_val2_group_data')
@login_required
def pre_val2_data():
    selected_device = request.args.get('selected_device')
    selected_cohort = request.args.get('selected_cohort')
    selected_age = request.args.get('selected_age')
    selected_gender = request.args.get('selected_gender')

    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')
    
    df['age'] = df.apply(lambda row: get_user_age(row), axis=1)
    df['gender'] = df.apply(lambda row: get_user_gender(row), axis=1)
   
    if selected_cohort and selected_cohort != '0' :
        df = df[df['Cohort'] == selected_cohort] 
    if selected_age and selected_age not in ['0', 'all']:
        age_range = selected_age.split('-')
        df = df[ df['age'].isnull() | (df['age'] >= float(age_range[0])) & (df['age'] <= float(age_range[1]))]
    if selected_gender and selected_gender !='0':
        df = df[df['gender'] == selected_gender] 

    dataframe = pd.read_excel(users_tat2_table_data, sheet_name='Sheet1',engine='openpyxl',usecols=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])

    users_dict = df.to_dict('records')
    individual_users_diff = {}
    for user in users_dict:

        try:
            if selected_device == 'Apple':
                sleep_df = dataframe[(dataframe['UserID'] == user['ID']) & (dataframe['SleepDiary'] == 'Correct') & (~dataframe['AppleIssue'].isin(['No Data','App Failure']))] 
                multi_day_df = pd.read_csv(s3_bucket_name+'apple'+'/'+user['ID'] +  '/multi_day.csv')
            else:
                sleep_df = dataframe[(dataframe['UserID'] == user['ID']) & (dataframe['SleepDiary'] == 'Correct') & (~dataframe['FitbitIssue'].isin(['No Data','App Failure']))] 
                multi_day_df = pd.read_csv(s3_bucket_name+'fitbit'+'/'+user['FitbitID'] +  '/multi_day.csv')
            sleep_df['date'] = sleep_df.apply(lambda x : x['Date'].date() ,axis=1)

            diff_in_total = difference_in_sleep_diary_and_algorithm(sleep_df,multi_day_df )
            individual_users_diff[user['ID']] = diff_in_total['Total']

        except Exception as e :
            print (e)
            
    diff = get_statics_of_diff_in_sleep_diary_and_algorithm(individual_users_diff)
    return jsonify(json.dumps(diff))


@application.route('/pre_val2_individual_data')
@login_required
def pre_val2_individual_data():  
    selected_user = request.args.get('selected_user')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')
    user_row = df.loc[df['ID'] == selected_user]
    fitbitID = user_row['FitbitID'].values[0]

    jsonResponse={}

    def get_date(row):
        date = parse(row['SleepOffset'])
        if date.hour <12 :
            return date.date() + datetime.timedelta(days=-1)
        return date.date() 
    
    apple_night_folders = get_night_folders_tab2(selected_user,'apple',start_date,end_date)
    
    apple_multi_day_df = pd.read_csv(s3_bucket_name+'apple'+'/'+ selected_user +  '/multi_day.csv')
    apple_multi_day_df['date'] = apple_multi_day_df.apply(lambda row: parse(row['DateTime']).date(), axis=1)
    apple_algorithm_df = apple_multi_day_df[(apple_multi_day_df['date']>=parse(start_date).date()) & (apple_multi_day_df['date']<=parse(end_date).date())] 
    if not apple_algorithm_df.empty:
        apple_algorithm_df['date_on_x'] = apple_algorithm_df.apply(lambda row: get_date(row), axis=1)

    fitbit_night_folders = get_night_folders_tab2(fitbitID,'fitbit',start_date,end_date)
    fitbit_multi_day_df = pd.read_csv(s3_bucket_name+'fitbit'+'/'+ fitbitID +  '/multi_day.csv')
    fitbit_multi_day_df['date'] = fitbit_multi_day_df.apply(lambda row: parse(row['DateTime']).date(), axis=1)
    fitbit_algorithm_df = fitbit_multi_day_df[(fitbit_multi_day_df['date']>=parse(start_date).date()) & (fitbit_multi_day_df['date']<=parse(end_date).date())] 
    if not fitbit_algorithm_df.empty:    
        fitbit_algorithm_df['date_on_x'] = fitbit_algorithm_df.apply(lambda row: get_date(row), axis=1)

    # get timezone from any recording folder name, apple or fitbit
    recd_folder = apple_night_folders[0]['night'] if apple_night_folders  else fitbit_night_folders[0]['night']
    time_zone = int(recd_folder[-5] + str(int(recd_folder[-4:-2]) * 3600 + int(recd_folder[-2:]) * 60))

    sleep_data ,kss_data , naps_data = get_sleep_data(selected_user)
    
    
    dataframe = pd.read_excel(users_tat2_table_data, sheet_name='Sheet1',engine='openpyxl',usecols=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])

    try:
        apple_df = dataframe[(dataframe['UserID'] == selected_user) & (dataframe['SleepDiary'] == 'Correct') & (~dataframe['AppleIssue'].isin(['No Data','App Failure']))]
        apple_df['date'] = apple_df.apply(lambda x : x['Date'].date() ,axis=1)
        
        apple_df_within_range = apple_df[(apple_df['date']>=parse(start_date).date()) & (apple_df['date']<=parse(end_date).date())]
       
        apple_diff = difference_in_sleep_diary_and_algorithm(apple_df_within_range,apple_multi_day_df )
        jsonResponse['apple_diff'] =  json.dumps(apple_diff) 
        apple_statics = get_statics_from_multi_day(apple_df_within_range,apple_multi_day_df)
        jsonResponse['apple_statics'] =  apple_statics
    except Exception as e :
        print("EEEEEEEEEEEEE")
        print (e)

    try:
        fitbit_df = dataframe[(dataframe['UserID'] == selected_user) &  (dataframe['SleepDiary'] == 'Correct') & (~dataframe['FitbitIssue'].isin(['No Data','App Failure']))] 
        fitbit_df['date'] = fitbit_df.apply(lambda x : x['Date'].date() ,axis=1)    
        fitbit_df_within_range = fitbit_df[(fitbit_df['date']>=parse(start_date).date()) & (fitbit_df['date']<=parse(end_date).date())]   
        fitbit_diff = difference_in_sleep_diary_and_algorithm(fitbit_df_within_range,fitbit_multi_day_df )
        jsonResponse['fitbit_diff'] = json.dumps(fitbit_diff)
        fitbit_statics = get_statics_from_multi_day(fitbit_df_within_range,fitbit_multi_day_df)
        jsonResponse['fitbit_statics'] =  fitbit_statics 
    except Exception as e :
        pass

    try:
        apple_night_recordings = get_night_recordings_from_folders(apple_night_folders)
        cr_apple =  CircanianRhythms( apple_night_recordings,  sleep_data, kss_data, naps_data, apple_algorithm_df,  time_zone,  150 ).plot()
        jsonResponse['circadian_rhythms_apple_graphJSON'] = json.dumps(cr_apple, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e :
        print (e)

    try:
        fitbit_night_recordings = get_night_recordings_from_folders(fitbit_night_folders)
        cr_fitbit = CircanianRhythms( fitbit_night_recordings, sleep_data, kss_data, naps_data, fitbit_algorithm_df, time_zone,  150 ).plot()
        jsonResponse['circadian_rhythms_fitbit_graphJSON'] = json.dumps(cr_fitbit, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e :
        pass

    return jsonResponse

@application.route('/pre_val3_group_data')
@login_required
def pre_val3_data():
    selected_users = request.args.get('selected_users')
    selected_device = request.args.get('selected_device')
    selected_cohort = request.args.get('selected_cohort')
    selected_age = request.args.get('selected_age')
    selected_gender = request.args.get('selected_gender')
    users = []
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')

    df['age'] = df.apply(lambda row: get_user_age(row), axis=1)
    df['gender'] = df.apply(lambda row: get_user_gender(row), axis=1)
    
    if selected_users:
        df = df[df['ID'].isin(selected_users.split(','))]
    if selected_cohort and selected_cohort != '0' :
        df = df[df['Cohort'] == selected_cohort] 
    if selected_age and selected_age not in ['0', 'all']:
        age_range = selected_age.split('-')
        df = df[ df['age'].isnull() | (df['age'] >= float(age_range[0])) & (df['age'] <= float(age_range[1]))]
    if selected_gender and selected_gender !='0':
        df = df[df['gender'] == selected_gender] 

    print (df)

    users_dict = df.to_dict('records')
    for user in users_dict:
        device_folder = user[selected_device]
        try:
            device_sleep_metrics = download_csv_file(s3_bucket_name + selected_device.lower() + '/' +user[get_device_id(selected_device)]+ '/' + device_folder +  '/sleep_metrics.csv')
            psg_sleep_metrics =    download_csv_file(s3_bucket_name + 'psg/'  + user['PSG'] +  '/sleep_metrics.csv')
            if all((psg_sleep_metrics  is not None, device_sleep_metrics  is not None)):
                
                psg_sleep_metrics= df_efficiency_to_int(psg_sleep_metrics)
                device_sleep_metrics= df_efficiency_to_int(device_sleep_metrics)
                psg_minus_device = np.where(psg_sleep_metrics['Value'] == device_sleep_metrics['Value'], 0, psg_sleep_metrics['Value'] - device_sleep_metrics['Value'])
                user['psg_minus_device_df'] = pd.DataFrame({'Metric': psg_sleep_metrics['Metric'].to_list(),'Value': psg_minus_device,})
                
            users.append(user) 
        except Exception as e:
            print (e)      
    users_df =   [user['psg_minus_device_df']  for user in users if  'psg_minus_device_df' in user]                  
    gruop_by_df= pd.concat(users_df , axis=0).dropna(axis=1).groupby('Metric')
    statics_df = pd.DataFrame({'Metric': gruop_by_df.groups.keys(),
                              'mean': gruop_by_df.mean()['Value'].values,
                              'max': gruop_by_df.max()['Value'].values,
                              'min': gruop_by_df.min()['Value'].values, 
                            })
    statics_dict = statics_df.to_dict('records')
    return jsonify(statics_dict)


@application.route('/pre_val3_individual_data')
@login_required
def pre_val3_individual_data():
    selected_user = request.args.get('selected_user')
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')
    user_row = df.loc[df['ID'] == selected_user]
    fitbitID = user_row['FitbitID'].values[0]
    PSGID = user_row['PSG'].values[0]
    apple_folder = user_row['Apple'].values[0]
    fitbit_folder = user_row['Fitbit'].values[0]  
    apple_metrics_df = pd.read_csv(s3_bucket_name+'apple'+'/'+selected_user+ '/' +apple_folder +'/'+ 'sleep_metrics.csv')
    fitbit_metrics_df = pd.read_csv(s3_bucket_name+'fitbit'+'/'+fitbitID+ '/' +fitbit_folder+'/'+'sleep_metrics.csv')
    psg_metrics_df = pd.read_csv(s3_bucket_name+'psg'+'/'+PSGID+ '/' + 'sleep_metrics.csv')

    apple_metrics_df = df_efficiency_to_int(apple_metrics_df)
    fitbit_metrics_df = df_efficiency_to_int(fitbit_metrics_df)
    psg_metrics_df = df_efficiency_to_int(psg_metrics_df)

    psg_minus_apple = np.where(psg_metrics_df['Value'] == apple_metrics_df['Value'], 0, psg_metrics_df['Value'] - apple_metrics_df['Value'])
    psg_minus_fitbit = np.where(psg_metrics_df['Value'] == fitbit_metrics_df['Value'], 0, psg_metrics_df['Value'] - fitbit_metrics_df['Value'])
    apple_minus_fitbit = np.where(apple_metrics_df['Value'] == fitbit_metrics_df['Value'], 0, apple_metrics_df['Value'] - fitbit_metrics_df['Value'])

    psg_minus_apple_metrics = pd.DataFrame({'Metric': psg_metrics_df['Metric'].to_list(),'Value': psg_minus_apple})
    psg_minus_fitbit_metrics = pd.DataFrame({'Metric': psg_metrics_df['Metric'].to_list(),'Value': psg_minus_fitbit})
    apple_minus_fitbit_metrics = pd.DataFrame({'Metric': psg_metrics_df['Metric'].to_list(),'Value': apple_minus_fitbit})

    print (psg_minus_apple_metrics)

    psg_minus_apple_metrics = psg_minus_apple_metrics.replace(np.nan, 0).to_dict("rows")
    psg_minus_fitbit_metrics = psg_minus_fitbit_metrics.replace(np.nan, 0).to_dict("rows")
    apple_minus_fitbit_metrics = apple_minus_fitbit_metrics.replace(np.nan, 0).to_dict("rows")
    
    jsonResponse =  {}

    jsonResponse['psg_minus_apple_metrics']  = psg_minus_apple_metrics
    jsonResponse['psg_minus_fitbit_metrics']  = psg_minus_fitbit_metrics
    jsonResponse['apple_minus_fitbit_metrics']  = apple_minus_fitbit_metrics

    response = db_table.query(
                IndexName='InvertedIndex',
                KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(selected_user))
        )
    user_details=response['Items'][0]
    jsonResponse['user_details'] = user_details

    return jsonResponse

@application.route('/pre_val4_individual_data')
@login_required
def pre_val4_individual_data():
    selected_user = request.args.get('selected_user')
    df = pd.read_excel(users_data, sheet_name='Sheet1',engine='openpyxl')
    print(df)
    jsonResponse = {}
    user_row = df.loc[df['ID'] == selected_user]
    PSGID = user_row['PSG'].values[0]
    fitbitID = user_row['FitbitID'].values[0]
    apple_folder = user_row['MSLTApple'].values[0]
    fitbit_folder = user_row['MSLTFitbit'].values[0]
    apple_night_folder=[]
    fitbit_night_folder=[]
    apple_night_folder.append({'path':s3_bucket_name+'apple'+'/'+selected_user,'night':apple_folder})
    pre_folder, next_folder = get_pre_next_rec(selected_user,'apple',apple_folder)
    apple_night_folder.append({'path':s3_bucket_name+'apple'+'/'+selected_user,'night':pre_folder})
    apple_night_folder.append({'path':s3_bucket_name+'apple'+'/'+selected_user,'night':next_folder})

    fitbit_night_folder.append({'path':s3_bucket_name+'fitbit'+'/'+fitbitID,'night':fitbit_folder})
    pre_folder, next_folder = get_pre_next_rec(fitbitID,'fitbit',fitbit_folder)
    fitbit_night_folder.append({'path':s3_bucket_name+'fitbit'+'/'+fitbitID,'night':pre_folder})
    fitbit_night_folder.append({'path':s3_bucket_name+'fitbit'+'/'+fitbitID,'night':next_folder})
    

    apple_night_recordings = get_night_recordings_from_folders(apple_night_folder)
    fitbit_night_recordings = get_night_recordings_from_folders(fitbit_night_folder)

    time_zone = int(apple_folder[-5] + str(int(apple_folder[-4:-2]) * 3600 + int(apple_folder[-2:]) * 60))

    mslt_recordings = get_recordings_from_mslt(s3_bucket_name + 'psg/'+PSGID+'/mslt')
    msltHypnogram_fig = MsltHypnogram.plotly_display(mslt_recordings['labels'], mslt_recordings['awakeings'],mslt_recordings['times'],
                 mslt_recordings['hrs'], 3 ,int(time_zone))
    
    jsonResponse['mslt_psg_graphJSON'] = json.dumps(msltHypnogram_fig, cls=plotly.utils.PlotlyJSONEncoder)

    cr_apple =  MsltCircanianRhythms( apple_night_recordings,  time_zone,  250 ).plot()
    cr_fitbit = MsltCircanianRhythms( fitbit_night_recordings, time_zone,  250 ).plot()

    jsonResponse['circadian_rhythms_apple_graphJSON'] = json.dumps(cr_apple, cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['circadian_rhythms_fitbit_graphJSON'] = json.dumps(cr_fitbit, cls=plotly.utils.PlotlyJSONEncoder)
    
    mslt_sleep_metrics=  mslt_recordings['sleep_metrics']
    mslt_sleep_metrics_list = {}
    
    all_tst = []
    all_tib = [] 
    all_sleep_l = []
    all_rem_l = []
    for idx , sleep_metric in enumerate(mslt_sleep_metrics) :
        try:
           
          filtered_Df = sleep_metric[sleep_metric['Metric'].isin(['TST','TIB','Sleep Latency','REM Latency'])]
          filtered_Df = filtered_Df.fillna(0)
          all_tst.append( float(filtered_Df[filtered_Df['Metric']=='TST']['Value'].values[0]) )
          all_tib.append(float(filtered_Df[filtered_Df['Metric']=='TIB']['Value'].values[0]) )
          all_sleep_l.append(float(filtered_Df[filtered_Df['Metric']=='Sleep Latency']['Value'].values[0]) )
          all_rem_l.append(float(filtered_Df[filtered_Df['Metric']=='REM Latency']['Value'].values[0]) )
          mslt_sleep_metrics_list['Nap {}'.format(idx)] = filtered_Df.to_dict('records')
        except Exception as e :
            pass
          
    mslt_sleep_metrics_list['mean']= [{'Metric': 'TST', 'Value': round(np.mean(all_tst),2)}, {'Metric': 'TIB', 'Value': round(np.mean(all_tib),2) }, 
                            {'Metric': 'Sleep Latency', 'Value':round(np.mean(all_sleep_l),2)}, {'Metric': 'REM Latency', 'Value': round(np.mean(all_rem_l),2)}]
    jsonResponse['mslt_sleep_metrics_list']  =mslt_sleep_metrics_list  

    try:
        apple_sleep_metrics_list = {}
        apple_multi_day= pd.read_csv(apple_night_folder[0]['path'] +  '/multi_day.csv')
        apple_multi_day['date'] = apple_multi_day.apply(lambda row : parse(row['DateTime']).date(),axis=1)
        apple_df = apple_multi_day[apple_multi_day['date'] == parse(apple_folder).date()]
        
        apple_df['midnight'] = apple_df.apply(lambda row : datetime.datetime.combine(row['date'], datetime.datetime.min.time()), axis=1) 
        apple_df['seven_am'] = apple_df['midnight'] + datetime.timedelta(hours=7)
        apple_df['seven_pm'] = apple_df['midnight'] + datetime.timedelta(hours=19)
        apple_df['bedtime'] = apple_df.apply(lambda row : parse(row['BedTime']),axis=1)
        
        apple_df = apple_df[(apple_df['bedtime']>= apple_df['seven_am']) & (apple_df['bedtime'] <= apple_df['seven_pm']) ]
        apple_df_dict_list = apple_df.to_dict('records')
        
        for idx , sleep_metric in enumerate(apple_df_dict_list) :
            apple_sleep_metrics_list['Nap {}'.format(idx)] = []
            apple_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "TST", 'Value': sleep_metric['TST']})
            apple_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "TIB", 'Value': sleep_metric['TIB']})
            apple_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "Sleep Latency", 'Value': sleep_metric['Sleep Latency']})
            apple_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "REM Latency", 'Value': sleep_metric['REM Latency']})

        jsonResponse['apple_sleep_metrics_list']  =apple_sleep_metrics_list    

    except Exception as e :
        pass

    try:
        fitbit_sleep_metrics_list = {}
        fitbit_multi_day= pd.read_csv(fitbit_night_folder[0]['path'] +  '/multi_day.csv')
        fitbit_multi_day['date'] = fitbit_multi_day.apply(lambda row : parse(row['DateTime']).date(),axis=1)
        fitbit_df = fitbit_multi_day[fitbit_multi_day['date'] == parse(apple_folder).date()]

        fitbit_df['midnight'] = fitbit_df.apply(lambda row : datetime.datetime.combine(row['date'], datetime.datetime.min.time()), axis=1) 
        fitbit_df['seven_am'] = fitbit_df['midnight'] + datetime.timedelta(hours=7)
        fitbit_df['seven_pm'] = fitbit_df['midnight'] + datetime.timedelta(hours=19)
        fitbit_df['bedtime'] = fitbit_df.apply(lambda row : parse(row['BedTime']),axis=1)
        
        fitbit_df = fitbit_df[(fitbit_df['bedtime']>= fitbit_df['seven_am']) & (fitbit_df['bedtime'] <= fitbit_df['seven_pm']) ]
        fitbit_df_dict_list = fitbit_df.to_dict('records')

        for idx , sleep_metric in enumerate(fitbit_df_dict_list) :
            fitbit_sleep_metrics_list['Nap {}'.format(idx)] = []
            fitbit_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "TST", 'Value': sleep_metric['TST']})
            fitbit_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "TIB", 'Value': sleep_metric['TIB']})
            fitbit_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "Sleep Latency", 'Value': sleep_metric['Sleep Latency']})
            fitbit_sleep_metrics_list['Nap {}'.format(idx)].append({'Metric': "REM Latency", 'Value': sleep_metric['REM Latency']})

        jsonResponse['fitbit_sleep_metrics_list']  =fitbit_sleep_metrics_list  

    except Exception as e :
        print (e)
    
    return jsonify(jsonResponse)

