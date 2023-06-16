## CHANGES in v0.2.11

- Add information, that a role or roles on an user can only be changed by administrator.
- A description has been added to the method add_user which explains how to assign more than one role to the user.
- some test only work on linux development engines ... fix that test also work on windows
- ensure only the fields ['first_name', 'last_name', 'email', 'phone', 'roles'] can be changed on user update
- replace xcube copy/paste failure text with ocdb text
  
## CHANGES in v0.2.10

Requirements for OCDB version 2.2 added
- user update
- user pwd
- sbm status  
  
## CHANGES in v0.2.9

- The client is now using verified SSL connections only.
- Improved help message when changing passwords
- `ocdb-cli user update` is now refusing to change the password. The server will also refuse doing that but only as of
  version 0.1.20. Maybe this feature can be deprecated in future versions.

## CHANGES in v0.2.8

- Sends now information that is it a command line client when logging in 

## CHANGES in v0.2.7

- Improved password encryption
- Config files get now user read only permissions 
- Client is now sending version info to server when logging in to ensure
  that the user uses the correct encryption
- Added new command allowing to get the version general info about the client
- Updated API version to info
- The client is now tied to API version (tag 'v0')

## CHANGES in v0.2.6

- Fixed submission upload: It accepts now not to pass any document files

## CHANGES in v0.2.4:

- upload_submission now accepts single files
- upload submissions accepts now None publication date and false allow_publication
- Added an API function add_submission_file
- Renamed an API function upload_submission_file to update_submission_file
- Renamed option store_path to path when uploading submissions
- Allows now to add a non validating submission file to a submission

## CHANGES in v0.2.3:

- Added api version tag to distinguish between api version and the
  tag used by the api which changed to latest during the maintenance 
  phase
- Changed api version tag to latest

## CHANGES in v0.2.2:

- A user can now add a file to a submission
- The system enforces now the file extension .zip when downloading
  submission or dataset files

## CHANGES in v0.2.1:

- The command line options are more consistent now
- Added a validation command for submission files


## CHANGES in v0.2:

- Pushed project to gitlab.eumetsat.int
- Updated URLs in README to https:ocdb.eumetsat.int
- Updated command reference eocdb-client to ocdb-client in README.md doc