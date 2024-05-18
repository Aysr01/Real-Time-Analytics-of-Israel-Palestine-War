#!/bin/bash
apt-get update
pip install --upgrade pip
cd model_endpoint
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 get_predictions:app