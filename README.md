# Workday

Pull people and teams information from a Workday report and have it automatically pushed to Glean.

> [!NOTE]
> This connector has been refactored since it's initial release. The original script `workday_bulkindexemployees.py` is deprecated. It is available for customers that are still using it, but should not be used going forward.

## Requirements
- [x] Workday Report in JSON format.
- [x] Username/Password or API key to access the Workday report.
- [x] Glean Indexing API key.
- [x] Glean tenant/backend domain, e.g. `mycompany-be.glean.com`

### Workday Report
You must make available a Workday report, in JSON format, containing the directory/people data to be synced to Glean.

  * Workday reports can be accessed using a specific URL. This is required.
    * E.g. `https://wd3-services1.myworkday.com/ccx/service/customreport2/companyname/directory/reportname?format=json`
  * The report URL can be authenticated with either a username/password (basic auth) or bearer token.
    * This custom connector supports both.
  * The fields used are up to the customer and will vary between organizations. The custom connector code supports a mapping file that allows you to map which fields in the Workday report correspond to the people fields expected by Glean.

The following data is required in the report by Glean:

#### People Data

Mandatory:

1. Email
2. Name (alternatively, can be split into FirstName and LastName)
3. Department

Strongly recommended:

1. Manager Email
2. Title, e.g. "Software Engineer"
3. Start Date (YYYY-MM-DD), e.g. "2024-02-15"
4. Location information, i.e.
   * City
   * Country
   * State
   * etc

#### Teams Data Only
If you only want to use this connector to synchronize teams/squad/group information to Glean, then only the following fields are mandatory:

1. User email
2. List of team names & IDs for each team/squad/group the user is a member of.

<details>
<summary>Example Workday Report in JSON - People Data</summary>

> [!NOTE]
> The fields in your report may be different, e.g. `CF_-_Business_Unit` instead of `department`. This connector supports mapping the names of your fields the values expected by Glean.

```json
{
    "Report_Entry": [
        {
            "workerName": "John Doe",
            "workerEmail": "john.doe@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "pronoun": "He/Him",
            "businessTitle": "Software Engineer",
            "department": "Engineering",
            "managerEmail": "jane.smith@example.com",
            "businessUnit": "Product Development",
            "city": "San Francisco",
            "state": "California",
            "country": "United States",
            "region": "North America",
            "workerType": "Full-time",
            "workerID": "12345",
            "hireDate": "2020-01-01",
            "terminationDate": null,
            "bio": "Experienced software engineer with a passion for building scalable applications.",
            "office": "123 Main St, San Francisco, CA 94107",
            "primaryWorkPhone": "+1 (555) 123-4567",
            "workerStatus": "Active",
            "photo": "https://example.com/photos/john_doe.jpg",
            "linkedin": "https://www.linkedin.com/in/johndoe",
            "twitter": "https://twitter.com/johndoe",
            "workerTeams": [
                {
                    "teamName": "Web Development",
                    "teamID": "web-dev"
                }
            ]
        },
        {
            "workerName": "Jane Smith",
            "workerEmail": "jane.smith@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "pronoun": "She/Her",
            "businessTitle": "Product Manager",
            "department": "Product",
            "managerEmail": "michael.johnson@example.com",
            "businessUnit": "Product Development",
            "city": "New York",
            "state": "New York",
            "country": "United States",
            "region": "North America",
            "workerType": "Full-time",
            "workerID": "67890",
            "hireDate": "2018-05-15",
            "terminationDate": null,
            "bio": "Experienced product manager with a track record of delivering successful products.",
            "office": "456 Broadway, New York, NY 10013",
            "primaryWorkPhone": "+1 (555) 987-6543",
            "workerStatus": "Active",
            "photo": "https://example.com/photos/jane_smith.jpg",
            "linkedin": "https://www.linkedin.com/in/janesmith",
            "twitter": "https://twitter.com/janesmith",
            "workerTeams": [
                {
                    "teamName": "Product Management",
                    "teamID": "product-mgmt"
                },
                {
                    "teamName": "Product Development",
                    "teamID": "product-dev"
                }
            ]
        }
    ]
}
```
</details>

<details>
<summary>Example Workday Report in JSON - Teams Data Only</summary>

> [!NOTE]
> The fields in your report may be different, e.g. `teamName` instead of `Organisation_Name`. This connector supports mapping the names of your fields the values expected by Glean.

```json
{
   "Report_Entry": [
      {
         "Email_-_Work": "sally.smith@example.com",
         "CF_-_Business_Unit": "Product Development",
         "Employee_ID": "000555",
         "Worker": "Sally Smith",
         "Worker_s_Manager": "Amy Pond",
         "Delivery_Teams_group": [
            {
               "Organisation_Name": "Squad - Procurement",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-101"
            }
         ]
      },
      {
         "Email_-_Work": "ellie.example@example.com",
         "CF_-_Business_Unit": "Product Development",
         "Employee_ID": "000222",
         "Worker": "Ellie Example",
         "Worker_s_Manager": "Sally Smith",
         "Delivery_Teams_group": [
            {
               "Organisation_Name": "Squad - Core App",
               "Organisation_Reference_ID": "CUSTOM-ID__-Z-987"
            },
            {
               "Organisation_Name": "Squad - Engineering",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-1224"
            },
            {
               "Organisation_Name": "Squad - Foundations",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-XYZ102"
            }
         ]
      },
      {
         "Email_-_Work": "guy.incognito@example.com",
         "CF_-_Business_Unit": "Product Development",
         "Employee_ID": "008888",
         "Worker": "Guy Incognito",
         "Worker_s_Manager": "Sally Smith",
         "Delivery_Teams_group": [
            {
               "Organisation_Name": "Squad - Procurement",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-101"
            }
         ]
      },
      {
         "Email_-_Work": "ned.flanders@example.com",
         "CF_-_Business_Unit": "Finance",
         "Employee_ID": "008663",
         "Worker": "Ned Flanders",
         "Worker_s_Manager": "Monty Burns",
         "Delivery_Teams_group": [
            {
               "Organisation_Name": "Squad - Leads",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-220"
            },
            {
               "Organisation_Name": "Squad - Data & Analytics",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-167"
            },
            {
               "Organisation_Name": "Portfolio - FSI",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-62"
            },
            {
               "Organisation_Name": "Tribe - Integrations",
               "Organisation_Reference_ID": "ORGANIZATION_ID-Z-94"
            }
         ]
      }
   ]
}
```
</details>

### Glean Indexing API Key
  * You should use a different key for each service you integrate with Glean.
  * You can create one by [clicking here](https://app.glean.com/admin/setup/tokenManagement?tab=indexing).
  
    * **Description:**
      * Whatever you like, e.g. `Workday People Data Sync`
    * **Scopes:**
      * Enter `ENTITIES` in the scopes field.
      * **DO NOT** select global permissions option (if present). This is not needed.
    * **Expires:**
      * Select an appropriate expiration date up to 2 years into the future.
      * You will need to rotate the token yourself. Automatic token rotation is not supported with this custom connector.
    * **Greenlisted IPs:**
      * If testing, leave this blank.
        * Once you deploy into production and have this connector automatically run on a schedule, it is strongly recommended to greenlist the external IPs of the service (e.g. GCP CloudFunctions, AWS Lambda) that the custom connector is running on.
          * This ensures that the API key cannot be used elsewhere.
    * **Rotation period:**
      * Not supported. Leave blank.

### Glean Backend / Tenant Domain
  * This is in the format of `tenantid-be.glean.com`
  * It will always have the `-be` in the subdomain.
    * This is different to the domain that is used to access the Glean web interface, e.g. `app.glean.com`, `company.glean.com`
  * You can locate this by inspecting the Network tab using Developer Tools when making a search in Glean. You will see some requests being made to a `xxxxxx-be.glean.com` domain.
    * If you are unsure, contact Glean Support who can provide this for you.

---

## Usage

### 1. Set Environmental Variables

| ENV Name | Value |
| --- | ---|
| `WORKDAY_REPORT_URL` | The full URL of the Workday report in JSON format, e.g. `https://wd3-services1.myworkday.com/ccx/service/customreport2/companyname/directory/reportname?format=json` |
| `WORKDAY_AUTH_TYPE` | The way the connector will authenticate to fetch the Workday report. Can be `basic` for username/password or `bearer` for API key. |
| `WORKDAY_USERNAME` | The username to be used for basic username/password authentication. Only required if `WORKDAY_AUTH_TYPE=basic` |
| `WORKDAY_PASSWORD` | The password to be used for basic username/password authentication. Only required if `WORKDAY_AUTH_TYPE=basic` |
| `WORKDAY_API_KEY` | The API key to be used for bearer authentication. Only required if `WORKDAY_AUTH_TYPE=bearer` |
| `GLEAN_BACKEND_DOMAIN` | The tenant/backend domain for your Glean tenant, e.g. `mycompany-be.glean.com` |
| `GLEAN_API_KEY` | The Indexing API Key created in Glean. |

> [!TIP]
> You can also add these values to a `.env` file in the same directory as the `sync_people.py` script.

### 2. Update `mapping.json`

`mapping.json` maps the fields that the Glean API expects/understands to the fields containing that data in your Workday report.

Fields on the LHS are Glean API fields - these should **not** be modified, but CAN be removed if not required.

Fields on the RHS are the associated fields from the Workday report. These should be updated by you to match the report.

<details>
<summary>Example mapping.json</summary>

```json
{   
    "id": "workerID",
    "email": "workerEmail",
    "firstName": "firstName",
    "lastName": "lastName",
    "preferredName": "workerName",
    "pronoun": "pronoun",
    "title": "businessTitle",
    "department": "department",
    "managerEmail": "managerEmail",
    "businessUnit": "businessUnit",
    "type": "workerType",
    "startDate": "hireDate",
    "endDate": "terminationDate",
    "bio": "bio",
    "phoneNumber": "primaryWorkPhone",
    "photoUrl": "photo",
    "profileUrl": "workerProfile",
    "linkedinUrl": "linkedin",
    "twitterUrl": "twitter",
    "structuredLocation": {
        "address": "office",
        "city": "city",
        "state": "state",
        "country": "country",
        "region": "region",
        "zipCode": "zip_code",
        "timezone": "timezone",
        "deskLocation": "desk_location",
        "countryCode": "country_code"
    },
    "teams": [{
        "__sourceField": "workerTeams",
        "name": "teamName",
        "id": "teamID",
        "url": "teamUrl"
    }],
    "additionalFields": [
        "any_other_fields_in_the_source_data",
        "that_you_want_Glean_to_index",
        "should_be_listed_here",
        "for_example",
        "languages",
        "skills",
        "DOB",
        "backgroundCheck",
        "inProbation",
        "certifications",
        "education",
        "awards",
        "patents",
        "etc"
    ]
}
```
</details>

### 3. (Optional) Test the script
The custom connector supports two test modes:

* Pull test mode - Tests that the data can be fetched from the Workday report, but does not push the data to Glean.
* Push test mode - Tests that the data can be pushed to Glean, but does not fetch the data from Workday (instead a local .json file is used).

To enable a test mode, set the following environmental variables:

| ENV Name | Value |
| --- | --- |
| `DEBUG_MODE=True` | (Optional) Enable more verbose logging. |
| `TEST_MODE=pull` | Enable **pull** test mode. Data will be fetched from the Workday report URL, but not pushed to Glean. |
| `TEST_MODE=push` | Enable **push** test mode. Data will be loaded from a specific local .json file (instead of being fetched from Workday) and pushed to Glean. |
| `TEST_DATA_FILE=my_sample_data.json` | **For push test mode only:** The local json file to load data from instead of Workday. Must be in the same format as the Workday report output. |

### 4. Run the script

First setup a new virtual Python environment:
```
python3 -m venv venv && source venv/bin/activate
```

Install requirements:
```
pip install -r requirements.txt
```

Run the script:
```
python sync_people.py
```

You can optionally run the script with the `--teamsonly` flag if you are only pushing Teams data to Glean:
```
python sync_people.py --teamsonly
```

### 5. Check output

```
(venv) user@computer workday % python sync_people.py

INFO Jul 26 14:28:56 AEST: Loading mapping file: mapping.json
INFO Jul 26 14:28:56 AEST: Fetching data from Workday: https://wd3-services1.myworkday.com/ccx/service/customreport2/companyname/directory/reportname?format=json
INFO Jul 26 14:28:56 AEST: Transforming Workday data to Glean API format...
INFO Jul 26 14:28:56 AEST: Starting upload of 6 records to the Glean API: https://mycompany-be.glean.com/api/index/v1/bulkindexemployees
INFO Jul 26 14:28:56 AEST: Upload ID: 068a3735-5fad-73b9-8001-b05b146697e1
INFO Jul 26 14:28:56 AEST: Uploaded 6/6 records to Glean API.
INFO Jul 26 14:28:56 AEST: Immediate processing of uploaded data scheduled successfully.
INFO Jul 26 14:28:56 AEST: Data uploaded successfully to Glean API. Total records uploaded: 6
INFO Jul 26 14:28:56 AEST: Please allow 1 hour for the data to be visible in the Glean app.
```

## Warranty/Liability

TL;DR - Examine the code and use this software at your own risk.
This software is licensed under [AGPL 3.0](https://www.gnu.org/licenses/agpl-3.0.html). Specifically for warranty and liability, this means:

```
  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.
```