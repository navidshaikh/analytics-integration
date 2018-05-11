#!/bin/bash
for item in $(cat repo_list)
do
    cd $item
    git pull origin master
    context=$(grep current config.yaml|cut -f2 -d " ")
    saasherder --context $context pull
    cd ../
done

IMAGE=$1
IMAGE=$(echo $IMAGE|sed -e "s/\/osio-prod\//\//g")
NAME_SPACE=$(echo $IMAGE|cut -f2 -d "/")
APP_NAME=$(echo $IMAGE|cut -f3 -d "/"|cut -f1 -d ":")

for item in $(cat repo_list)
do
  cd $item
  CURRENT_CONTEXT=$(grep current config.yaml|cut -f2 -d " ")
  GIT_URL=$(saasherder --context $CURRENT_CONTEXT get url $APP_NAME)
  rc=$?
  if [ $? == 0 ]
  then
    GIT_HASH=$(saasherder --context $CURRENT_CONTEXT get hash $APP_NAME)
    TAG_LENGTH=$(saasherder --context $CURRENT_CONTEXT get has_length $APP_NAME)
    IMAGE_TAG=$(echo $GIT_HASH|cut -c1-$TAG_LENGTH)
    echo "git-url=$GIT_URL"
    echo "git-sha=$GIT_HASH"
    echo "image-tag=$IMAGE_TAG"
    cd ../
    exit 0
  else
    echo "GIT_URL not found for $APP_NAME in $CURRENT_CONTEXT, checking next!"
    cd ../
    continue
done

echo "$NAME_SPACE/$APP_NAME not found via saasherder."
exit 1
