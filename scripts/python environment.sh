sudo apt-get update
python3 -m pip install --upgrade pip
pip install -r /app/requirements.txt
sleep 15
python /app/utils/create_kafka_topics.py
python /app/start_stream.py comments