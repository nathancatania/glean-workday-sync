#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
CLOUD_FUNCTION_SERVICE_ACCOUNT="workday-tester-cf"
CLOUD_FUNCTION_DEPLOY_NAME="workday_test_cf"
SECRET_NAME="custom-connector-password"

# Exit on any error
set -e

# Delete the Cloud Function
echo "Deleting Cloud Function $CLOUD_FUNCTION_DEPLOY_NAME..."
gcloud functions delete $CLOUD_FUNCTION_DEPLOY_NAME --quiet

# Remove IAM bindings
echo "Removing IAM bindings for service account $CLOUD_FUNCTION_SERVICE_ACCOUNT..."
gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudfunctions.invoker" \
    --condition="None" \
    --quiet

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --condition="None" \
    --quiet

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --condition="None" \
    --quiet

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --all \
    --quiet

# Delete the secret
# echo "Deleting secret $SECRET_NAME..."
# gcloud secrets delete $SECRET_NAME --quiet

# Delete the service account
echo "Deleting service account $CLOUD_FUNCTION_SERVICE_ACCOUNT..."
gcloud iam service-accounts delete $CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com --quiet

echo "Cleanup complete!"