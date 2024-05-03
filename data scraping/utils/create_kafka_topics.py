from kafka.admin import KafkaAdminClient, NewTopic
import logging

logging.basicConfig(level="INFO",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
logger = logging.getLogger("create_kafka_topics")

admin_client = KafkaAdminClient(
    bootstrap_servers="kafka:9092", 
    client_id='test'
)

topics_list = admin_client.list_topics()
needed_topics = {"reddit_posts", "reddit_comments"}.difference(set(topics_list))
if not needed_topics:
    logger.info("Topics already exist")
else:
    logger.info(f"Creating topics: {needed_topics}")

    for topic in needed_topics:
        topic_object= NewTopic(name=topic, num_partitions=1, replication_factor=1)
        try:
            admin_client.create_topics(new_topics=topics_list, validate_only=False)
            logger.info(f"Topic {topic} created")
        except Exception as e:
            logger.error(f"Error creating topic {topic}: {e}")