#!/bin/bash 

mkdir -p builds

# build attach hosted zone
cd lambda/attach_hosted_zone/
pip install -r requirements.txt -t .
zip -r ../../builds/attach_hosted_zone.zip ./*
cd -

# build get DBCluster.ReaderEndpoint
cd lambda/rds_ro_name/
pip install -r requirements.txt -t .
zip -r ../../builds/rds_ro_name.zip ./*
cd -
