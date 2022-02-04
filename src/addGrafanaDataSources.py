# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import requests

TIMEOUT = 10
logging.basicConfig(level=logging.INFO)

headers = {
    'Content-Type': 'application/json',
}
HTTP_SERVER_PROTOCOL = "http"
HTTPS_SERVER_PROTOCOL = "https"
DATA_SOURCE_NAME = "InfluxDB"
DATA_SOURCE_TYPE = "influxdb"
DATA_SOURCE_DIRECT_ACCESS = "direct"
DATA_SOURCE_PROXY_ACCESS = "proxy"
DATA_SOURCE_JSONDATA_VERSION = "Flux"
# The port inside the container that we map to a port on the host
INFLUXDB_CONTAINER_PORT = 8086
INFLUXDB_CERT_RELATIVE_PATH = "influxdb2_certs/influxdb.crt"
INFLUXDB_KEY_RELATIVE_PATH = "influxdb2_certs/influxdb.key"


def create_influxdb_datasource_config(influxdb_parameters, cert, key) -> dict:
    """

    :param influxdb_parameters: The retrieved InfluxDB parameter JSON
    :param cert: The InfluxDB cert for HTTPS.
    :param key: The InfluxDB key for HTTPS.
    :return: data: The datasource JSON to add.
    """

    data = {}

    # InfluxDB port inside the container is always 8086 unless overridden inside the InfluxDB config
    # We reference the InfluxDB container name in the provided URL instead of using localhost/127.0.0.1
    # since this will be interpreted from inside the Grafana container
    if influxdb_parameters['InfluxDBServerProtocol'] == HTTP_SERVER_PROTOCOL:
        data = {
            "name": DATA_SOURCE_NAME,
            "type": DATA_SOURCE_TYPE,
            "access": DATA_SOURCE_DIRECT_ACCESS,
            "editable": False,
            "url": "http://{}:{}".format(influxdb_parameters['InfluxDBContainerName'], INFLUXDB_CONTAINER_PORT),
            "jsonData": {
                "version": DATA_SOURCE_JSONDATA_VERSION,
                "organization": influxdb_parameters['InfluxDBOrg'],
                "defaultBucket": influxdb_parameters['InfluxDBBucket'],
            },
            "secureJsonData": {
                "token": influxdb_parameters['InfluxDBToken']
            }
        }
    elif influxdb_parameters['InfluxDBServerProtocol'] == HTTPS_SERVER_PROTOCOL:
        data = {
            "name": DATA_SOURCE_NAME,
            "type": DATA_SOURCE_TYPE,
            "access": DATA_SOURCE_PROXY_ACCESS,
            "editable": False,
            "url": "https://{}:{}".format(influxdb_parameters['InfluxDBContainerName'], INFLUXDB_CONTAINER_PORT),
            "jsonData": {
                "version": DATA_SOURCE_JSONDATA_VERSION,
                "organization": influxdb_parameters['InfluxDBOrg'],
                "defaultBucket": influxdb_parameters['InfluxDBBucket'],
                "tlsSkipVerify": (influxdb_parameters['InfluxDBSkipTLSVerify'] == 'true'),
                "tlsAuth": True,
                "serverName": "https://{}:{}".format(influxdb_parameters['InfluxDBContainerName'],
                                                     INFLUXDB_CONTAINER_PORT)
            },
            "secureJsonData": {
                "token": influxdb_parameters['InfluxDBToken'],
                "tlsClientCert": cert,
                "tlsClientKey": key
            }
        }
    else:
        logging.error("Received invalid InfluxDBServerProtocol! Should be http or https, but was: {}"
                      .format(influxdb_parameters['InfluxDBServerProtocol']))

    logging.info("Generated InfluxDB datasource config")
    return data


def create_and_add_datasource_to_grafana(url, data, tls_verify):
    """

    :param url: The Grafana URL to send requests to.
    :param data: The datasource JSON to add.
    :param tls_verify: Use TLS verify or not.
    :return:
    """

    logging.info("Adding generated datasource to Grafana")
    response = requests.post(url=url, headers=headers, data=json.dumps(data), verify=tls_verify)
    if response.status_code != 200:
        logging.error("Request to add datasource request to Grafana failed with status code {}! "
                      "Check the aws.greengrass.labs.dashboard.Grafana log to investigate."
                      .format(response.status_code))
        exit(1)


def influxdb_datasource_exists(grafana_server_protocol, username, password, grafana_port,
                               tls_verify):
    """

    :param grafana_server_protocol: HTTP or HTTPS
    :param username: The retrieved Grafana username
    :param password: The retrieved Grafana password
    :param grafana_port: The Grafana port
    :param tls_verify: Use TLS verify or not.
    :return:
    """
    url = '{}://{}:{}@localhost:{}/api/datasources/name/{}' \
        .format(grafana_server_protocol, username, password, grafana_port, DATA_SOURCE_NAME)
    response = requests.get(url=url, headers=headers, verify=tls_verify)
    logging.info("Grafana response status code: {}".format(response.status_code))
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        logging.info("No InfluxDB data source exists in Grafana. Creating one now...")
        return False
    else:
        logging.warning("Grafana has returned the response code {}. InfluxDB may not have been set up"
                        " or configured correctly.".format(response.status_code))
        return False


def add_influxdb_datasource_to_grafana(mount_path, grafana_secrets, influxdb_parameters, grafana_port,
                                       grafana_server_protocol, tls_verify):
    """

    :param mount_path: The InfluxDB mount path.
    :param grafana_secrets: The retrieved Grafana secret JSON containing the username/password.
    :param influxdb_parameters: The retrieved InfluxDB parameter JSON
    :param grafana_port: The Grafana port
    :param grafana_server_protocol:  HTTP or HTTPS
    :param tls_verify: Use TLS verify or not.
    :return:
    """

    if not tls_verify:
        import urllib3
        # Necessary to suppress warning for self-signed certs
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    username = grafana_secrets["grafana_username"]
    password = grafana_secrets["grafana_password"]

    try:

        # Check if the InfluxDB data source is already present
        if not influxdb_datasource_exists(grafana_server_protocol, username, password, grafana_port, tls_verify):
            logging.info("No InfluxDB data source found, creating a new one...")
            cert = key = ""

            # If using HTTPS, load in the cert and key
            if influxdb_parameters['InfluxDBServerProtocol'] == HTTPS_SERVER_PROTOCOL:
                logging.info("Retrieving InfluxDB cert and key from mount path...")
                with open(os.path.join(mount_path, INFLUXDB_CERT_RELATIVE_PATH)) as f:
                    cert = f.read()
                with open(os.path.join(mount_path, INFLUXDB_KEY_RELATIVE_PATH)) as f:
                    key = f.read()
                if len(cert) == 0 or len(key) == 0:
                    raise ValueError("Retrieved Grafana certs are empty!")

            config = create_influxdb_datasource_config(influxdb_parameters, cert, key)
            url = '{}://{}:{}@localhost:{}/api/datasources' \
                .format(grafana_server_protocol, username, password, grafana_port)
            create_and_add_datasource_to_grafana(url, config, tls_verify)
            logging.info("InfluxDB datasource successfully added to Grafana!")
        else:
            logging.info("InfluxDB data source is already present, exiting...")
            exit(0)
    except Exception as e:
        logging.error('Exception occurred when adding InfluxDB datasource to Grafana.', exc_info=True)
        raise e
