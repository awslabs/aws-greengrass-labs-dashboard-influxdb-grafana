# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
import sys
import requests
import src.addGrafanaDataSources as agds
from unittest import mock

sys.path.append("src")

testInfluxDBParams = {
    'InfluxDBContainerName': 'greengrass_InfluxDB',
    'InfluxDBOrg': 'greengrass',
    'InfluxDBBucket': 'greengrass-telemetry',
    'InfluxDBPort': '8086',
    'InfluxDBInterface': '127.0.0.1',
    'InfluxDBToken': 'testToken',
    'InfluxDBServerProtocol': 'https',
    'InfluxDBSkipTLSVerify': 'true',
    'InfluxDBTokenAccessType': 'RO'
}

https_publish_json = {
    "name": "InfluxDB",
    "type": "influxdb",
    "access": "proxy",
    "editable": False,
    "url": "https://greengrass_InfluxDB:8086",
    "jsonData": {
        "version": "Flux",
        "organization": "greengrass",
        "defaultBucket": "greengrass-telemetry",
        "tlsSkipVerify": True,
        "tlsAuth": True,
        "serverName": "https://greengrass_InfluxDB:8086"
    },
    "secureJsonData": {
        "token": "testToken",
        "tlsClientCert": "testCert",
        "tlsClientKey": "testKey"
    }
}

http_publish_json = {
    "name": "InfluxDB",
    "type": "influxdb",
    "access": "direct",
    "editable": False,
    "url": "http://greengrass_InfluxDB:8086",
    "jsonData": {
        "version": "Flux",
        "organization": "greengrass",
        "defaultBucket": "greengrass-telemetry",
    },
    "secureJsonData": {
        "token": "testToken"
    }
}

test_grafana_secrets = {
    "grafana_username": "username",
    "grafana_password": "password"
}

testCert = "testCert"
testKey = "testKey"


def test_create_https_influxdb_datasource_data():

    output = agds.create_influxdb_datasource_config(testInfluxDBParams, testCert, testKey)
    assert output == https_publish_json


def test_create_http_influxdb_datasource_data():

    testInfluxDBParams['InfluxDBServerProtocol'] = 'http'
    output = agds.create_influxdb_datasource_config(testInfluxDBParams, "", "")
    assert output == http_publish_json


def test_add_valid_datasource_to_grafana(mocker):
    testResp = requests.Response()
    testResp.status_code = 200
    mocker.patch('requests.post', return_value=testResp)
    agds.create_and_add_datasource_to_grafana("https://test", "test", False)


def test_add_invalid_datasource_to_grafana(mocker):
    testResp = requests.Response()
    testResp.status_code = 404
    mocker.patch('requests.post', return_value=testResp)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        agds.create_and_add_datasource_to_grafana("https://test", "test", False)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_influxdb_datasource_exists(mocker):
    testResp = requests.Response()
    testResp.status_code = 200
    mocker.patch('requests.get', return_value=testResp)
    assert agds.influxdb_datasource_exists("https://test", "username", "password", "3000", False)


def test_influxdb_datasource_does_not_exist(mocker):
    testResp = requests.Response()
    testResp.status_code = 404
    mocker.patch('requests.get', return_value=testResp)
    assert not agds.influxdb_datasource_exists("https://test", "username", "password", "3000", False)


def test_influxdb_datasource_error(mocker):
    testResp = requests.Response()
    testResp.status_code = 400
    mocker.patch('requests.get', return_value=testResp)
    assert not agds.influxdb_datasource_exists("https://test", "username", "password", "3000", False)


def test_add_existing_influxdb_datasource_to_grafana(mocker):
    mocker.patch('src.addGrafanaDataSources.influxdb_datasource_exists', return_value=True)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        agds.add_influxdb_datasource_to_grafana("testPath", test_grafana_secrets, {}, 3000,
                                                "https", False)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_add_new_influxdb_datasource_to_grafana(mocker):
    testInfluxDBParams['InfluxDBServerProtocol'] = 'https'
    testResp = requests.Response()
    testResp.status_code = 200
    mocker.patch('requests.post', return_value=testResp)
    mocker.patch('src.addGrafanaDataSources.influxdb_datasource_exists', return_value=False)

    my_text = "mock text"
    mocked_open_function = mock.mock_open(read_data=my_text)

    with mock.patch("builtins.open", mocked_open_function):
        agds.add_influxdb_datasource_to_grafana("testPath", test_grafana_secrets, testInfluxDBParams, 3000,
                                                "https", False)


def test_invalid_grafana_certs(mocker):
    testInfluxDBParams['InfluxDBServerProtocol'] = 'https'
    testResp = requests.Response()
    testResp.status_code = 200
    mocker.patch('requests.post', return_value=testResp)
    datasource_exists_mocker = mocker.patch('src.addGrafanaDataSources.influxdb_datasource_exists', return_value=False)

    my_text = ""
    mocked_open_function = mock.mock_open(read_data=my_text)

    with mock.patch("builtins.open", mocked_open_function):
        with pytest.raises(ValueError, match='Retrieved Grafana certs are empty'):
            agds.add_influxdb_datasource_to_grafana("testPath", test_grafana_secrets, testInfluxDBParams, 3000, "https",
                                                    False)

    assert datasource_exists_mocker.call_count == 1


def test_invalid_influxdb_server_protocol():
    testInfluxDBParams['InfluxDBServerProtocol'] = 'test'
    data = agds.create_influxdb_datasource_config(testInfluxDBParams, "testCert", "testKey")
    assert data == {}
