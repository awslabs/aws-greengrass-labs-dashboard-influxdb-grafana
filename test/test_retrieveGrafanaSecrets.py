# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import sys
import pytest
import json
from awsiot.greengrasscoreipc.model import UnauthorizedError
import src.retrieveGrafanaSecrets as ris

sys.path.append("src/")

test_grafana_secrets = {
    "grafana_username": "username",
    "grafana_password": "password"
}


def test_retrieve_secret_valid_response(mocker):

    mock_ipc_call = mocker.patch("src.retrieveGrafanaSecrets.get_secret_over_ipc",
                                 return_value=json.dumps(test_grafana_secrets))
    result = ris.retrieve_secret("arn:test:object")
    assert result == test_grafana_secrets
    assert mock_ipc_call.call_count == 1
    mock_ipc_call.assert_any_call("arn:test:object")


def test_retrieve_secret_invalid_response(mocker):

    testArn = "garbage"
    mock_ipc_call = mocker.patch("src.retrieveGrafanaSecrets.get_secret_over_ipc", return_value=json.dumps(testArn))
    with pytest.raises(ValueError, match='Retrieved Grafana secret is in an invalid format'):
        ris.retrieve_secret("arn:test:object")
    assert mock_ipc_call.call_count == 1
    mock_ipc_call.assert_any_call("arn:test:object")


def test_retrieve_secret_empty_response(mocker):

    testArn = {}
    mock_ipc_call = mocker.patch("src.retrieveGrafanaSecrets.get_secret_over_ipc", return_value=json.dumps(testArn))
    with pytest.raises(ValueError, match='Retrieved Grafana secret was empty!'):
        t = ris.retrieve_secret("arn:test:object")
        assert len(t) == 0
    assert mock_ipc_call.call_count == 1
    mock_ipc_call.assert_any_call("arn:test:object")


def test_no_ipc_connection(mocker):

    mock_ipc_call = mocker.patch("awsiot.greengrasscoreipc.connect", side_effect=TimeoutError("test"))

    with pytest.raises(TimeoutError, match='test'):
        ris.get_secret_over_ipc("arn:test:object")
        assert mock_ipc_call.call_count == 1

    mock_ipc_call = mocker.patch("awsiot.greengrasscoreipc.connect", side_effect=UnauthorizedError())
    with pytest.raises(UnauthorizedError):
        ris.get_secret_over_ipc("arn:test:object")
        assert mock_ipc_call.call_count == 1

    mock_ipc_call = mocker.patch("awsiot.greengrasscoreipc.connect", side_effect=Exception("test"))
    with pytest.raises(Exception, match='test'):
        ris.get_secret_over_ipc("arn:test:object")
        assert mock_ipc_call.call_count == 1


def test_valid_secret_retrieval(mocker):
    mock_ipc_client = mocker.patch("awsiot.greengrasscoreipc.connect")
    t = ris.get_secret_over_ipc("testArn")
    assert t is not None
    assert mock_ipc_client.call_count == 1
