from utils.annotator import Annotator
from utils.scraper import RedditAPI
import json
import queue
import concurrent.futures
import logging
from datetime import datetime
from tqdm import tqdm


exec_time = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(level=logging.INFO,
                    filename= "logs/{}.log".format(exec_time),
                    filemode="w",
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
                    )
logger = logging.getLogger(__name__)


israel_keywords = ['israel', 'israeli', 'zionist', 'zionism']
palestine_keywords = ['palestine', 'palestinian', 'gaza', 'hamas']
keywords = israel_keywords + palestine_keywords
keywords.append("israel palestine")
sorts = ["relevance", "top"]

def main():
    reddit = RedditAPI(limit=1)
    response_queue = queue.Queue()
    posts_queue = reddit(keywords, sorts)
    # Annotate data using Llama3
    logger.info("Annotating {} posts using Llama3...".format(posts_queue.qsize()))
    annotator = Annotator(posts_queue, response_queue)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range(25):
            executor.submit(annotator)
    json.dump(list(response_queue.queue), open("scraped_data/israel-palestine.json", "w"), indent=4)


if __name__ == "__main__":
    main()
