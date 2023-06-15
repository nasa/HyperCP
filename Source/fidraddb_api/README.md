[![ocdb-cli](https://github.com/eocdb/ocdb-client/actions/workflows/main.yml/badge.svg)](https://github.com/eocdb/ocdb-client/actions/workflows/main.yml)

# Copernicus Ocean Colour Database (OCDB) Python Client
> Copyright (C) 2019 Copernicus/EUMETSAT  
>
> License: MIT

! keep synchronized with https://gitlab.eumetsat.int/OC/External/OC-DB/ocdb_docs/-/blob/master/docs/source/ocdb-api-cli.md !

## Installation

It is possible to install the CLI and API via conda:

```bash
conda install -c ocdb -c conda-forge ocdb-client

# development installation
# activate conda environment and then:
   $ python -m pip install -e .
```

Once that is done, you can test whether it is running by

```bash
ocdb-cli


Usage: ocdb-cli [OPTIONS] COMMAND [ARGS]...

  EUMETSAT Ocean Color In-Situ Database Client.

Options:
  --version       Show the version and exit.
  --server <url>  OC-DB Server URL.
  --help          Show this message and exit.

Commands:
  conf     Configuration management.
  ds       Dataset management.
  lic      Show license and exit.
  sbm      Submission management.
  sbmfile  Submission management.
  user     User management.
```

## Configure

In order to access the database you need to configure the REST API server address.
The default address is ```https://ocdb.eumetsat.int```.


cli:
```bash
ocdb-cli conf 

https://ocdb.eumetsat.int

ocdb-cli conf server_url [some url]
```

python:
```python
from ocdb.api.OCDBApi import new_api

api = new_api()

api.config

#Out[11]: {'server_url': 'https://ocdb.eumetsat.int'}

api.set_config_param('server_url','[some server url]')

```

## Search Database with the Python API

The method 'find_datasets' allows querying the Database for several information, using different keywords:
- __expr__: looks for any files containing any of the words passed. Also Lucene syntax can be used (See below for more details)
- __region__: looks for files containg measurements collected in the polygon defined by specified coordinates (format: "[West],[South],[East],[North]")
- __start_time__: looks for any files containing measurement collected later than the selected date (format: "2016-07-01")
- __end_time__: looks for any files containing measurement collected earlier than the selected date (format: "2019-07-01")
- __wdepth__: looks for any files containing measurements collected within the defined range of water (bottom) depth (format:"[[min_depth],[max_depth]]")
- __mtype__: filters radiometric data depending on wavelength option. Could be 'all', 'multispectral' or 'hyperspectral'
- __shallow__: set to 'yes' to include also measurements indicated as done in shallow waters by the PIs (Default is 'no')
- __pmode__: can be set either to 'contains' (to filter results based on selected pgroup or variables), or to 'same_cruise' (to include measurements from cruise during which __all__ the selected groups/variables were acquired), or to 'do_not_filter' (to not filter results at all) 
- __pgroup__: looks for files containing only certain geophysical variable types. Refer to [Search](ocdb-search.md) chapter for the complete list
- __pname__: looks for files containing only the specified variables. A complete list of queryable variables are avaialable [here](ocdb-standard-field-unit.md)
- __status__: set to 'PUBLISHED' to get only public available data or to 'PROCESSED' to get both public and not published data (available only for admin users and data owners) 
- __submission_id__: looks for data submitted below the specified submission label
- __geojson__: (Default is True)
- __user_id__: look for data sumbmitted by the specified user (by username)

The results is a dictionary containing information and whole dataset related to the file containing the measurement the satisfied the search criteria.
Dictionary keys are: 
- *total_count*: number of datasets returned by the query
- _datasets_: information about dataset files and the submissions they belong to
- _query_: query parametrization
- *dataset_ids*: ids of the returned datasets

python:
```bash
data = api.find_datasets(region='50,45,51,46')
data['datasets']

  [{'id': '5d97112af9305e0001c6d6fc', 'path': 'LOG/IOPstudy/DS3', 'filename': 'DS3_IOPstudy.csv'}]

```

## Search Database with Lucene syntax

The first example below attempts to find data files that include the name *"Astrid"* in the investigators meta field.


bash:
```bash
ocdb-cli ds find --expr "investigators: *Astrid*"

{
  "locations": {},
  "total_count": 4,
  "datasets": [
    {
      "id": "5d2433e81f59e20001aaae74",
      "path": "AWI/SO/SO235/archive/Bracher_2019_SO235_db.txt"
    },
    ...
```

python:
```python
api.find_datasets(expr="investigators=*Astrid*")

{
  "locations": {},
  "total_count": 4,
  "datasets": [
    {
      "id": "5d2433e81f59e20001aaae74",
      "path": "AWI/SO/SO235/archive/Bracher_2019_SO235_db.txt"
    },
    ...
```

A complete and up-to-date list of the fields that can be queried is available [here](ocdb-search.md)

## Get Datasets

The search engine returns a list of datasets. In order to retrieve the actual data, dataset IDs obtained through the previous step, using cli ds find function and api find_datasets method, should be used. A dataset ID can be used to get actual data as in the example below:

bash:
```bash
ocdb-cli ds get --id 5d971154f9305e0001c6d700
```

python:
```python
api.get_dataset(dataset_id='5d971154f9305e0001c6d700', fmt='pandas')

	      date	    time	     lat	    lon	depth	  ...	 tot_chl_a
0     20140723	12:30:00	-19.9743	57.4493	    0	     	  0.05280
1	  20140723	14:00:00	-19.7216	57.6288	    0		      0.04767
2	  20140723	17:00:00	-19.2121	57.9908	    0		      0.05028
3	  20140723	20:00:00	-18.7211	58.3397	    0             0.04490
4	  20140723	23:00:00	-18.2994	58.7023	    0		      0.07901

...

```

## User Management

__Login User__:

The login procedure will ask for a user name and password. You can specify the password
 as an option. However, under normal circumstances we advice to use the command line prompt.

The example below will login a user with the user name 'scott'. 'scott' is
a 'submitter' user. 'scott', after login, could submit data to the system but he has not have any administrative privileges.

cli:
```bash
ocdb-cli user login --user scott --password tiger
```

python:
```python
api.login_user(username='scott', password='tiger')
```


__Add User__:

To add a user, specify the required user information


cli:
```bash
ocdb-cli user add -u <user_name> -p <password> -fn <user's first name> -ln <user's family name> -em <user's email> -ph <user's phone number> -r <role>
```

python:
```python
api.add_user(username='<user_name>', password='<passwd>', roles=['<role1>, <role2>'])
```

<role1> could be either 'submit' (for any users) or 'admin' (for admin users only).
You need to have administrative access rights to be able to complete this action.


__Get User Information__:

cli:
```bash
ocdb-cli user get --user scott
```

python:
```python
api.get_user(username='scott')
```

You need to have administrative access rights to perform this operation for any user. 
Users can request their own information without restrictions.

__Delete a User__:


cli:
```bash
ocdb-cli user delete --user scott
```

python:
```python
api.delete_user(name='scott')
```
You need to have administrative access rights to be able to complete this action.

__Update an Existing User__:


cli:
```bash
ocdb-cli user update --key <field to be updated> --value <your value>
```

python:
```python
api.update_user(<user_name>, key=<key>, value=<value>)
```

You need to have administrative access rights to perform this operation for any user. 

__Update password__:

Any user can update his own password, after login.

cli:
```bash
ocdb-cli user ownpwd -op <old password> -p <new password>
```

python:
```bash
api.change_user_login(<username>,<old_password>,<new_password>)
```


## Managing Submissions

__Upload a new submission__:
to contribute data trhough a new submission.

cli:
```bash
ocdb-cli sbm upload "<affiliation>/<experiment>/<cruise>" <data files list> -s <submission label> -ap -d <document files list>
```
-ap should be set **only** to allow data be available for the general public

python:
```python
api.upload_submission('<affilition>/<experiment>/<cruise>',dataset_files=('<file_path1>','<file_path2>',...),submission_id='<submission_label>', doc_files=('<file_path1>','<file_path2>',...),[allow_publication = <True/False>],[publication_date = '<yyyy/mm/dd>'])
```
*allow_publication* should be set to True **only** to allow data be available for the general public
*publication_date* should be set only when data can be available for the general public but only after the specified date


__Get Submission__:
to get information for a specific submission

cli:
```bash
ocdb-cli sbm get IOPstudy2
```

python:
```python
api.get_submission('IOPstudy2')
```

You need to have administrative access rights to perform this operation for any submission. 
Users can monitor their own submissions without restrictions.

__Get Submissions for a specific User__:


cli:
```bash
ocdb-cli sbm user scott
```

python:
```python
api.get_submissions_for_user('scott')
```

You need to have administrative access rights to perform this operation for any submission. 
Users can monitor their own submissions without restrictions.


__Delete Submission__:


cli:
```bash
ocdb-cli sbm delete <submission-id>
```

python:
```python
api.delete_submission(<submission-id>)
```
You need to have administrative access rights to perform this operation for any submission. 
Users can delete their own submissions without restrictions.


__Update Submission Status__:

This command allows to manipulate the status assigned to any submission. Some status changes will have impact on
whether the data are searchable or not in the Database.

The following list shows the different stati and the impact on the accessibility when changing them:

- SUBMITTED: A dataset has been submitted. Usually also means that the data has issues. This will trigger
  the automated validation process
- VALIDATED: The data has been submitted and passed the quality checks (even in case any warning was raised)
- PROCESSED: The data has been processed into the database and is searchable, but only by admin users and the user who submetted it
- PUBLISHED: The data has been processed into the database and is publicly available
- CANCELED: The data submission has been canceled. Setting this status will remove the data from the database and will
  not be findable anymore. It can be still reprocessed again into the Database
- PAUSED: The user paused the submission. This indicates that the admin users shall not publish or process the data

cli:
```bash
ocdb-cli sbm status --submission-id <submission-id> --status <status>
```


python
```python
api.update_submission_status(<submission-id>, <status>)
```

You need to have administrative access rights to perform this operation for any submission. 
Users can submit, cancel and pause their own submissions without restrictions.


__Download Submission File__:


This command will download a single submission file. Please be aware that the **version of the file is the one of the submission
status**. Do not use this feature to download data, instead use the "get_dataset" function of the API.

cli:
```bash
ocdb-cli sbmfile download -s <submission_label> --index <index> [--out-file <file_name>]
```

By default files are downloaded as 'download.zip'

python
```python
api.download_submission_file(<submission_label>,<index>, out_fn =  <file_name>)
```


__Upload Submission File__:


Both measurement and documentation files can be added to **an existing submission**


cli:
```bash
ocdb-cli sbmfile add --submission-id <submission_label> --file <local_file_path>  -t <type>
```

python
```python
api.add_submission_file(<submission_label>,<local_file>,<type>)
```
where _type_ could be 'MEASUREMENT' or 'DOCUMENT'


Both **existing measurement and documentation files** can be added to updated, replacing them with a new file from local.

cli:
```bash
ocdb-cli sbmfile update --submission-id <submission_label> --file <local_file_path>  --index <index>
```

python
```python
api.update_submission_file(<submission_label>,<local_file>,<index>)
```

where *index* is the index of the file in the submission to be updated.


Users can update their own submission files without restrictions.


## General

__Get License__


```bash
ocdb-cli lic
```

## Development

### Testing

    $ pytest --cov=ocdb_client --cov-report html
