#!/bin/sh

echo "Waiting for DynamoDB to start up"
sleep 10

echo "Creating tables"
DYNAMODB_CMD="aws dynamodb --endpoint-url http://dynamodb:8000 --region eu-west-1"

${DYNAMODB_CMD} create-table \
	--table-name rooms \
	--attribute-definitions AttributeName=PKEY,AttributeType=S AttributeName=SKEY,AttributeType=S \
	--key-schema AttributeName=PKEY,KeyType=HASH AttributeName=SKEY,KeyType=RANGE \
	--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

${DYNAMODB_CMD} create-table \
	--table-name games \
	--attribute-definitions AttributeName=PKEY,AttributeType=S \
	--key-schema AttributeName=PKEY,KeyType=HASH \
	--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
