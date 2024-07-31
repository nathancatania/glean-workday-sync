# Serve Sample Workday Reports for Testing

This folder contains code for a GCP Cloud Function designed to provide an endpoint that can be used to test the fetching of Workday Reports.

The URL of the Cloud Function can be used as the value for WORKDAY_REPORT_URL when testing the connector.

The Cloud Function response is authenticated using either basic or bearer authentication (mimicking an actual Workday Report endpoint), and returns sample data in JSON format using the same structure as what would come from a Workday Report URL.

This allows the data fetching components of the connector to be tested wihtout having access to an actual Workday instance.

## Setup

Modify the variables inside `deploy.sh` as needed. Then run:

```
chmod +x deploy.sh
./deploy.sh
```

This will:
* Create a secret with the password/bearer value in it that is used by the Cloud Function to authenticate requests.
* Create a Service Account and give it permissions to call the Cloud Function and access the specific secret above.
* Deploy a GCP Cloud Function to serve the sample data (`sample_data.json`, `sample_data_teams.json`, etc).

## Usage

Once deployed, the Cloud Function URL can be used as the WORKDAY_REPORT_URL for testing. You must append ?format=json to the end of the URL setting it as the value for WORKDAY_REPORT_URL.

Different sample data sets can be returned by using the `report` parameter in the URL, e.g.:

* `https://<cloud-function-url>?format=json&report=teams` will return data suitable for testing the `--teamsonly` flag of the connector.
* `https://<cloud-function-url>?format=json&report=additionalfields` will return data suitable for testing additional fields that can be optionally synced to Glean.

## Cleanup

You can run `cleanup.sh` to remove all resources created by this script:

* The deployed cloud function will be deleted.
* The IAM bindings for the service account will be removed.
* The service account will be deleted.
* (Optionally) The secret will be deleted
    * You will need to uncomment out the `# Delete the secret` section in the script if you want this step to happen.
