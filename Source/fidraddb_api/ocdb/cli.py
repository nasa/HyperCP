import json
from typing import Sequence, List, Optional

import click

from ocdb.api import JsonObj, OCDBApi
from ocdb.api.util import DATASET_TYPES
from .version import VERSION, LICENSE_TEXT


def _dump_json(obj: JsonObj):
    print(json.dumps(obj, indent=2))


@click.command()
@click.argument('name', required=False)
@click.argument('value', required=False)
@click.help_option("--help", "-h")
@click.pass_context
def conf(ctx, name, value):
    """
    Configuration management.
    Set configuration parameter NAME to VALUE, display configuration parameter NAME,
    or display all configuration parameters.
    """
    api: OCDBApi = ctx.obj
    if name is not None and value is not None:
        api.set_config_param(name, value, write=True)
    else:
        if name is not None:
            config = {name: api.get_config_param(name)}
        else:
            config = api.config
        _dump_json(config)


def _check_args(ctx, param, value):
    max_num_args = 15
    if len(value) > max_num_args:
        raise click.BadParameter(f"A maximum of {max_num_args} files per upload are allowed.")
    return value


@click.command('upload')
@click.argument('cal-char-files', metavar='<cal-char-file> ...', required=True, nargs=-1, callback=_check_args)
# @click.option('--doc-file', '-d', 'doc_files', metavar='<doc-file>', nargs=1,
#               multiple=True,
#               help="Labels all subsequent files as documentation files")
@click.option('--disagree-publication', '-dp', 'disagree_publication', metavar='<disagree-publication>', is_flag=True,
              help="Specify that you disagree to publish the data")
@click.help_option("--help", "-h")
@click.pass_context
# def upload_cal_char(ctx, cal_char_files: Sequence[str], doc_files: Sequence[str]):
def upload_cal_char(ctx, cal_char_files: Sequence[str], disagree_publication: bool):
    """ Upload fidraddb cal/char files.

    \b
    Please choose max 15 FidRadDB cal/char files.
    The filenames must follow the syntax:
       CP_[class or serial number]_[file type]_[calibrationDate].txt
    """
    api: OCDBApi = ctx.obj
    results = api.fidrad_upload(cal_char_files=cal_char_files,
                                disagree_publication=disagree_publication)
    warn_key = "Warning!"
    warn_lines = None
    if warn_key in results:
        warn_lines = results.pop(warn_key)
    _dump_json(results)
    if warn_lines:
        print()
        print(warn_key)
        print('"' * len(warn_key))
        for line in warn_lines:
            print(line)


@click.command(name="history-tail")
@click.argument('num-lines', default='50')
@click.help_option("--help", "-h")
@click.pass_context
def get_fidrad_history_tail(ctx, num_lines: str):
    """Get history tail from FidRadDb <num_lines> (default 50 lines)."""
    api: OCDBApi = ctx.obj
    result = api.fidrad_history_tail(num_lines)
    if type(result) is list:
        headline = "FidRadDB History Tail"
        num_lines_info = f"({len(result)} lines)"
        print()
        print(headline, num_lines_info)
        print('"' * len(headline))
        for line in result:
            print(line.strip())
        print('"' * len(headline))
        print(headline, num_lines_info)
        print()
    else:
        _dump_json(result)


@click.command(name="history-search")
@click.argument('search-string', required=True)
@click.argument('max-num-lines', default=20)
@click.help_option("--help", "-h")
@click.pass_context
def fidrad_history_search(ctx, search_string: str, max_num_lines):
    """
    Returns a grep-like but bottom-up search result from the FidRadDB history file with a user-defined maximum
    number of result lines.
    :param search_string: The string to be searched for in the history.
    :param max_num_lines: The maximum number of search results.
    """
    api: OCDBApi = ctx.obj
    result = api.fidrad_history_search(search_string, max_num_lines)
    if type(result) is list:
        headline = f"FidRadDB Bottom-Up History Search for '{search_string}'"
        num_lines_info = f"({len(result)} lines)"
        print()
        print(headline, num_lines_info)
        print('"' * len(headline))
        for line in result:
            print(line.strip())
        print('"' * len(headline))
        print(headline, num_lines_info)
        print()
    else:
        _dump_json(result)


@click.command(name="list")
@click.argument('name-part', default='__ALL__')
@click.help_option("--help", "-h")
@click.pass_context
def fidrad_list_files(ctx, name_part: str):
    """
    \b
    Lists the files available on the server.
    If a name-part is specified, only files containing this part are returned.

    :param name_part: The name-part to search for.
    """
    api: OCDBApi = ctx.obj
    result = api.fidrad_list_files(name_part)
    if type(result) is list:
        indent = " " * 4
        headline = "Files on Server"
        print()
        print(indent + headline)
        print(indent + '"' * len(headline))
        result.sort()
        for line in result:
            print(indent + line.strip())
        print()
        print(indent + f"Num files: {len(result)}" + ("" if name_part == "__ALL__" else
                                                      f" ... (filtered by '{name_part}')"))
        print()
    else:
        _dump_json(result)


@click.command(name="delete")
@click.argument('file-name', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def fidrad_delete_file(ctx, file_name: str):
    """
    Will delete the file with the user defined name on the server.
    :param file_name: The name of the file to be deleted
    """
    api: OCDBApi = ctx.obj
    result = api.fidrad_delete_file(file_name)
    _dump_json(result)


@click.command(name="download")
@click.argument('file-name', metavar='<file_name>', required=True)
# @click.option('--output-dir', "-o, default=".")\
@click.option('--output-dir', '-o', metavar='<output_dir>', nargs=1,
              multiple=False, default="'.'", show_default=True,
              help="The directory, to which the file should be written.")
@click.help_option("--help", "-h")
@click.pass_context
def fidrad_download_file(ctx, file_name: str, output_dir: str):
    """
    Will download the file with the user defined name from the server.

    :param file_name: The name of the file to be downloaded.
    """
    api: OCDBApi = ctx.obj
    output_dir = output_dir.replace('\'', '')
    result = api.fidrad_download_file(file_name, output_dir)
    _dump_json(result)


@click.command(name='upload')
@click.argument('path', metavar='<path>', required=True)
@click.argument('dataset-files', metavar='<dataset-file> ...', required=True, nargs=-1)
@click.option('--doc-file', '-d', 'doc_files', metavar='<doc-file>', nargs=1,
              multiple=True,
              help="Labels all subsequent files as documentation files")
@click.option('--submission-id', '-s', 'submission_id', metavar='<submission-id>', nargs=1, required=True,
              help="Give submission ID")
@click.option('--publication-date', '-pd', 'publication_date', metavar='<publication-date>', nargs=1,
              help="set date for publication")
@click.option('--allow-publication', '-ap', 'allow_publication', metavar='<allow-publication>', is_flag=True,
              help="Specify that you agree to publish the data")
@click.help_option("--help", "-h")
@click.pass_context
def upload_submission(ctx, path: str, dataset_files: Sequence[str], doc_files: Sequence[str],
                      submission_id: str, publication_date: str, allow_publication: bool):
    """ Upload submission files."""
    validation_results = ctx.obj.upload_submission(path=path, dataset_files=dataset_files,
                                                   doc_files=doc_files, submission_id=submission_id,
                                                   publication_date=publication_date,
                                                   allow_publication=allow_publication)
    _dump_json(validation_results)


@click.command(name="download")
@click.option('--dataset-id', '-id', help='Specify dataset IDs', multiple=True)
@click.option('--download-docs', '-docs', metavar='<docs>', help='Get docs, too', is_flag=True)
@click.option('--out-file', '-o', metavar='<out-file>', help='Specify name for the outfile (zip)')
@click.help_option("--help", "-h")
@click.pass_context
def download_datasets(ctx, dataset_id: List[str], download_docs: bool, out_file: str):
    """Download dataset files --dataset-id <id> [--dataset-id <id> ...] --download-docs [--out-file <out-file>]."""

    if not dataset_id:
        raise click.ClickException("Please give at least one dataset-id.")

    result = ctx.obj.download_datasets_by_ids(dataset_id, download_docs, out_file)
    print(result)


@click.command(name="get")
@click.option('--id', 'dataset_id', metavar='<id>',
              help='Dataset ID.')
@click.option('--path', '-p', 'dataset_path', metavar='<path>',
              help='Dataset path of the form affil/project/cruise/name.')
@click.help_option("--help", "-h")
@click.pass_context
def get_dataset(ctx, dataset_id: str, dataset_path: str):
    """Get dataset with given <id> or <path>."""
    if (not dataset_id and not dataset_path) or (dataset_id and dataset_path):
        raise click.ClickException("Either <id> or <path> must be given.")
    if dataset_id:
        dataset = ctx.obj.get_dataset(dataset_id)
    else:
        dataset = ctx.obj.get_dataset_by_name(dataset_path)
    _dump_json(dataset)


@click.command(name='find')
@click.option('--expr', metavar='<expr>',
              help="Query expression")
@click.option('--query', metavar='<query>', type=str, multiple=True,
              help='Query the dataset attributes --query <attribute>=<value>. Possible attributes are: '
                   'path, submission_id, user_id, pgroup, pname, pmode')
@click.option('--offset', metavar='<offset>', type=int, default=1,
              help="Results offset. Offset of first result is 1.")
@click.option('--count', metavar='<count>', type=int, default=1000,
              help="Maximum number of results.")
@click.help_option("--help", "-h")
@click.pass_context
def find_datasets(ctx, expr, offset, count, query):
    """Find datasets using query expression <expr>."""

    if not expr and not query:
        raise click.ClickException("Please give either an search keyword or expression --expr or a --query.")

    kwargs = {'expr': expr, 'offset': offset, 'count': count}

    for q in query:
        buffer = q.split('=')
        if len(buffer) == 2:
            buffer = q.split('=')
            kwargs[buffer[0]] = buffer[1]
        else:
            raise click.ClickException("Please use syntax --query field1=value1 --query field2=value2")

    dataset_refs = ctx.obj.find_datasets(**kwargs)
    _dump_json(dataset_refs)


@click.command(name="list")
@click.argument('path', metavar='<path>')
@click.help_option("--help", "-h")
@click.pass_context
def list_datasets(ctx, path):
    """List datasets in <path>."""

    if not path:
        raise click.ClickException("Please give a <path>.")

    dataset = ctx.obj.list_datasets_in_path(path)
    _dump_json(dataset)


# noinspection PyShadowingBuiltins
@click.command(name="del")
@click.argument('id', metavar='<id>')
@click.help_option("--help", "-h")
@click.pass_context
def delete_dataset(ctx, id):
    """Delete dataset given by <id>."""
    if not id:
        raise click.ClickException("Please give an <id>.")
    ctx.obj.delete_dataset(id)


@click.command(name="val")
@click.argument('file', metavar='<file name>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def validate_submission_file(ctx, file):
    """Validate submission <file> before upload."""
    validation_result = ctx.obj.validate_submission_file(file)
    _dump_json(validation_result)


@click.command(name="get-by-sb")
@click.argument('submission-id', metavar='<submission-id>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def get_datasets_by_submission(ctx, submission_id):
    """Get datasets by submission <submission_id>."""
    result = ctx.obj.get_datasets_by_submission(submission_id=submission_id)
    _dump_json(result)


@click.command(name="del-by-sb")
@click.argument('submission-id', metavar='<submission-id>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def delete_datasets_by_submission(ctx, submission_id):
    """Delete datasets by <submission_id>."""
    result = ctx.obj.delete_datasets_by_submission(submission_id=submission_id)
    _dump_json(result)


@click.command(name="get")
@click.argument('submission-id', metavar='<submission-id>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def get_submission(ctx, submission_id: str):
    """Get submission <submission_id>."""
    result = ctx.obj.get_submission(submission_id)
    _dump_json(result)


@click.command(name="user")
@click.argument('user-name', metavar='<user-name>', default=None, required=False)
@click.help_option("--help", "-h")
@click.pass_context
def get_submissions_for_user(ctx, user_name: Optional[str]):
    """Get submissions for user <user_name>."""
    result = ctx.obj.get_submissions_for_user(user_name)
    _dump_json(result)


@click.command(name="delete")
@click.argument('submission-id', metavar='<submission-id>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def delete_submission(ctx, submission_id: str):
    """Delete submission <submission_id>."""
    result = ctx.obj.delete_submission(submission_id)
    _dump_json(result)


@click.command(name="status")
@click.option('--submission-id', '-s', metavar='<submission-id>', help='Specify submission ID', required=True)
@click.option('--status', '-st', metavar='<status>', help='Specify new status', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def update_submission_status(ctx, submission_id: str, status: str):
    """Update submission status --submission-id <submission_id> --status <status>."""
    result = ctx.obj.update_submission_status(submission_id, status)
    _dump_json(result)


@click.command(name="download")
@click.option('--submission-id', '-s', metavar='<submission-id>', help='Specify submission ID', required=True)
@click.option('--index', '-i', metavar='<index>', help='Specify submission file index', required=True)
@click.option('--out-file', '-o', metavar='<out-file>', help='Specify name for the outfile (zip)')
@click.help_option("--help", "-h")
@click.pass_context
def download_submission_file(ctx, submission_id: str, index: int, out_file: str):
    """Get submission file --submission-id <submission-id> --index <index> [--out-file <name>.zip]."""
    result = ctx.obj.download_submission_file(submission_id, index, out_file)
    print(result)


@click.command(name="get")
@click.option('--submission-id', '-s', metavar='<submission-id>', help='Specify submission ID', required=True)
@click.option('--index', '-s', metavar='<index>', help='Specify submission file index', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def get_submission_file(ctx, submission_id: str, index: int):
    """Get submission file --submission_id <submission_id> --index <index>."""
    result = ctx.obj.get_submission_file(submission_id, index)
    print(result)


@click.command(name='update')
@click.option('--file', metavar='<submission-file>', help="Give submission file to re-upload", required=True)
@click.option('--submission-id', '-s', 'submission_id', metavar='<submission-id>', help="Give submission ID",
              required=True)
@click.option('--index', '-i', metavar='<index>', help='Specify submission file index', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def update_submission_file(ctx, submission_id: str, file: str, index: int):
    """Upload multiple dataset and documentation files."""
    validation_results = ctx.obj.update_submission_file(submission_id=submission_id, file_name=file, index=index)
    _dump_json(validation_results)


@click.command(name='add')
@click.option('--file', metavar='<submission-file>', help="Give submission file to re-upload", required=True)
@click.option('--submission-id', '-s', 'submission_id', metavar='<submission-id>', help="Give submission ID",
              required=True)
@click.option('--type', '-t', metavar='<type>', help='Specify type of new submission file',
              type=click.Choice(DATASET_TYPES), required=True)
@click.help_option("--help", "-h")
@click.pass_context
def add_submission_file(ctx, submission_id: str, file: str, type: str):
    """Upload multiple dataset and documentation files."""
    validation_results = ctx.obj.add_submission_file(submission_id=submission_id, file_name=file, typ=type)
    _dump_json(validation_results)


@click.command(name="lic")
def show_license():
    """
    Show license and exit.
    """
    click.echo(LICENSE_TEXT)


# noinspection PyShadowingBuiltins
@click.group()
@click.version_option(VERSION)
@click.option('--server', 'server_url', metavar='<url>', envvar='OCDB_SERVER_URL', help='OCDB Server URL.')
@click.option('--verbose', '-v', metavar='<verbose>', is_flag=True, help='OCDB client verbose reporting',
              required=False)
@click.help_option("--help", "-h")
@click.pass_context
def cli(ctx, server_url: str, verbose: bool):
    """
    EUMETSAT Ocean Color In-Situ Database Client.
    """
    if server_url is not None:
        ctx.obj.server_url = server_url

    if verbose is not None:
        ctx.obj.verbose = verbose


@click.command(name="add")
@click.option('--username', '-u', metavar='<username>', help='Username', required=True)
@click.option('--password', '-p', metavar='<password>', help='Password', required=True)
@click.option('--first-name', '-fn', metavar='<first_name>', help='First Name', default='')
@click.option('--last-name', '-ln', metavar='<last_name>', help='Last Name', default='')
@click.option('--email', '-em', metavar='<email>', help='Email', required=True)
@click.option('--phone', '-ph', metavar='<phone>', help='Phone', default='')
@click.option('--roles', '-r', metavar='<roles>', help='Roles', multiple=True, required=True)
@click.help_option("--help", "-h")
@click.pass_context
def add_user(ctx, username: str, password: str, first_name: str, last_name: str, email: str, phone: str,
             roles: Sequence[str]):
    """
        Add a user

        If you want to add a user with more than one role, use a "-r" option per role.

        Example:

        ocdb-cli user add -u <name> -p <pw> -em <email> -r admin -r submit
    """
    result = ctx.obj.add_user(username=username, password=password, first_name=first_name,
                              last_name=last_name, email=email, phone=phone, roles=roles)
    _dump_json(result)


@click.command(name="update")
@click.option('--username', '-u', metavar='<username>', help='Username', required=True)
@click.option('--key', '-k',
              type=click.Choice(['first_name', 'last_name', 'email', 'phone', 'roles'], case_sensitive=True),
              metavar='<key>', help='Key (e.g. email)', required=True)
@click.option('--value', '-v', metavar='<value>', help='Value for the field. Can be first_name, '
                                                       'last_name, email, phone, roles (admin only)', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def update_user(ctx, username: str, key: str, value: str):
    """Update an existing user"""
    # Todo: Check syntax. What about (username=username, key=key, value=value)?
    result = ctx.obj.update_user(username, key, value)
    _dump_json(result)


@click.command(name="pwd")
@click.argument('username', metavar='<username>', required=False)
@click.option('--password', '-p', metavar='<password>', help='Current password (your password if you are admin)',
              prompt=True, hide_input=True)
@click.option('--new-password', '-p', metavar='<new_password>', help='New password',
              prompt=True, hide_input=True, confirmation_prompt=True)
@click.help_option("--help", "-h")
@click.pass_context
def change_login(ctx, username: str, password: str, new_password: str):
    """Set the password for an existing user."""
    if username is None:
        username = ctx.obj.whoami()['name']
    # Todo: Check syntax. What about (username, key=key, value=value)?
    result = ctx.obj.change_user_login(username=username, password=password, new_password=new_password)
    _dump_json(result)


@click.command(name="login")
@click.option('--username', '-u', metavar='<username>', help='Username', prompt=True)
@click.option('--password', '-p', metavar='<password>', help='Password', prompt=True, hide_input=True)
@click.help_option("--help", "-h")
@click.pass_context
def login_user(ctx, username: str, password: str):
    """Login."""
    # Todo: Check syntax. What about (username=username, password=password)
    result = ctx.obj.login_user(username, password)
    _dump_json(result)


@click.command(name="version")
@click.help_option("--help", "-h")
@click.pass_context
def version(ctx):
    """Get the version of the client."""
    result = ctx.obj.version()
    _dump_json(result)


@click.command(name="info")
@click.help_option("--help", "-h")
@click.pass_context
def info(ctx):
    """Get software infos."""
    result = ctx.obj.info()
    _dump_json(result)


@click.command(name="whoami")
@click.help_option("--help", "-h")
@click.pass_context
def whoami_user(ctx):
    """Get current user."""
    result = ctx.obj.whoami()
    _dump_json(result)


@click.command(name="list")
@click.help_option("--help", "-h")
@click.pass_context
def list_user(ctx):
    """List users."""
    result = ctx.obj.list_user()
    _dump_json(result)


@click.command(name="logout")
@click.help_option("--help", "-h")
@click.pass_context
def logout_user(ctx):
    """Log out current user if logged in."""
    result = ctx.obj.logout_user()
    _dump_json(result)


@click.command(name="get")
@click.argument('username', metavar='<username>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def get_user(ctx, username: str):
    """Get user info of <username>."""
    result = ctx.obj.get_user(username)
    _dump_json(result)


@click.command(name="delete")
@click.argument('username', metavar='<username>', required=True)
@click.help_option("--help", "-h")
@click.pass_context
def delete_user(ctx, username: str):
    """Delete user <username>."""
    result = ctx.obj.delete_user(username)
    _dump_json(result)


@click.group()
@click.help_option("--help", "-h")
def ds():
    """
    Dataset management.
    """


@click.group()
@click.help_option("--help", "-h")
def fidRadDB():
    """
    FidRadDB management
    """


@click.group()
@click.help_option("--help", "-h")
def sbm():
    """
    Submission management.
    """


@click.group()
@click.help_option("--help", "-h")
def sbmfile():
    """
    Submission management.
    """


@click.group()
@click.help_option("--help", "-h")
def df():
    """
    Documentation files management.
    """


@click.group()
@click.help_option("--help", "-h")
def user():
    """
    User management.
    """


cli.add_command(conf)
cli.add_command(ds)
cli.add_command(fidRadDB)
cli.add_command(sbm)
cli.add_command(sbmfile)
cli.add_command(user)
cli.add_command(show_license)
cli.add_command(version)
cli.add_command(info)

# Todo: Check whether cli is correct for the following three methods. Otherwise use user.*?
cli.add_command(whoami_user)
cli.add_command(login_user)
cli.add_command(logout_user)

ds.add_command(find_datasets)
ds.add_command(download_datasets)
ds.add_command(get_dataset)
ds.add_command(delete_dataset)
ds.add_command(list_datasets)
ds.add_command(get_datasets_by_submission)
ds.add_command(delete_datasets_by_submission)

fidRadDB.add_command(upload_cal_char)
fidRadDB.add_command(get_fidrad_history_tail)
fidRadDB.add_command(fidrad_history_search)
fidRadDB.add_command(fidrad_list_files)
fidRadDB.add_command(fidrad_delete_file)
fidRadDB.add_command(fidrad_download_file)

sbm.add_command(update_submission_status)
sbm.add_command(upload_submission)
sbm.add_command(get_submission)
sbm.add_command(get_submissions_for_user)
sbm.add_command(delete_submission)

sbmfile.add_command(download_submission_file)
sbmfile.add_command(update_submission_file)
sbmfile.add_command(add_submission_file)
sbmfile.add_command(validate_submission_file)

user.add_command(add_user)
user.add_command(update_user)
user.add_command(change_login)
user.add_command(get_user)
user.add_command(delete_user)
# Warning: The following three methods are redundant (see cli.*)!
user.add_command(whoami_user)
user.add_command(list_user)
user.add_command(login_user)
user.add_command(logout_user)
