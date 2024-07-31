#!/bin/bash

# DEFAULTS
PHRASE_FOR_AUTH="youShouldChangeThis!"                          # This will be both the pwd and bearer token to use when accessing the endpoint for testing
CLOUD_FUNCTION_SERVICE_ACCOUNT="workday-tester-cf"              # Name of the service account to be created that will be assigned to the cloud function
CLOUD_FUNCTION_ENTRYPOINT="workday_report_export"               # The entry point of the cloud function
CLOUD_FUNCTION_DEPLOY_NAME="workday_test_cf"                    # The name of the cloud function to be deployed
SECRET_NAME="custom-connector-password"                         # The name of the secret to be created to store the report URL password/bearer token. You will need to update main.py as well if changed.

# Exit on any error
set -e

echo "Ensure you are authenticated with gcloud before running this script:"
echo "gcloud auth login --update-adc"

# Configuration
read -p "Enter your GCP Project ID (e.g. my-project-name): " PROJECT_ID

# Set project
gcloud config set project $PROJECT_ID

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

# Check if secret exists
if gcloud secrets describe $SECRET_NAME &>/dev/null; then
    echo "Secret $SECRET_NAME already exists. Skipping creation."
else
    echo "Creating secret..."
    echo -n "$PHRASE_FOR_AUTH" | gcloud secrets create $SECRET_NAME --data-file=-
fi

# Check if service account exists
if gcloud iam service-accounts describe $CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com &>/dev/null; then
    echo "Service account $CLOUD_FUNCTION_SERVICE_ACCOUNT already exists. Skipping creation."
else
    echo "Creating service account..."
    gcloud iam service-accounts create $CLOUD_FUNCTION_SERVICE_ACCOUNT --display-name "Workday Connector Cloud Function SA for Testing"

    # Assign roles to the service account
    echo "Assigning roles to service account..."
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/cloudfunctions.invoker" --condition="None"
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.invoker" --condition="None"
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/logging.logWriter" --condition="None"
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --condition="expression=resource.name.startsWith('projects/$PROJECT_NUMBER/secrets/$SECRET_NAME'),title=AccessSpecificSecretOnly,description=Only allow access to a specific secret."
fi

# Check if necessary files exist
for file in main.py requirements.txt sample_data.json sample_data_teams.json sample_data_additionalfields.json; do
    if [ ! -f "$file" ]; then
        echo "Error: $file not found in the current directory."
        exit 1
    fi
done

# Deploy the function
echo "Deploying function..."
gcloud functions deploy $CLOUD_FUNCTION_DEPLOY_NAME \
    --runtime=python312 \
    --source=. \
    --entry-point=$CLOUD_FUNCTION_ENTRYPOINT \
    --trigger-http \
    --allow-unauthenticated \
    --service-account=$CLOUD_FUNCTION_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
    --set-secrets=/secrets/$SECRET_NAME=$SECRET_NAME:latest \
    --min-instances=0 \
    --max-instances=1 \
    --security-level=secure-always

# Get the function URL
FUNCTION_URL=$(gcloud functions describe $CLOUD_FUNCTION_DEPLOY_NAME --format="value(httpsTrigger.uri)")

echo "Deployment complete!"
echo "Function URL: $FUNCTION_URL"
echo "You can test the function using:"
echo "curl -X GET '$FUNCTION_URL?format=json' -H 'Authorization: Basic $(echo -n 'workdayuser:$PHRASE_FOR_AUTH' | base64)'"