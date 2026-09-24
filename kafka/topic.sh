#!/bin/bash

set -e

BOOTSTRAP_SERVER="kafka-1:9092"

create_topic() {
    local topic=$1
    local partitions=$2

    docker exec kafka-1 \
        /opt/kafka/bin/kafka-topics.sh \
        --create \
        --if-not-exists \
        --topic "$topic" \
        --bootstrap-server "$BOOTSTRAP_SERVER" \
        --partitions "$partitions" \
        --replication-factor 3 \
        --config min.insync.replicas=2

    echo "Topic ready: $topic"
}

create_topic "agent.tasks" 12
create_topic "agent.events" 12
create_topic "agent.dlq" 6