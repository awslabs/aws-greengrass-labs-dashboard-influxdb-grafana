# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import sys
import pytest
import json
import logging
from unittest.mock import patch
import concurrent.futures

from awsiot.greengrasscoreipc.model import UnauthorizedError
import src.retrieveInfluxDBParams as ridp

TIMEOUT = 10
logging.basicConfig(level=logging.INFO)
test_publish_topic = "test/topic"

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


def timeout_helper():
    raise concurrent.futures.TimeoutError("test")


def unauthorized_helper():
    raise UnauthorizedError()


def exception_helper():
    raise Exception("test")


@patch('streamHandlers.InfluxDBDataStreamHandler')
def test_retrieve_influxdb_params(InfluxDBDataStreamHandler, mocker):

    mocker.patch("awsiot.greengrasscoreipc.connect")
    handler = InfluxDBDataStreamHandler()
    handler.influxdb_parameters = str.encode(json.dumps(testparams))
    params = ridp.retrieve_influxdb_params("test/topic", "test/topic")
    assert json.loads(params) == testparams


@patch('streamHandlers.InfluxDBDataStreamHandler')
def test_fail_to_retrieve_influxdb_params(InfluxDBDataStreamHandler, mocker):

    mocker.patch("awsiot.greengrasscoreipc.connect")
    handler = InfluxDBDataStreamHandler()
    handler.influxdb_parameters = None
    mocker.patch("src.retrieveInfluxDBParams.publish_token_request", side_effect=ValueError("test"))
    with pytest.raises(SystemExit) as e:
        ridp.retrieve_influxdb_params("test/topic", "test/topic")
        assert e.type == SystemExit
        assert e.value.code == 1


@patch('streamHandlers.InfluxDBDataStreamHandler')
def test_errors_retrieving_influxdb_params(InfluxDBDataStreamHandler, mocker):

    # Speed up testing by changing the timeout
    ridp.TIMEOUT = .1
    mocker.patch("awsiot.greengrasscoreipc.connect")
    handler = InfluxDBDataStreamHandler()
    handler.influxdb_parameters = None
    mocker.patch("src.retrieveInfluxDBParams.publish_token_request")
    with pytest.raises(SystemExit) as e:
        ridp.retrieve_influxdb_params("test/topic", "test/topic")
        assert e.type == SystemExit
        assert e.value.code == 1

    mocker.patch("time.sleep", side_effect=Exception("test"))
    with pytest.raises(SystemExit) as e:
        ridp.retrieve_influxdb_params("test/topic", "test/topic")
        assert e.type == SystemExit
        assert e.value.code == 1


def test_no_ipc_connection(mocker):

    mock_ipc_call = mocker.patch("awsiot.greengrasscoreipc.connect", side_effect=concurrent.futures.TimeoutError("test"))

    with pytest.raises(concurrent.futures.TimeoutError, match='test'):
        ridp.retrieve_influxdb_params("test/topic", "test/topic")
        assert mock_ipc_call.call_count == 1

    mock_ipc_call = mocker.patch("awsiot.greengrasscoreipc.connect", side_effect=UnauthorizedError())
    with pytest.raises(UnauthorizedError):
        ridp.retrieve_influxdb_params("test/topic", "test/topic")
        assert mock_ipc_call.call_count == 1

    mock_ipc_call = mocker.patch("awsiot.greengrasscoreipc.connect", side_effect=Exception("test"))
    with pytest.raises(Exception, match='test'):
        ridp.retrieve_influxdb_params("test/topic", "test/topic")
        assert mock_ipc_call.call_count == 1


def test_valid_publish_token_request(mocker):
    try:
        mock_ipc_client = mocker.patch("awsiot.greengrasscoreipc.connect")
        ridp.publish_token_request(mock_ipc_client, test_publish_topic)
    except Exception:
        logging.error("Caught an exception that should not have been thrown!")
        assert False


def test_invalid_publish_token_request(mocker):
    mock_ipc_client = mocker.patch("awsiot.greengrasscoreipc.connect")
    mock_ipc_client.new_publish_to_topic = timeout_helper
    with pytest.raises(concurrent.futures.TimeoutError, match='test'):
        ridp.publish_token_request(mock_ipc_client, test_publish_topic)

    mock_ipc_client.new_publish_to_topic = unauthorized_helper
    with pytest.raises(UnauthorizedError):
        ridp.publish_token_request(mock_ipc_client, test_publish_topic)

    mock_ipc_client.new_publish_to_topic = exception_helper
    with pytest.raises(Exception, match='test'):
        ridp.publish_token_request(mock_ipc_client, test_publish_topic)
