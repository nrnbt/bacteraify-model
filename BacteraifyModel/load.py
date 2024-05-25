import os
import pandas as pd
from tensorflow.keras.models import load_model
import tensorflow as tf

from joblib import load
import logging
from django.http import JsonResponse

import boto3
from BacteraifyModel.const import CNN_MODEL_FILE_PATH, SVM_MODEL_FILE_PATH
from botocore.exceptions import NoCredentialsError
import hashlib 
from datetime import datetime
import io
from django.views.decorators.csrf import csrf_exempt
import json

logger = logging.getLogger(__name__)

def fetch_file_from_s3(file_key):
    try:
        aws_access_key_id=os.environ.get('S3_SURVEY_ACCESS_KEY_ID')
        aws_secret_access_key=os.environ.get('S3_SURVEY_SECRET_KEY_ID')
        aws_bucket_name=os.environ.get('S3_SURVEY_BUCKET_NAME')
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        response = s3_client.get_object(Bucket=aws_bucket_name, Key='uploads/'+file_key)
        file = response['Body'].read()
        buffered_reader = io.BufferedReader(io.BytesIO(file))
        return buffered_reader
    except Exception as e:
        logger.error(f"Error reading file from S3: {e}")
        return None

def save_result_to_s3(data):
    S3_SURVEY_ACCESS_KEY_ID = os.environ.get('S3_SURVEY_ACCESS_KEY_ID')
    S3_SURVEY_SECRET_KEY_ID = os.environ.get('S3_SURVEY_SECRET_KEY_ID')
    S3_SURVEY_BUCKET_NAME = os.environ.get('S3_SURVEY_BUCKET_NAME')

    csv_data = data.to_csv(index=False)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    hashed_timestamp = hashlib.sha256(timestamp.encode()).hexdigest()
    file_name = f"{hashed_timestamp}" + '.csv'

    s3 = boto3.client('s3', aws_access_key_id=S3_SURVEY_ACCESS_KEY_ID, aws_secret_access_key=S3_SURVEY_SECRET_KEY_ID)
    key = 'results/' + file_name
    fo = io.BytesIO(csv_data.encode())

    try:
        s3.upload_fileobj(fo, S3_SURVEY_BUCKET_NAME, key)
        return file_name

    except NoCredentialsError:
        return "AWS credentials not available or incorrect"

def predict(data: pd.DataFrame, model_types: list):
    file_names = {}
    model_types_len = len(model_types)
    for index, char in enumerate(model_types):
        if char == "CNN":
            if hasattr(tf, "executing_eagerly_outside_functions"):
                tf.compat.v1.executing_eagerly_outside_functions = (tf.executing_eagerly_outside_functions)
                del tf.executing_eagerly_outside_functions
            path = CNN_MODEL_FILE_PATH
            model = load_model(path)
            logger.info("------------------------------ CNN MODEL ------------------------------")
            logger.info(model)
            y_pred = model.predict(data)
            logger.info("--------------------------- CNN MODEL Y_PRED ---------------------------")
            logger.info(y_pred)

            file_names["CNN"] = save_result_to_s3(pd.DataFrame(y_pred))
        elif char == "SVM":
            path = SVM_MODEL_FILE_PATH
            model = load(path)
            X_test = data.values if isinstance(data, pd.DataFrame) else data
            logger.info("------------------------------ SVM MODEL ------------------------------")
            logger.info(model)
            y_pred = model.predict(X_test)
            y_pred_probabilities = model.predict_proba(X_test)
            logger.info("--------------------------- SVM MODEL Y_PRED ---------------------------")
            logger.info(y_pred)
            file_names["SVM"] = save_result_to_s3(pd.DataFrame(y_pred_probabilities))
        else:
            logger.warning("Invalid model type")

    return file_names

@csrf_exempt
def load_and_predict(request):
    try:
        try:
            body_data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        model_types = []

        survey_fie_name = body_data.get('survey_file_name')
        CNN = body_data.get('CNN')
        SVM = body_data.get('SVM')
        if CNN:
            model_types.append('CNN')
        if SVM:
            model_types.append('SVM')

        survey_file = fetch_file_from_s3(survey_fie_name)
        df = pd.read_csv(survey_file)
        result = predict(df, model_types)
        return JsonResponse({ 'prediction_result_file_names': result })
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=400)
