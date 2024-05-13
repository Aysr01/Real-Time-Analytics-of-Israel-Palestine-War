#!/bin/bash
spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 --jars utils/postgresql-42.7.0.jar utils/comments_count.py