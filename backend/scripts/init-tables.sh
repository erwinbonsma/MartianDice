#!/bin/sh

echo "Waiting for DynamoDB to start up"
sleep 10

echo "Creating tables"
DYNAMODB_CMD="aws dynamodb --endpoint-url http://dynamodb:8000 --region eu-west-1"
STAGE_NAME=dev

${DYNAMODB_CMD} create-table \
	--table-name MartianDice-Rooms-${STAGE_NAME} \
	--attribute-definitions AttributeName=PKEY,AttributeType=S AttributeName=SKEY,AttributeType=S \
	--key-schema AttributeName=PKEY,KeyType=HASH AttributeName=SKEY,KeyType=RANGE \
	--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

${DYNAMODB_CMD} create-table \
	--table-name MartianDice-Games-${STAGE_NAME} \
	--attribute-definitions AttributeName=PKEY,AttributeType=S AttributeName=SKEY,AttributeType=S \
	--key-schema AttributeName=PKEY,KeyType=HASH AttributeName=SKEY,KeyType=RANGE \
	--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

echo "Done"

# Sleep so that container can be used to interactively inspect tables
sleep 2147483647