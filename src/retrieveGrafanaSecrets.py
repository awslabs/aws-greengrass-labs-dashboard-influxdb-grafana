# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import awsiot.greengrasscoreipc
from awsiot.greengrasscoreipc.model import GetSecretValueRequest, UnauthorizedError

TIMEOUT = 10
logging.basicConfig(level=logging.INFO)


def get_secret_over_ipc(secret_arn) -> str:
    """
    Parse arguments.

    Parameters
    ----------
        secret_arn(str): The ARN of the secret to retrieve from Secret Manager.

    Returns
    -------
        secret_string(str): Retrieved IPC secret.
    """

    try:
        ipc_client = awsiot.greengrasscoreipc.connect()
        request = GetSecretValueRequest()
        request.secret_id = secret_arn
        operation = ipc_client.new_get_secret_value()
        operation.activate(request)
        futureResponse = operation.get_response()
        response = futureResponse.result(TIMEOUT)
        return response.secret_value.secret_string
    except TimeoutError as e:
        logging.error("Timeout occurred while getting secret: {}".format(secret_arn), exc_info=True)
        raise e
    except UnauthorizedError as e:
        logging.error("Unauthorized error while getting secret: {}".format(secret_arn), exc_info=True)
        raise e
    except Exception as e:
        logging.error("Exception while getting secret: {}".format(secret_arn), exc_info=True)
        raise e


def retrieve_secret(secret_arn):
    """
    Get Secret Arn.
    :param secret_arn: the AWS Secret Manager secret ARN
    :return: the secret JSON string
    """

    try:
        response = get_secret_over_ipc(secret_arn)
        responseString = json.loads(response)
        if len(responseString) == 0:
            raise ValueError("Retrieved Grafana secret was empty!")
        if "grafana_username" in responseString and "grafana_password" in responseString:
            return responseString
        else:
            raise ValueError("Retrieved Grafana secret is in an invalid format!")
    except Exception as e:
        logging.error("Exception while retrieving secret: {}".format(secret_arn), exc_info=True)
        raise e
