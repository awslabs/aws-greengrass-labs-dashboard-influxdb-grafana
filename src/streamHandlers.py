# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging

import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    SubscriptionResponseMessage
)


class InfluxDBDataStreamHandler(client.SubscribeToTopicStreamHandler):
    def __init__(self):
        super().__init__()
        self.influxdb_parameters = {}

    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        """
        When we receive a message over IPC on the token response topic, load in the InfluxDB parameters

        Parameters
        ----------
            event(SubscriptionResponseMessage): The received IPC message

        Returns
        -------
            None
        """
        try:
            self.influxdb_parameters = event.json_message.message
            if len(self.influxdb_parameters) == 0:
                raise ValueError("Retrieved Influxdb parameters are empty!")
        except Exception:
            logging.error('Failed to load telemetry event JSON!', exc_info=True)
            exit(1)

    def on_stream_error(self, error: Exception) -> bool:
        """
        Log stream errors but keep the stream open.

        Parameters
        ----------
            error(Exception): The exception we see as a result of the stream error.

        Returns
        -------
            False(bool): Return False to keep the stream open.
        """
        logging.error("Received a stream error.", exc_info=True)
        return False  # Return True to close stream, False to keep stream open.

    def on_stream_closed(self) -> None:
        """
        Handle the stream closing.

        Parameters
        ----------
            None

        Returns
        -------
            None
        """
        logging.info('Subscribe to InfluxDB response topic stream closed.')
