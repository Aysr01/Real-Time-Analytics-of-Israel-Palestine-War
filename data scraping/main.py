import sys
from utils.stream_data import StreamData
import yaml
import logging

logging.basicConfig(level=logging.INFO
                    , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    topics = {
        "comments": "reddit_comments",
        "posts": "reddit_posts"
    }
    # Load the subreddits from the config file
    with open("/app/config.yaml", "r") as file:
        subreddits = yaml.safe_load(file)["subreddits"]
    # Get the data type
    data_type = sys.argv[1]
    print(data_type)
    if data_type in {"comments", "posts"}:
        # Instantiate StreamData class
        data_stream = StreamData("kafka:9092", topics[data_type])
        # Stream the data
        data_stream(data_type, subreddits)
    else:
        logger.error("Invalid data type. Choose either 'comments' or 'posts'")

