import requests
import re
import json
import logging
from typing import List
import random
from datetime import datetime
pattern = re.compile(r"[a-z\s]+")


exec_time = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(level=logging.INFO,
                    filename= "logs/{}.log".format(exec_time),
                    filemode="w",
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
                    )
logger = logging.getLogger(__name__)


def log_error(error, message, used_proxy, logger=logger):
    logger.error(f"{error}: {message} - {used_proxy}")


class Annotator:
    def __init__(self, posts_queue, response_queue):
        self.url = "https://www.llama2.ai/api"
        self.posts_queue = posts_queue
        self.response_queue = response_queue
        self.valide_answers = ["with palestine", "with israel", "neutral", "indifferent", "inquisitive"]
        self.annotation_prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>" \
            "\nYou are a helpful assistant.<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\n\npost: {}," \
            "\n comment: {} "\
            "\n based on the given post and comment,pick just one answer from the list below, the comment is :" \
            " [with palestine, with israel, neutral, indifferent, inquisitive], important!!! you're answer should be the smallest in" \
            " terms of verbosity <|eot_id|>\n"
        )
        self.validation_prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>" \
            "\nYou are a helpful assistant.<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\n\n" \
            "a person was asked to highlight a comment on a reddit post by choosing one word from this list" \
            " [with palestine, with israel, neutral, indifferent, inquisitive]" \
            "his answer was unfortunately wrong because he didn't respect the condition saying" \
            " that the answer should be chosen from the given list, this was his answer <<{}>>, the post was {}" \
            "and the comment was {} correct the answer of this person by choosing one response from the given list." \
            "\nimportant!!!! give me just the correct answer in the minimum verbosity.<|eot_id|>\n"
        )
        self.proxies = open("valid_proxies/proxies.txt").read().split("\n")

    def ask_llama3(self, prompt: str) -> str:
        payload = json.dumps({
                    "prompt": prompt,
                    "model": "meta/meta-llama-3-70b-instruct",
                    "systemPrompt": "You are a helpful assistant.",
                    "temperature": 0.75,
                    "topP": 0.9,
                    "maxTokens": 800,
                    "image": None,
                    "audio": None
                    }
                )
        headers = {
        'Content-Type': 'text/plain'
        }
        while(self.proxies):
            proxy = random.choice(self.proxies)
            try:
                response = requests.request(
                    "POST", self.url,
                    proxies={'http': f"http://{proxy}="},
                    headers=headers, data=payload
                )
            except Exception as e:
                log_error(e, "Error in asking llama3",  f"used proxy: {proxy}")
                self.proxies.remove(proxy)
                continue
            if response.status_code != 200:
                log_error(
                    "Status code: " + response.status_code,
                    "Error in asking llama3",
                    f"used proxy: {proxy}"
                )
                self.proxies.remove(proxy)
                continue
            break
        if not self.proxies:
            raise Exception("No more proxies!!")
        return response.text
    
    def annotate(self, post: dict, comment: dict) -> str:
        prompt = self.annotation_prompt.format(post, comment)
        response = self.ask_llama3(prompt)
        lower_response = response.lower()
        return pattern.search(lower_response).group()
    
    def validate(self, response: str, post: dict, comment: dict) -> str:
        prompt = self.validation_prompt.format(response, post, comment)
        response = self.ask_llama3(prompt)
        lower_response = response.lower()
        return pattern.search(lower_response).group()
    
    def __call__(self) -> str:
        while(True):
            try:
                post = self.posts_queue.get(timeout=1)
            except:
                return None
            post_wc = {k:v for k,v in post.items() if k != "comments"}
            for comment in post["comments"]:
                logger.info(f"Annotating comment whose the id is {comment['id']}") 
                response = self.annotate(post_wc, comment)
                if response and response not in self.valide_answers:
                    logger.info(f"Validating response: {response}")
                    response = self.validate(response, post_wc, comment)
                comment["label"] = response
            self.response_queue.put(post)
