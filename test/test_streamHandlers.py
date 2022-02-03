# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import sys
import pytest
import logging
import src.streamHandlers as streamHandler


from awsiot.greengrasscoreipc.model import (
    SubscriptionResponseMessage, JsonMessage
)

logging.basicConfig(level=logging.INFO)

sys.path.append("src/")

testparams = {
    'InfluxDBContainerName': 'greengrass_InfluxDB',
    'InfluxDBOrg': 'greengrass',
    'InfluxDBBucket': 'greengrass-telemetry',
    'InfluxDBPort': '8086',
    'InfluxDBInterface': '127.0.0.1',
    'InfluxDBToken': 'vb53ZyYlxJjAeWcDbgPjbNvkvdD95b2hCrt0CoaZyEL5QYBiQfLw3TbgqgDozj74_aZ9pYCwVJM6Vj5quLAfSA==',
    'InfluxDBServerProtocol': 'https',
    'InfluxDBSkipTLSVerify': 'true',
    'InfluxDBTokenAccessType': 'RW'
}


def test_validInfluxDBParams(mocker):

    handler = streamHandler.InfluxDBDataStreamHandler()
    message = JsonMessage(message=testparams)
    response_message = SubscriptionResponseMessage(json_message=message)
    handler.on_stream_event(response_message)
    assert handler.influxdb_parameters == testparams


def test_invalidInfluxDBParams(mocker):
    import src.streamHandlers as streamHandler

    emptyparams = {}

    handler = streamHandler.InfluxDBDataStreamHandler()
    message = JsonMessage(message=emptyparams)
    response_message = SubscriptionResponseMessage(json_message=message)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        handler.on_stream_event(response_message)
        assert pytest_wrapped_e.type == SystemExit


def test_stream_operations(mocker):

    try:
        handler = streamHandler.InfluxDBDataStreamHandler()
        assert not handler.on_stream_error(ValueError("test"))
        handler.on_stream_closed()
    except Exception:
        logging.error("Caught an exception that should not have been thrown!")
        assert False
