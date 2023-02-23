import sys
import sys
sys.path.append('/mnt/access')
import yaml
from os.path import dirname, abspath
import os

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


with open(os.path.join(dirname(abspath(__file__)), 'config.yaml'), 'r') as r:

    config = yaml.load(r, Loader=Loader)

    windows = [int(x) for x in config['prediction']['window'].split(',')]
    cls_choices = []
    for cls_choice in config['classifier_choice']:
        for name, item in cls_choice.items():
            if item.get('enabled'):
                cls_choices.append(name)

    feature_choices = []
    for feature_choice in config['feature_choice']:
        for name, item in feature_choice.items():
            if item.get('enabled'):
                feature_choices.append(name)

    models_path = config['models_path']
    model_version = config['model_version']
    num_class_choice = config['prediction']['num_class_choice']
    s3_processed_bucket = config['s3_processed_bucket']
    app_env = config['app_env']


class AppConfig(object):
    SECRET_KEY = '50cfb9d889f3be673d41b8452ebaa293'
    DEBUG = False


class DevelopmentConfig(AppConfig):
    DEBUG = True
    APP_ENV = 'dev'
    COGNITO_USER_POOL_ID = 'us-west-2_3nTOtT0JT'
    COGNITO_APP_CLIENT_ID = '57a76e1ic7fscgate9u7mhhrkk'
    S3_DATA_STORE_BUCKET_NAME = 'cernodatastore'
    S3_PROCESSED_BUCKET = 's3://cerno-processed/'
    DYNAMODB_TABLE = "cernousers"
    PROCESS_DATA_TABLE = "ProcessData-Portal"


class ProductionConfig(AppConfig):
    APP_ENV = 'prod'
    COGNITO_USER_POOL_ID = 'us-west-1_Kl9Zxs2jx'
    COGNITO_APP_CLIENT_ID = '4v1qd8p3frdrld52693f1nq6hq'
    S3_DATA_STORE_BUCKET_NAME = 'cernodatastoreprod'
    S3_PROCESSED_BUCKET = 's3://cerno-processedprod/'
    DYNAMODB_TABLE = "cernousers"
    PROCESS_DATA_TABLE = "ProcessData-Portal"


app_config = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
}