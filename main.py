import json
import boto3
import os
import uuid


def authorize(event, context):
    supplied_token = event["authorizationToken"]

    if supplied_token == os.environ["VALID_TOKEN"]:
        effect = "Allow"
    else:
        effect = "Deny"

    return {
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": _allow_all_methods(event["methodArn"]),
            }],
        },
    }


def list_announcements(event, context):
    items = boto3.client('dynamodb').scan(
        TableName=os.environ["TABLE_NAME"],
    ).get("Items", [])
    
    return json.dumps({
        "announcements": _format_dynamodb_output(items),
    })


def create_announcement(body, context):
    try:
        params = json.loads(body)
    except Exception as e:
        return json.dumps({"message": "Error: {}".format(str(e))})

    if not isinstance(params, dict):
        return json.dumps({"message": "Error: request body is malformed"})

    supplied_fields = set([key for key, value in params.items()])

    if not(supplied_fields <= set(["title", "description", "date"])):
        return json.dumps({"message": "Error: incorrect set of fields"})
    else:
        for field_name in supplied_fields:
            if not isinstance(params[field_name], str):
                return json.dumps({"message": "Error: only string values are supported"})

        boto3.client('dynamodb').put_item(
            TableName=os.environ['TABLE_NAME'],
            Item=_create_item(params),
        )

    return json.dumps({
        "message": "Success",
    })


def _allow_all_methods(method_arn):
    arn_split = method_arn.split(":")
    api_details_split = arn_split[5].split("/")
    api_details_split[2] = "*"
    api_details = "/".join(api_details_split)
    arn_split[5] = api_details

    return ":".join(arn_split)


def _format_dynamodb_output(items):
    result = []

    for item in items:
        formatted_item = {}

        for key, type_plus_value in item.items():
            if key == "uid": continue

            formatted_item[key] = type_plus_value["S"]

        result.append(formatted_item)

    return result


def _create_item(params):
    result = {}

    for key, value in params.items():
        result[key] = {"S": value}

    result["uid"] = {"S": str(uuid.uuid1())}

    return result
