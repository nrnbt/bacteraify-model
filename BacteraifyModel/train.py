import os
import pandas as pd
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import to_categorical
import tensorflow as tf

from joblib import load
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from BacteraifyModel.const import CNN_MODEL_FILE_PATH, SVM_MODEL_FILE_PATH
import json
from .load import fetch_file_from_s3
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

def train_pre_trained_model_cnn(new_data_x):
    scaler = MinMaxScaler()
    new_data_x = scaler.fit_transform(new_data_x)
    new_data_x = new_data_x.reshape(new_data_x.shape[0], new_data_x.shape[1], 1)

    cnn_model_to_save_pre_version = load_model(CNN_MODEL_FILE_PATH)
    cnn_model = load_model(CNN_MODEL_FILE_PATH)

    pseudo_labels = cnn_model.predict(new_data_x)
    pseudo_labels_classes = np.argmax(pseudo_labels, axis=1)
    pseudo_labels_encoded = to_categorical(pseudo_labels_classes, num_classes=30)

    for layer in cnn_model.layers[:-3]:  # Freeze all layers except the last few layers
        layer.trainable = False

    cnn_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy', tf.keras.metrics.Recall()])
    cnn_model.fit(new_data_x, pseudo_labels_encoded, epochs=10, batch_size=10, validation_split=0.2)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_filename = f'cnn_last_updated_model_{timestamp}.h5'
    MODELS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'old', model_filename)
    cnn_model_to_save_pre_version.save(MODELS_PATH)

    cnn_model.save(CNN_MODEL_FILE_PATH)

    return

@csrf_exempt
def train_model(request):
    try:
        try:
            body_data = json.loads(request.body)
            file_names = body_data.get('file_names')

            combined_df = pd.DataFrame()
            for files in file_names:
                survey_file = fetch_file_from_s3(files)
                df = pd.read_csv(survey_file)
                combined_df = pd.concat([combined_df, df], ignore_index=True)

            print('survey_data_frames --------------------------\n', combined_df)
            train_pre_trained_model_cnn(combined_df)
            print('traiiiined --------------------------\n', file_names)
            return JsonResponse({ 'trained_files': file_names })
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)}, status=400)
