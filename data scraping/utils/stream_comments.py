import praw
from typing import List, Dict
from kafka import KafkaProducer
import json
import os
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Install NLTK data
nltk.download('punkt')
nltk.download('stopwords')


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
                    )
logger = logging.getLogger(__name__)


class StreamData:
    def __init__(self, bootstrap_server: str, topic: str):
        client_id = os.environ.get('CLIENT_ID')
        client_secret = os.environ.get('CLIENT_SECRET')
        user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
        username = os.environ.get('REDDIT_USERNAME')
        password = os.environ.get('REDDIT_PASSWORD')
        self.reddit = praw.Reddit(client_id=client_id,
                            client_secret=client_secret,
                            user_agent=user_agent,
                            username=username,
                            password=password)
        self.bootstrap_server = bootstrap_server
        self.topic = topic
        if bootstrap_server:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_server,
                value_serializer=lambda x: x.encode('utf-8')
                )
        self.keywords = [
            "israel", "palestine", "hamas", "ghaza",
            "jerusalem", "zionist", "zionism", "palestinian",
            "israeli", "al-aqsa", 
        ]
        
    def is_conflict(self, text: str) -> bool:
        stop_words = set(stopwords.words('english'))
        word_tokens = word_tokenize(text)
        filtered_text = [word for word in word_tokens if word.lower() not in stop_words]
        stemmer = PorterStemmer()
        stemmed_text = [stemmer.stem(word) for word in filtered_text]
        for keyword in self.keywords:
            if keyword in stemmed_text:
                return True
        return False
    
    def retrieve_parent_content(self, id: str):
        if id.startswith("t1"):
            parent = self.reddit.comment(id)
            return parent.body
        else:
            return None
        
        
    def stream_comments(self, subreddits: List[str]):
        subreddits = "+".join(subreddits)
        comments = self.reddit.subreddit(subreddits).stream.comments()
        for comment in comments:
            try:
                comment_data = {
                    "timestamp": comment.created_utc,
                    "id": comment.id,
                    "body": comment.body,
                    "author": comment.author.name,
                    "subreddit_id": comment.subreddit_id,
                    "subreddit": comment.subreddit.display_name,
                    "ups": comment.ups,
                    "parent_content": self.retrieve_parent_content(comment.parent_id),
                    "submission_title": comment.submission.title,
                    "submission_text": comment.submission.selftext,
                }
            except Exception as e:
                logger.error("{}: Failed to extract data from the following comment: {}".format(e, comment.id))
            else:
                if self.is_conflict(
                    comment.submission.title + " " + comment.submission.selftext
                    ):
                    comment_json = json.dumps(comment_data)
                    self.producer.send(self.topic, value=comment_json)
                    self.producer.flush()
                    logger.info("Comment {} from {} streamed to Kafka topic {}" \
                                .format(comment.id, comment.subreddit, self.topic))

    def stream_submissions(self, subreddits: List[str]):
        subreddits = "+".join(subreddits)
        submissions = self.reddit.subreddit(subreddits).stream.submissions()
        for submission in submissions:
            try:
                preview = submission.preview["images"][0]["source"]["url"]
            except:
                preview = None
            submission_data = {
                "timestamp": submission.created_utc,
                "id": submission.id,
                "title": submission.title,
                "text": submission.selftext,
                "author": submission.author.name,
                "subreddit_id": submission.subreddit_id,
                "subreddit": submission.subreddit.display_name,
                "ups": submission.ups,
                "num_comments": submission.num_comments,
                "upvote_ratio": submission.upvote_ratio,
                "preview": preview
            }
            submission_json = json.dumps(submission_data)
            self.producer.send(self.topic, value=submission_json)
            self.producer.flush()
            logger.info("Submission {} streamed to Kafka topic {}".format(submission.id, self.topic))

    def __call__(self, data_type: str, subreddits: List[str]):
        try:
            if data_type == "comments":
                self.stream_comments(subreddits)
            elif data_type == "submissions":
                self.stream_submissions(subreddits)
            else:
                logger.error("Invalid data type. Choose between 'comments' and 'submissions'")
        except Exception as e:
            logger.error("An error occurred: {}".format(str(e)))
