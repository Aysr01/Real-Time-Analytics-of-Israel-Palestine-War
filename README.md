# Real Time Analytics of Israeli-Palestinian War
This project aims to perform real-time analysis of the Israeli-Palestinian conflict by processing social media data from Reddit. It utilizes a distributed architecture with Apache Kafka for data ingestion and streaming, Apache Spark for data processing, and Cassandra for storage. The data pipeline includes natural language processing with BERT for annotation and sentiment analysis. The processed insights are then visualized using Power BI and Jupyter notebooks to gain an understanding of the ongoing conflict based on real-time discussions on Reddit.
![final_project_schema_copy](https://github.com/Aysr01/Real-Time-Analytics-of-Israel-Palestine-War/assets/114707989/2db2af4b-87fb-4a49-aa17-a7b25f0297cc)

## Project Configuration
Before running this pipeline, you should adjust it to your needs.

- In the [configuration](./data%20scraping/config.yaml) file, you should specify the subreddit names from which you desire to stream comments (redditor opinions), or you can simply write "all" to stream comments from all subreddits. However, this can be computationally expensive.
- In the [docker-compose](./docker-compose.yml) file, and specifically in the "scraping_app" container, add your Reddit credentials to retrieve data from Reddit.

## Run Project
After the configuration of the pipeline, you would be able to run the pipeline, to do so, you have to run docker-compose file using the following command:

1- `$ docker-compose up`

If you notice that the scraping container has started publishing comments to Kafka and the model endpoint is running, you can run the Spark job by writing the following commands:

**in the first run**

2- `$ docker exec -it spark-worker1 pip install requests`

3- `$ docker exec -it spark-worker2 pip install requests`

**start the job**

4- `$ docker exec -it spark-master /bin/bash utils/start-job.sh`

## LLM Model
To classify opinions into three categories (with Palestine, with Israel, neutral), we used a fine-tuned **Google BERT** language model on the [Redditors Opinion on Israel-Palestine War](https://www.kaggle.com/datasets/ayoubsarab/redditors-opinion-on-israel-palestine-war) dataset, collected by our team and uploaded to **Kaggle** for general use.

### Confusion Matrix

| True Labels / Predicted Labels | neutral | with palestine | with israel |
|--------------------------------|---------|----------------|-------------|
| neutral                        | 622     | 90             | 139         |
| with palestine                 | 76      | 622            | 182         |
| with israel                    | 87      | 140            | 674         |

### Model Evaluation

|                  | precision | recall | f1-score | support |
|------------------|-----------|--------|----------|---------|
| neutral          | 0.79      | 0.73   | 0.76     | 851     |
| with palestine   | 0.73      | 0.71   | 0.72     | 880     |
| with israel      | 0.68      | 0.75   | 0.71     | 901     |
|                  |           |        |          |         |
| accuracy         |           |        | 0.73     | 2632    |
| macro avg        | 0.73      | 0.73   | 0.73     | 2632    |
| weighted avg     | 0.73      | 0.73   | 0.73     | 2632    |

## DashBoard

![Israelo-Palestine-conflict_page-0001](https://github.com/Aysr01/Real-Time-Analytics-of-Israel-Palestine-War/assets/114707989/b7ce1d87-c910-4d1e-90fb-81e5fa006613)

The dashboard provides insights into comments related to the Israel-Palestine issue over an 18-hour period. It shows a total of 2071 comments, with the majority coming from the "IsraelPalestine" subreddit. Opinions are categorized as "with palestine," "with israel," and "neutral." The "with palestine" opinion has the highest number of comments, followed by "with israel" and then "neutral." The cumulative comment count graph indicates a steady increase in comments for all opinions, with "with palestine" consistently leading. This suggests a high level of engagement and a significant leaning towards the "with palestine" opinion in the discussions.





