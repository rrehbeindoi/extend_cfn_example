import boto3
import httplib
import json
import urlparse
import uuid

"""
Example policy:
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:AddRoleToDBCluster",
                "rds:RemoveRoleFromDBCluster"
            ],
            "Resource": "arn:aws:rds:*:*:*"
        }
    ]
}
"""

def send_response(request, response, status=None, reason=None):
    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urlparse.urlparse(request['ResponseURL'])
        body = json.dumps(response)
        https = httplib.HTTPSConnection(url.hostname)
        https.request('PUT', url.path+'?'+url.query, body)

    return response

def lambda_handler(event, context=None):

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Status': 'SUCCESS'
    }

    if 'PhysicalResourceId' in event:
        response['PhysicalResourceId'] = event['PhysicalResourceId']
    else:
        response['PhysicalResourceId'] = str(uuid.uuid4())

    rds = boto3.client('rds')

    if event['RequestType'] == 'Delete' or event['RequestType'] == 'Update':
        try:
            clusterId = event['OldResourceProperties']['DBClusterIdentifier']
            roleArn   = event['OldResourceProperties']['RoleArn']
        except KeyError:
            return send_response(event, response, status='FAILED', reason='Missing DBClusterIdentifier or RoleArn')

        try:
            rds.remove_role_from_db_cluster(
                DBClusterIdentifier=clusterId,
                RoleArn=roleArn
            )
        except Exception as e:
            return send_response(event, response, status='FAILED', reason=e.message)

    if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
        try:
            clusterId = event['ResourceProperties']['DBClusterIdentifier']
            roleArn   = event['ResourceProperties']['RoleArn']
        except KeyError:
            return send_response(event, response, status='FAILED', reason='Missing DBClusterIdentifier or RoleArn')

        try:
            rds.add_role_to_db_cluster(
                DBClusterIdentifier=clusterId,
                RoleArn=roleArn
            )
        except Exception as e:
            return send_response(event, response, status='FAILED', reason=e.message)

    return send_response(event, response)
