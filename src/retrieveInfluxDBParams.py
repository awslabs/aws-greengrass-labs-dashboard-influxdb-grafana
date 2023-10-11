# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import time
import logging

import awsiot.greengrasscoreipc
from awsiot.greengrasscoreipc.model import (
    PublishToTopicRequest,
    PublishMessage,
    SubscribeToTopicRequest,
    UnauthorizedError, JsonMessage
)
import streamHandlers

logging.basicConfig(level=logging.INFO)
TIMEOUT = 15


def publish_token_request(ipc_publisher_client, publish_topic) -> None:
    """
    Publish a token request to the specified publish topic.

    Parameters
    ----------
        ipc_publisher_client(awsiot.greengrasscoreipc.client): the Greengrass IPC client
        publish_topic(str): the topic to publish the request on

    Returns
    -------
        None
    """

    try:
        request = PublishToTopicRequest()
        request.topic = publish_topic
        publish_message = PublishMessage()
        publish_message.json_message = JsonMessage(
            message={
                "action": "RetrieveToken",
                "accessLevel": "RO"
            }
        )
        request.publish_message = publish_message
        publish_operation = ipc_publisher_client.new_publish_to_topic()
        publish_operation.activate(request)
        futureResponse = publish_operation.get_response()
        futureResponse.result(TIMEOUT)

    except concurrent.futures.TimeoutError as e:
        logging.error('Timeout occurred while publishing to topic: {}'.format(publish_topic), exc_info=True)
        raise e
    except UnauthorizedError as e:
        logging.error('Unauthorized error while publishing to topic: {}'.format(publish_topic), exc_info=True)
        raise e
    except Exception as e:
        logging.error('Exception while publishing to topic: {}'.format(publish_topic), exc_info=True)
        raise e


# Ignore flake8 complexity warning
# flake8: noqa: C901
def retrieve_influxdb_params(publish_topic, subscribe_topic) -> str:
    """
    Subscribe to a token response topic and send a request to the token request topic
    in order to retrieve InfluxDB parameters.

    Parameters
    ----------
        publish_topic(str): the topic to publish the request on
        subscribe_topic(str): the topic to subscribe on to retrieve the response

    Returns
    -------
        influxdb_parameters(str): the retrieved parameters needed to connect to InfluxDB
    """

    subscriber_operation = None
    try:
        # First, set up a subscription to the InfluxDB token response topic
        ipc_subscriber_client = awsiot.greengrasscoreipc.connect()
        request = SubscribeToTopicRequest()
        request.topic = subscribe_topic
        handler = streamHandlers.InfluxDBDataStreamHandler()
        subscriber_operation = ipc_subscriber_client.new_subscribe_to_topic(handler)
        future = subscriber_operation.activate(request)
        future.result(TIMEOUT)
        logging.info('Successfully subscribed to topic: {}'.format(subscribe_topic))
    except concurrent.futures.TimeoutError as e:
        logging.error('Timeout occurred while subscribing to topic: {}'.format(subscribe_topic), exc_info=True)
        raise e
    except UnauthorizedError as e:
        logging.error('Unauthorized error while subscribing to topic: {}'.format(subscribe_topic), exc_info=True)
        raise e
    except Exception as e:
        logging.error('Exception while subscribing to topic: {}'.format(subscribe_topic), exc_info=True)
        raise e

    # Next, send a publish request to the InfluxDB token request topic
    ipc_publisher_client = awsiot.greengrasscoreipc.connect()
    retries = 0
    try:
        # Retrieve InfluDB parameters to connect; retry up to 10 times
        while not handler.influxdb_parameters and retries < 10:
            logging.info("Publish attempt {}".format(retries))
            publish_token_request(ipc_publisher_client, publish_topic)
            logging.info('Successfully published token request to topic: {}'.format(publish_topic))
            retries += 1
            time.sleep(2)

    except Exception:
        logging.error("Received error while sending token publish request!", exc_info=True)
    finally:
        # Close the operations for the clients
        if subscriber_operation:
            subscriber_operation.close()
        logging.info("Closed InfluxDB parameter response subscriber client")
        if not handler.influxdb_parameters:
            logging.error("Failed to retrieve InfluxDB parameters over IPC!")
            exit(1)
        logging.info("Successfully retrieved InfluxDB metadata and token!")

    return handler.influxdb_parameters
