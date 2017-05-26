#!/usr/bin/env python2.7
import json
import boto3
import urllib2
from cfnresponse import send, SUCCESS, FAILED
import logging
from optparse import OptionParser


logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class rds_readerendpoint(object):
    reason = None
    response_data = None

    def __init__(self, event, context):
        self.event = event
        self.context = context
        logger.info("Event: %s" % self.event)
        logger.info("Context: %s" % self.context)
        if self.context != None:
           self.rds = boto3.session.Session().client('rds')
        else:
           self.rds = boto3.session.Session(profile_name=event['ResourceProperties']['Profile']).client('rds')
        try:
            self.db_cluster_id = event['ResourceProperties']['DBClusterIdentifier']
        except KeyError as e:
            self.reason = "Missing required property %s" % e
            logger.error(self.reason)
            if self.context:
                self.send_status(FAILED)
            return

    def create(self, updating=False):
        try:
            response = self.rds.describe_db_clusters(
                DBClusterIdentifier=self.db_cluster_id
            )
            self.response_data = {}
            self.response_data['ReaderEndpoint'] = response['DBClusters'][0]['ReaderEndpoint']
            logger.info("Response: %s" % response)
            if not updating:
                self.send_status(SUCCESS)
        except Exception as e:
            self.reason = "Describe DB Cluster call Failed %s" % e
            logger.error(self.reason)
            if self.context:
                self.send_status(FAILED)
            return

    def delete(self, updating=False):
        self.send_status(SUCCESS)

    def update(self):
        self.create(updating=True)
        #self.delete(updating=True)
        self.send_status(SUCCESS)

    def send_status(self, PASS_OR_FAIL):
        send(
            self.event,
            self.context,
            PASS_OR_FAIL,
            reason=self.reason,
            response_data=self.response_data
        )

def lambda_handler(event, context):
    attachment = rds_readerendpoint(event, context)
    if event['RequestType'] == 'Delete':
        attachment.delete()
        return
    if event['RequestType'] == 'Create':
        attachment.create()
        return
    if event['RequestType'] == 'Update':
        attachment.update()
        return
    logger.info("Received event: " + json.dumps(event, indent=2))
    if context:
        send(event, context, FAILED, reason="Unknown Request Type %s" % event['RequestType'])


if __name__ == "__main__":
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d","--db_cluster_id", help="Which DB Cluster.")
    parser.add_option("-p","--profile", help="Profile name to use when connecting to aws.", default="default")
    parser.add_option("-x","--execute", help="Execute an update create or delete.", default="Create")
    (opts, args) = parser.parse_args()

    options_broken = False
    if not opts.db_cluster_id:
        logger.error("Must Specify DB Cluster")
        options_broken = True
    if options_broken:
        parser.print_help()
        exit(1) 
    if opts.execute != 'Update':
        event = { 'RequestType': opts.execute, 'ResourceProperties': { 'DBClusterIdentifier': opts.db_cluster_id, 'Profile': opts.profile } }
    else:
        event = { 'RequestType': opts.execute, 'ResourceProperties': { 'DBClusterIdentifier': opts.db_cluster_id, 'Profile': opts.profile }, 'OldResourceProperties': { 'DBClusterIdentifier': opts.db_cluster_id, 'Profile': opts.profile } }
    lambda_handler(event, None)
