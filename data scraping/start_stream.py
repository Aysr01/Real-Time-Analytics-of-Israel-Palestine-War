import sys
from utils.stream_data import StreamData

if __name__ == '__main__':
    topics = {
        "comments": "reddit_comments",
        "posts": "reddit_posts"
    }
    subreddits = ["IsraelPalestine", "worldnews"]
    # Get the data type
    data_type = sys.argv[1]
    print(data_type)
    assert data_type in {"comments", "posts"}
    # Instantiate StreamData class
    data_stream = StreamData("kafka:9092", topics[data_type])
    data_stream(data_type, subreddits)

