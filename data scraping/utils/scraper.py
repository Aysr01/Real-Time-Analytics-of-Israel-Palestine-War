from typing import Dict, List
import praw
import os
import logging
from tqdm import tqdm
import queue
from datetime import datetime

exec_time = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(level=logging.INFO,
                    filename= "logs/{}.log".format(exec_time),
                    filemode="w",
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
                    )
logger = logging.getLogger(__name__)


class RedditAPI:

    def __init__(self, limit):
        client_id = os.environ.get('CLIENT_ID')
        client_secret = os.environ.get('CLIENT_SECRET')
        user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
        username = os.environ.get('REDDIT_USERNAME')
        password = os.environ.get('REDDIT_PASSWORD')
        self.limit = limit
        self.reddit = praw.Reddit(client_id=client_id,
                            client_secret=client_secret,
                            user_agent=user_agent,
                            username=username,
                            password=password)


    def fetch_posts(self, search_query: str, sort: str) -> praw.models.Submission:
        posts = self.reddit.subreddit('all').search(search_query, sort=sort, time_filter="year", limit=self.limit)
        return posts

    def remove_redundancy(self, posts):
        posts_dict = {}
        for post in posts:
            posts_dict[post.id] = post
        return list(posts_dict.values())
        
    def extract_data(self, posts):
        i = 0
        desired_data = []
        for post in tqdm(posts):
            i += 1
            try:
                preview = post.preview["images"][0]["source"]["url"]
            except:
                preview = None
            post_data = {
                "url": post.url,
                "id": post.id,
                "timestamp": post.created_utc,
                "title": post.title,
                "text": post.selftext,
                "num_comments": post.num_comments,
                "upvotes": post.ups,
                "upvote_ratio": post.upvote_ratio,
                "subreddit": post.subreddit_name_prefixed,
                "class": post.link_flair_css_class,
                "preview": preview,
                "comments": []
            }
            #fetch Top 10 comments in terms of score
            post.comments.replace_more(limit=0)
            comments_list = [comment for comment in post.comments.list() if comment.depth==0]
            comments = sorted(comments_list, key=lambda c: c.score, reverse=True)
            n = len(comments)
            for comment in comments[:min(10, n)]:
                comment_data = {
                    "timestamp": comment.created_utc,
                    "id": comment.id,
                    "ups": comment.score,
                    "text": comment.body,
                }
                post_data["comments"].append(comment_data)
            logger.info("Extracted data from post number {}".format(i))
            desired_data.append(post_data)
        return desired_data
        
    def __call__(self, keywords: List[str], sorts: List[str]) -> List[Dict]:
        posts_queue = queue.Queue()
        posts_list = []
        for sort in sorts:
            logger.info("Extracting posts using the sort: {}".format(sort))
            for keyword in tqdm(keywords):
                posts = self.fetch_posts(keyword, sort)
                for post in posts:
                    posts_list.append(post)
        # removing redundancy
        logger.info("Removing redundancy...")
        unique_posts = self.remove_redundancy(posts_list)
        # Extracting useful posts info
        logger.info("Extracting Info from {} posts".format(len(unique_posts)))
        desired_data = self.extract_data(unique_posts)
        # adding posts to the queue
        for post in desired_data:
            posts_queue.put(post)
        return posts_queue
        