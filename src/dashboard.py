# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import argparse

import retrieveInfluxDBParams
import retrieveGrafanaSecrets
import addGrafanaDataSources

logging.basicConfig(level=logging.INFO)
TIMEOUT = 10


def parse_arguments() -> argparse.Namespace:
    """
    Parse arguments.

    Parameters
    ----------
        None

    Returns
    -------
        args(Namespace): Parsed arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--subscribe_topic", type=str, required=True)
    parser.add_argument("--publish_topic", type=str, required=True)
    parser.add_argument("--mount_path", type=str, required=True)
    parser.add_argument("--grafana_secret_arn", type=str, required=True)
    parser.add_argument('--skip_tls_verify', type=str, required=True)
    parser.add_argument('--grafana_port', type=str, required=True)
    parser.add_argument('--grafana_server_protocol', type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":

    try:
        args = parse_arguments()
        tls_verify = not (args.skip_tls_verify == 'true')

        grafana_secrets = retrieveGrafanaSecrets.retrieve_secret(args.grafana_secret_arn)
        influxdb_parameters = retrieveInfluxDBParams.retrieve_influxdb_params(args.publish_topic, args.subscribe_topic)
        addGrafanaDataSources.add_influxdb_datasource_to_grafana(
            args.mount_path,
            grafana_secrets,
            influxdb_parameters,
            args.grafana_port,
            args.grafana_server_protocol,
            tls_verify)
    except Exception:
        logging.error('Exception occurred when setting up dashboard.', exc_info=True)
        exit(1)
