import datetime

from flask import request, session, jsonify
from flask.json import JSONEncoder
from flask_login import login_required
import json
import plotly

from src import MyJSONEncoder
from src.libs.func.cognito import *
from src.libs.func.dynamo import full_query
from src.libs.utils import *
from src.libs.charts import *
from utilities.sleep_staging_result import SleepStagingResult, SleepStagingPrediction
from hypnodensity import Hypnodensity
from hypnogram import Hypnogram
import config as config

dynamodb = boto3.resource('dynamodb')
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE'])

s3client = boto3.client('s3')
s3_bucket_name = application.config['S3_PROCESSED_BUCKET']


@application.route("/patient_options")
@login_required
def get_patient_options():
    """
    get user list from cognito
    """
    options = {}
    username = session.get('username', None)
    user = User(username, '', session.get('group', None))
    patient_options = get_patient_list(user)
    patients_option = [
        {"label": patient._data['name'] if 'name' in patient._data else patient._data['preferred_username'],
         "value": patient._data['preferred_username']} for patient in patient_options
    ]
    options['patients_option'] = patients_option
    return jsonify(options)


@application.route("/patient_night_options")
@login_required
def get_patient_night_options():
    """
    get night sleep date list from MultiDay table
    """
    start = datetime.datetime.now()
    process_table = dynamodb.Table(application.config['PROCESS_DATA_TABLE'])
    end = datetime.datetime.now()
    print('loading table: %s' % (end - start))
    selected_patient = request.args.get('selected_patient')
    selected_device = request.args.get('selected_device')
    start = datetime.datetime.now()
    row_data = full_query(process_table, KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                                            Key('SK').begins_with('%s#m#night#' % selected_device))
    end = datetime.datetime.now()
    print('query table: %s' % (end - start))
    dates = []
    start = datetime.datetime.now()
    for data in row_data:
        date = data['SK'].split('#')[-2]
        timezone = data['TIMEZONE']
        dates.append(
            {
                'label': '%s-%s-%s' % (date[:4], date[4:6], date[6:]),
                'value': '%s/%s' % (date, timezone)
            }
        )
    end = datetime.datetime.now()
    print('clean data: %s' % (end - start))
    return jsonify(dates)


@application.route("/get-one-night-summary")
@login_required
def one_night_summary():
    process_table = dynamodb.Table(application.config['PROCESS_DATA_TABLE'])
    selected_patient = request.args.get('selected_patient')
    selected_device = request.args.get('selected_device')
    selected_night = request.args.get('selected_night')
    selected_date = selected_night.split('/')[0]
    time_zone = selected_night.split('/')[1]
    row_data = full_query(
        process_table,
        KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                               Key('SK').begins_with('%s#m#night#%s' % (selected_device, selected_date))
    )
    jsonResponse = {}
    if len(row_data):
        jsonResponse['summary'] = row_data[0]
        time_zone = int(row_data[0]['TIMEZONE'])
        selected_datetime = datetime.datetime.strptime(selected_date, '%Y%m%d').replace(tzinfo=datetime.timezone.utc)
        start_datetime = selected_datetime - datetime.timedelta(hours=12) - datetime.timedelta(seconds=time_zone)
        end_datetime = selected_datetime + datetime.timedelta(hours=12) - datetime.timedelta(seconds=time_zone)
        hr_data = full_query(
            process_table,
            KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                   Key('SK').between('%s#h#%s' % (selected_device, start_datetime.timestamp()), '%s#h#%s' % (selected_device, end_datetime.timestamp()))
        )
        hr_df = pd.DataFrame.from_records(hr_data)
        hr_fig = generate_hr_chart(hr_df, time_zone)
        hrv_fig = generate_hrv_chart(hr_df, time_zone)
        hr_fig_graphJSON = json.dumps(hr_fig, cls=plotly.utils.PlotlyJSONEncoder)
        hrv_fig_graphJSON = json.dumps(hrv_fig, cls=plotly.utils.PlotlyJSONEncoder)

        activity_data = full_query(
            process_table,
            KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                   Key('SK').between('%s#a#%s' % (selected_device, start_datetime.timestamp()), '%s#a#%s' % (selected_device, end_datetime.timestamp()))
        )
        
        activity_df = pd.DataFrame.from_records(activity_data)
        activity_fig = generate_activity_chart(activity_df, time_zone)
        activity_fig_graphJSON = json.dumps(activity_fig, cls=plotly.utils.PlotlyJSONEncoder)

        bed_time = row_data[0]['BedTime']
        out_of_bed_time = row_data[0]['OutOfBedTime']
        bed_time = datetime.datetime.strptime(bed_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=time_zone)
        out_of_bed_time = datetime.datetime.strptime(out_of_bed_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=time_zone)

        staging_data = full_query(
            process_table,
            KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                   Key('SK').between('%s#st#%s' % (selected_device, bed_time.timestamp()), '%s#st#%s' % (selected_device, out_of_bed_time.timestamp()))
        )

        staging_df = pd.DataFrame.from_records(staging_data)
        hypnogram_fig = Hypnogram.plotly_display(staging_df, config.num_class_choice, time_zone, classifier_name='ensemble')
        hypnogram_graphJSON = json.dumps(hypnogram_fig, cls=plotly.utils.PlotlyJSONEncoder)

        hypnodensity_fig = Hypnodensity.display(staging_df, time_zone, row_data[0])
        hypnodensity_graphJSON = json.dumps(hypnodensity_fig, cls=plotly.utils.PlotlyJSONEncoder)

        jsonResponse['hr_fig_graphJSON'] = hr_fig_graphJSON
        jsonResponse['hrv_fig_graphJSON'] = hrv_fig_graphJSON
        jsonResponse['activity_fig_graphJSON'] = activity_fig_graphJSON
        jsonResponse['hypnogram_graphJSON'] = hypnogram_graphJSON
        jsonResponse['hypnodensity_graphJSON'] = hypnodensity_graphJSON
    else:
        jsonResponse['summary'] = None
    application.json_encoder = MyJSONEncoder
    return jsonify(jsonResponse)

@application.route("/get-multiple-night-summary")
@login_required
def multiple_night_summary():
    process_table = dynamodb.Table(application.config['PROCESS_DATA_TABLE'])
    selected_patient = request.args.get('selected_patient')
    selected_device = request.args.get('selected_device')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_date = custom_date_parser(start_date).date()
    end_date = (custom_date_parser(end_date) + datetime.timedelta(days=1)).date()
    multi_day_data = full_query(
        process_table,
        KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                               Key('SK').between('%s#m#night#%s' % (selected_device, start_date.strftime('%Y%m%d')), '%s#m#night#%s' % (selected_device, end_date.strftime('%Y%m%d')))
    )
    jsonResponse = {}
    
    if len(multi_day_data) > 0 :
        multi_day_df = pd.DataFrame.from_records(multi_day_data)
        jsonResponse['multi_night_summary'] = get_multi_night_summary(multi_day_df)

        rhythm_multi_data = {}
        for one_day_data in multi_day_data:
            time_zone = int(one_day_data['TIMEZONE'])
            selected_date = one_day_data['SK'].split('#')[3]
            selected_datetime = datetime.datetime.strptime(selected_date, '%Y%m%d').replace(tzinfo=datetime.timezone.utc)
            start_datetime = selected_datetime - datetime.timedelta(hours=12) - datetime.timedelta(seconds=time_zone)
            end_datetime = selected_datetime + datetime.timedelta(hours=12) - datetime.timedelta(seconds=time_zone)
            hr_data = full_query(
                process_table,
                KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                    Key('SK').between('%s#h#%s' % (selected_device, start_datetime.timestamp()), '%s#h#%s' % (selected_device, end_datetime.timestamp()))
            )
            hr_df = pd.DataFrame.from_records(hr_data)
            
            activity_data = full_query(
                process_table,
                KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                    Key('SK').between('%s#a#%s' % (selected_device, start_datetime.timestamp()), '%s#a#%s' % (selected_device, end_datetime.timestamp()))
            )
            activity_df = pd.DataFrame.from_records(activity_data)
            
            bed_time = one_day_data['BedTime']
            out_of_bed_time = one_day_data['OutOfBedTime']
            bed_time = datetime.datetime.strptime(bed_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=time_zone)
            out_of_bed_time = datetime.datetime.strptime(out_of_bed_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=time_zone)
            staging_data = full_query(
                process_table,
                KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                    Key('SK').between('%s#st#%s' % (selected_device, bed_time.timestamp()), '%s#st#%s' % (selected_device, out_of_bed_time.timestamp()))
            )
            staging_df = pd.DataFrame.from_records(staging_data)

            sleep_data = full_query(
                process_table,
                KeyConditionExpression=Key('PK').eq('U#%s' % selected_patient) &
                                    Key('SK').between('%s#sl#%s' % (selected_device, start_datetime.strftime('%Y%m%d%H%M')), '%s#sl#%s' % (selected_device, end_datetime.strftime('%Y%m%d%H%M')))
            )
            sleep_df = pd.DataFrame.from_records(sleep_data)
            
            rhythm_data = {}
            rhythm_data['hr_df'] = hr_df
            rhythm_data['activity_df'] = activity_df
            rhythm_data['staging_df'] = staging_df
            rhythm_data['sleep_df'] = sleep_df
            rhythm_data['time_zone'] = time_zone
            rhythm_multi_data[selected_date] = rhythm_data

        circadian_rhythms_fig = CircanianRhythms(rhythm_multi_data, time_zone, None).plot()
        jsonResponse['circadian_rhythms_graphJSON'] = json.dumps(circadian_rhythms_fig, cls=plotly.utils.PlotlyJSONEncoder)
        jsonResponse['status'] = True
    else:
        jsonResponse['status'] = False
    
    application.json_encoder = MyJSONEncoder
    return jsonify(jsonResponse)

@application.route("/get_patient_data-old")
@login_required
def get_patient_data_old():
    selected_patient = request.args.get('selected_patient')
    selected_device = request.args.get('selected_device')
    selected_night = request.args.get('selected_night')
    night_string = selected_night.split('/')

    data_options = {
        'fitbit': get_fitbit_data,
        'apple': get_apple_data,
        'uuid': get_uuid_data,
    }

    patient_data = data_options[selected_device](selected_patient, selected_night)
    prediction = patient_data.get('prediction')
    sleep_metrics_df = patient_data.get('sleep_metrics_df')
    stages_duration_df = patient_data.get('stages_duration_df')
    hr = patient_data.get('hr')
    activity = patient_data.get('activity')
    epoch_time = patient_data.get('epoch_time')
    awakeings = patient_data.get('awakeings')
    multi_day_df = patient_data.get('multi_day_df')

    sleep_staging_obj = SleepStagingResult(subject_id=None, true_labels=['' for _ in range(len(prediction))])
    sleep_staging_obj.prediction_dict = {'ensemble': SleepStagingPrediction(
        prediction[['wake_prob', 'rem_prob', 'nrem_prob']].values, prediction['labels'].values)}

    # convert timezone from 5 last characters of night name to seconds. '-0800' --> -28800 seconds
    time_zone = int(night_string[-5] + str(int(night_string[-4:-2]) * 3600 + int(night_string[-2:]) * 60))

    sleep_metrics_columns = [{"name": i, "id": i} for i in sleep_metrics_df.columns]
    sleep_metrics_data = sleep_metrics_df.replace(np.nan, 0).to_dict("rows")

    multiday_row_for_selected_night = next(item for item in multi_day_df if item["DateTime"] == night_string)
    hypnodensity_fig = Hypnodensity.disply(sleep_staging_obj, 'ensemble', epoch_time, time_zone,
                                           multiday_row_for_selected_night)
    hypnogram_fig = Hypnogram.plotly_display(prediction, awakeings, config.num_class_choice,
                                             time_zone,
                                             time=epoch_time,
                                             classifier_name='ensemble')
    pie_stages_duration = generate_chart(stages_duration_df)
    hr_fig = generate_hr_chart(hr, time_zone, epoch_time)
    hrv_fig = generate_hrv_chart(hr, time_zone, epoch_time)
    activity_fig = generate_activity_chart(activity, epoch_time, time_zone)
    # awakeing_fig = generate_awakeing_chart(awakeings,time_zone)

    hypnodensity_graphJSON = json.dumps(hypnodensity_fig, cls=plotly.utils.PlotlyJSONEncoder)
    hypnogram_graphJSON = json.dumps(hypnogram_fig, cls=plotly.utils.PlotlyJSONEncoder)
    pie_stages_duration_graphJSON = json.dumps(pie_stages_duration, cls=plotly.utils.PlotlyJSONEncoder)
    # psg_fig_graphJSON = json.dumps(psg_fig, cls=plotly.utils.PlotlyJSONEncoder)
    hr_fig_graphJSON = json.dumps(hr_fig, cls=plotly.utils.PlotlyJSONEncoder)
    hrv_fig_graphJSON = json.dumps(hrv_fig, cls=plotly.utils.PlotlyJSONEncoder)
    activity_fig_graphJSON = json.dumps(activity_fig, cls=plotly.utils.PlotlyJSONEncoder)
    # awakeing_fig_graphJSON = json.dumps(awakeing_fig, cls=plotly.utils.PlotlyJSONEncoder)

    jsonResponse = {}
    jsonResponse['hypnodensity_graphJSON'] = hypnodensity_graphJSON
    jsonResponse['hypnogram_graphJSON'] = hypnogram_graphJSON
    jsonResponse['pie_stages_duration_graphJSON'] = pie_stages_duration_graphJSON
    jsonResponse['hr_fig_graphJSON'] = hr_fig_graphJSON
    jsonResponse['hrv_fig_graphJSON'] = hrv_fig_graphJSON
    jsonResponse['activity_fig_graphJSON'] = activity_fig_graphJSON
    # jsonResponse['awakeing_fig_graphJSON'] =awakeing_fig_graphJSON

    rec_details = {}
    rec_quality = 'None'
    try:
        row_for_selected_night = next(item for item in multi_day_df if item["DateTime"] == night_string)
        rec_quality = row_for_selected_night['Quality Issues']
        if np.isnan(rec_quality):
            rec_quality = "No quality issue"
        sleep_metrics_data.append({'Metric': 'Bed Time', 'Value': row_for_selected_night['BedTime']})
        sleep_metrics_data.append({'Metric': 'Out of Bed Time', 'Value': row_for_selected_night['OutOfBedTime']})

    except:
        pass

    jsonResponse['sleep_metrics_data'] = json.dumps(sleep_metrics_data)

    rec_details['quality'] = str(rec_quality)
    rec_details['rec_start'] = custom_date_parser(night_string).strftime('%Y-%m-%d %H:%M:%S')
    rec_details['rec_end'] = datetime.datetime.fromtimestamp(epoch_time[-1] + time_zone).strftime('%Y-%m-%d %H:%M:%S')
    jsonResponse['rec_details'] = rec_details

    return jsonify(jsonResponse)


@application.route("/get_patient_narcolepsy_data")
@login_required
def get_patient_narcolepsy_data():
    jsonResponse = {}
    selected_patient = request.args.get('selected_patient')
    selected_device = request.args.get('selected_device')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_date = custom_date_parser(start_date).date()
    end_date = custom_date_parser(end_date).date()

    multi_night_data_options = {
        'fitbit': get_fitbit_narcolepsy_data,
        'apple': get_apple_narcolepsy_data,
        'uuid': get_uuuid_narcolepsy_data,
    }

    multi_nights_data = multi_night_data_options[selected_device](selected_patient, start_date, end_date)
    night_folders = multi_nights_data.get('night_folders')
    nights_data = multi_nights_data.get('nights_data')
    jsonResponse['nacolepsy_graphJSON'] = json.dumps(generate_sleepiness_scale(night_folders, None, selected_patient),
                                                     cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['nacolepsy_naps_graphJSON'] = json.dumps(generate_narcolepsy_naps_chart(nights_data),
                                                          cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['nacolepsy_sleep_graphJSON'] = json.dumps(generate_narcolepsy_sleep_latency_chart(nights_data),
                                                           cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['nacolepsy_rem_graphJSON'] = json.dumps(generate_narcolepsy_rem_latency_chart(nights_data),
                                                         cls=plotly.utils.PlotlyJSONEncoder)

    return jsonify(jsonResponse)


@application.route("/get_patient_multi_night_data")
@login_required
def get_patient_multi_night_data():
    jsonResponse = {}
    selected_patient = request.args.get('selected_patient')
    selected_device = request.args.get('selected_device')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_date = custom_date_parser(start_date).date()
    end_date = custom_date_parser(end_date).date()

    multi_night_data_options = {
        'fitbit': get_fitbit_multi_night_data,
        'apple': get_apple_multi_night_data,
        'uuid': get_uuuid_multi_night_data,
    }

    multi_nights_data = multi_night_data_options[selected_device](selected_patient, start_date, end_date)
    night_folders = multi_nights_data.get('night_folders')
    nights_data = multi_nights_data.get('nights_data')
    profile_json = multi_nights_data.get('profile_json')

    jsonResponse['multi_night_summary'] = multi_nights_data.get('multi_night_summary')
    jsonResponse['circadian_rhythms_graphJSON'] = json.dumps(generate_circadian_rhythms(night_folders),
                                                             cls=plotly.utils.PlotlyJSONEncoder)
    # jsonResponse['multi_night_tst_graphJSON'] = json.dumps(generate_multi_night_tst_chart(nights_data), cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['multi_night_rem_nrem_sleep_graphJSON'] = json.dumps(
        generate_multi_night_rem_nrem_sleep_chart(nights_data), cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['multi_night_tib_tst_graphJSON'] = json.dumps(generate_multi_night_tib_tst_chart(nights_data),
                                                               cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['multi_night_sleep_eff_graphJSON'] = json.dumps(
        generate_multi_night_sleep_efficiency_chart(nights_data), cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['multi_night_aweking_graphJSON'] = json.dumps(generate_multi_night_awekeing_chart(nights_data),
                                                               cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['sleep_trends_fig_graphJSON'] = json.dumps(generate_sleep_trends_chart(nights_data),
                                                            cls=plotly.utils.PlotlyJSONEncoder)
    jsonResponse['hear_rate_avg_fig_graphJSON'] = json.dumps(
        generate_hear_rate_chart(profile_json, start_date, end_date), cls=plotly.utils.PlotlyJSONEncoder)

    return jsonify(jsonResponse)


@application.route("/get_patient_details")
@login_required
def get_patient_details():
    """
    get device data from dynamoDB
    """
    selected_username = request.args.get('username')
    user_details = None

    try:
        response = db_table.query(
            IndexName='InvertedIndex',
            KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(selected_username))
        )
        user_details = response['Items'][0]
        user_details['user_device_options'] = []

        # check fitbitid
        if 'fitbitid' in user_details:
            user_details['user_device_options'].append({'label': 'Fitbit', 'value': 'fitbit'})

        # check cognitouuid
        # response = db_table.scan(FilterExpression=Attr("fitbitid").exists())
        if 'watchuuid' in user_details:
            user_details['user_device_options'].append({'label': 'Cognito UUID', 'value': 'uuid'})

        # check apple
        try:
            response = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix='apple/', Delimiter="/")
            folders = [x['Prefix'].split('/')[1] for x in response['CommonPrefixes']]
            if selected_username in folders:
                user_details['user_device_options'].append({'label': 'Apple', 'value': 'apple'})
        except Exception as e:
            pass
    except Exception as e:
        pass

    return jsonify(user_details)


@application.route("/get_patient_question_ans")
@login_required
def get_patient_question_ans():
    selected_username = request.args.get('username')
    user_que_ans = {
        'cr': [],
        'ins': [],
        'eds': [],
        'sa': []
    }

    try:
        qa_response = db_table.query(
            KeyConditionExpression=Key('PK').eq("USER#{}".format(selected_username)) & Key('SK').begins_with(
                "#COMPLAINT")
        )

        qa_detail = qa_response['Items']
        for qa in qa_detail:
            if 'cr' in qa['SK']:
                user_que_ans['cr'].append(qa)
            if 'ins' in qa['SK']:
                user_que_ans['ins'].append(qa)
            if 'eds' in qa['SK']:
                user_que_ans['eds'].append(qa)
            if 'sa' in qa['SK']:
                user_que_ans['sa'].append(qa)
    except Exception as e:
        pass

    return jsonify(user_que_ans)

