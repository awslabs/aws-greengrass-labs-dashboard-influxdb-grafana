# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import sys
import pytest

sys.path.append("src/")


def test_parse_valid_args(mocker):
    mock_parse_args = mocker.patch(
        "argparse.ArgumentParser.parse_args", return_value=argparse.Namespace(
            subscribe_topic="test/subscribe",
            publish_topic="test/publish",
            mount_path="test_path",
            grafana_secret_arn="testarn",
            grafana_port="testport",
            grafana_server_protocol="testprotocol",
            skip_tls_verify="testskipverify"
        )
    )
    import src.dashboard as dashboard

    args = dashboard.parse_arguments()
    assert args.subscribe_topic == "test/subscribe"
    assert args.publish_topic == "test/publish"
    assert args.mount_path == "test_path"
    assert args.grafana_secret_arn == "testarn"
    assert args.grafana_port == "testport"
    assert args.grafana_server_protocol == "testprotocol"
    assert args.skip_tls_verify == "testskipverify"

    assert mock_parse_args.call_count == 1


def test_parse_no_args(mocker):
    import src.dashboard as dashboard

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        dashboard.parse_arguments()
    assert pytest_wrapped_e.type == SystemExit
