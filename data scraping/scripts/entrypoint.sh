sudo apt-get update
python3 -m pip install --upgrade pip
pip install -r /app/requirements.txt
sleep 10
python /app/utils/create_kafka_topics.py
python /app/main.py comments