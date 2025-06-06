# Copyright 2022 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Commands for the HMC console.
"""


import click
import dateutil.parser

import zhmcclient
from .zhmccli import cli
from ._helper import print_resources, print_properties, print_dicts, \
    print_list, TABLE_FORMATS, hide_property, COMMAND_OPTIONS_METAVAR, \
    click_exception, get_level_str, prompt_ftp_password, \
    convert_ec_mcl_description, parse_timestamp, TIMESTAMP_BEGIN_DEFAULT, \
    TIMESTAMP_END_DEFAULT


def find_console_hwmessage(cmd_ctx, console, message_id):
    """
    Find a Hardware messae for this HMC and return its resource object.
    """
    try:
        message = console.hw_messages.find(**{'element-id': message_id})
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return message


@cli.group('console', options_metavar=COMMAND_OPTIONS_METAVAR)
def console_group():
    """
    Command group for the HMC console.

    These commands always target the (one) console of the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@console_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--all', is_flag=True, required=False,
              help='Show all properties. Default: Hide some properties in '
              'table output formats')
@click.pass_obj
def console_show(cmd_ctx, **options):
    """
    Show properties of the console of the targeted HMC.

    \b
    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:
      - ec-mcl-description
      - network-info

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_show(cmd_ctx, options))


@console_group.command('restart', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--force', '-f', is_flag=True, required=False,
              help='Perform the restart regardless of whether users are '
              'logged in to the HMC. Users in this sense are local or remote '
              'GUI users. Disconnected GUI users and users at the WS-API do '
              'not count for this.')
@click.option('--wait', '-w', is_flag=True, required=False,
              help='Wait for the HMC to become available again. Note that '
              'any session IDs have become invalid.')
@click.option('--timeout', '-T', type=int, required=False, default=60,
              help='Timeout (in seconds) when waiting for the HMC to become '
              'available again. Default: 60.')
@click.pass_obj
def console_restart(cmd_ctx, **options):
    """
    Restart the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_restart(cmd_ctx, options))


@console_group.command('get-audit-log', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--begin', type=str, required=False,
              help='Begin time for the log, in a format supported by '
              'the python-dateutil package. Default: Earliest available.')
@click.option('--end', type=str, required=False,
              help='End time for the log, in a format supported by '
              'the python-dateutil package. Default: Latest available.')
@click.pass_obj
def get_audit_log(cmd_ctx, **options):
    """
    Get the audit log of the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_get_audit_log(cmd_ctx, options))


@console_group.command('get-security-log',
                       options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--begin', type=str, required=False,
              help='Begin time for the log, in a format supported by '
              'the python-dateutil package. Default: Earliest available.')
@click.option('--end', type=str, required=False,
              help='End time for the log, in a format supported by '
              'the python-dateutil package. Default: Latest available.')
@click.pass_obj
def get_security_log(cmd_ctx, **options):
    """
    Get the security log of the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_get_security_log(cmd_ctx, options))


@console_group.command('list-api-features',
                       options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--name', type=str, metavar='NAME',
              required=False,
              help='A regular expression used to limit returned objects to '
                   'those that have a matching name field.')
@click.pass_obj
def list_api_features(cmd_ctx, **options):
    """
    Lists the Web Services API features available of the console of the
    targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_list_api_features(cmd_ctx, options))


@console_group.command('list-firmware',
                       options_metavar=COMMAND_OPTIONS_METAVAR)
@click.pass_obj
def console_list_firmware(cmd_ctx, **options):
    """
    Lists the firmware levels on the targeted HMC.

    The firmware levels are listed for each EC stream of the HMC as MCL levels
    for different installation states:

    \b
    * retrieved - latest MCL level that has been retrieved
    * installable-conc - latest MCL level that has been retrieved and is
      concurrently installable
    * activated - latest MCL level that has been installed and activated
    * accepted - latest MCL level that has been accepted (= cannot be removed)
    * removable-conc - latest MCL level that has been installed and activated
      and can be removed concurrently (down to latest accepted)

    The MCL levels '0' and '000' are shown as '-' which means there is no such
    level. If a particular installation state is not available, this is shown
    as 'n/a' (but this should not happen).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_console_list_firmware(cmd_ctx, options))


@console_group.command('upgrade', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--bundle-level', '-b', type=str, required=False,
              help="Name of the bundle to be installed on the HMC "
              "(e.g. 'H71'). "
              "Default: When --ftp-host is specified, all code changes on "
              "the FTP server will be installed. Otherwise, all locally "
              "available code changes will be installed.")
@click.option('--backup-location-type', type=str, required=False, default='usb',
              help="Type of backup location for the HMC backup that is "
              "performed: 'ftp': The FTP server that was used for the last "
              "console backup as defined on the 'Configure Backup Settings' "
              "user interface task in the HMC GUI., "
              "'usb': The USB storage device mounted to the HMC.")
@click.option('--accept-firmware', '-a', type=bool, required=False,
              default=True,
              help="Boolean indicating to accept the previous bundle level "
              "before installing the new level. Default: true")
@click.option('--ftp-host', type=str, required=False,
              help="The hostname for the FTP server from which the firmware "
              "will be retrieved. "
              "Default: When --bundle-level is specified, firmware will be "
              "retrieved from the IBM support site. Otherwise, all locally "
              "available code changes will be installed.")
@click.option('--ftp-protocol', type=click.Choice(["sftp", "ftp", "ftps"]),
              required=False, default="sftp",
              help="The protocol to connect to the FTP server, if the firmware "
              "is retrieved from an FTP server. Default: sftp.")
@click.option('--ftp-user', type=str, required=False,
              help="The username for the FTP server login, if the firmware "
              "is retrieved from an FTP server.")
@click.option('--ftp-password', type=str, required=False,
              help="The password for the FTP server login, if the firmware "
              "is retrieved from an FTP server. Specifying a hyphen '-' will "
              "prompt for the password.")
@click.option('--ftp-directory', type=str, required=False,
              help="The path name of the directory on the FTP server with the "
              "firmware files, if the firmware is retrieved from an FTP "
              "server.")
@click.option('--timeout', '-T', type=int, required=False, default=1200,
              help='Timeout (in seconds) when waiting for the HMC upgrade '
              'to be complete. Default: 1200.')
@click.pass_obj
def console_upgrade(cmd_ctx, **options):
    """
    Upgrade the firmware on the targeted HMC to a new bundle level.

    This is done by performing the "Console Single Step Install" operation
    which performs the following steps:

    \b
    * If `accept-firmware` is True, the firmware currently installed on the
      this HMC is accepted. Note that once firmware is accepted, it cannot be
      removed.
    * A backup of the this HMC is performed to the specified backup device.
    * The new firmware for the specified bundle level is retrieved from the IBM
      support site or from an FTP server. If no bundle level is specified, but
      an FTP server, all firmware available on the FTP server is retrieved.
      If no bundle level is specified and no FTP server, the already locally
      available firmware is used and no additional firmware is retrieved.
    * The specified firmware is installed.
    * The newly installed firmware is activated, which includes rebooting this
      HMC.

    Note that it is not possible to downgrade the HMC firmware with this
    operation.

    If the HMC firmware is already at the requested bundle level, nothing is
    changed and the command succeeds.

    For HMCs that run on an HMA that also hosts an SE (e.g. z16 and higher),
    the HMC firmware can only be upgraded if the HMA hosts an alternate SE.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_upgrade(cmd_ctx, options))


@console_group.group('hw-message', options_metavar=COMMAND_OPTIONS_METAVAR)
def console_hwmessage_group():
    """
    Command group for managing Hardware Messages for the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@console_hwmessage_group.command(
    'list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--all', is_flag=True, required=False,
              help='Show all properties.')
@click.option('--service-supported', type=bool, required=False, default=None,
              help='Filter that narrows the list of returned messages to '
              'those with the specified service-supported value. Note: '
              'Dependent on the number of messages, this may take a while.')
@click.option('--begin', type=str, metavar='TIMESTAMP', required=False,
              help='Filter that narrows the list of returned messages to '
              'those created on or after the specified point in time. '
              'Valid formats are HMC timestamp values and most known formats '
              'to represent date and time. An omitted timezone defaults to '
              'UTC. Other omitted fields default to their earliest possible '
              'values. Ambiguous 3-integer dates (e.g. 01/05/09) are '
              'interpreted as M/D/Y.')
@click.option('--end', type=str, metavar='TIMESTAMP', required=False,
              help='Filter that narrows the list of returned messages to '
              'those created on or before the specified point in time. '
              'Valid formats are HMC timestamp values and most known formats '
              'to represent date and time. An omitted timezone defaults to '
              'UTC. Other omitted fields default to their latest possible '
              'values. Ambiguous 3-integer dates (e.g. 01/05/09) are '
              'interpreted as M/D/Y.')
@click.pass_obj
def console_hwmessage_list(cmd_ctx, **options):
    """
    List the Hardware Messages for the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_hwmessage_list(cmd_ctx, options))


@console_hwmessage_group.command(
    'show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.pass_obj
def console_hwmessage_show(cmd_ctx, message_id):
    """
    Show a Hardware Message for the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_hwmessage_show(
        cmd_ctx, message_id))


@console_hwmessage_group.command(
    'delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.pass_obj
def console_hwmessage_delete(cmd_ctx, message_id):
    """
    Delete a Hardware Message for the targeted HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_hwmessage_delete(
        cmd_ctx, message_id))


@console_hwmessage_group.command(
    'request-service', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.option('--customer-name', type=str, required=False,
              help='Name of the person that can be contacted about the '
              'problem. Optional, default is the customer name registered with '
              'IBM for the machine.')
@click.option('--customer-phone', type=str, required=False,
              help='Telephone number of the person that can be contacted '
              'about the problem. Optional, default is the customer phone '
              'registered with IBM for the machine.')
@click.pass_obj
def console_hwmessage_request_service(cmd_ctx, message_id, **options):
    """
    Request service from IBM for a Hardware Message for the targeted HMC and
    delete the hardware message.

    The hardware message's "service-supported" property must be True.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_hwmessage_request_service(
        cmd_ctx, message_id, options))


@console_hwmessage_group.command(
    'get-service-info', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.option('--delete', is_flag=True, required=False,
              help='Controls whether the hardware message will be deleted '
              'upon successful completion of the operation.')
@click.pass_obj
def console_hwmessage_get_service_info(cmd_ctx, message_id, **options):
    """
    Get problem information and a telephone number for requesting service from
    IBM for a hardware message for the targeted HMC and optionally delete the
    hardware message.

    The hardware message's "service-supported" property must be True.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_hwmessage_get_service_info(
        cmd_ctx, message_id, options))


@console_hwmessage_group.command(
    'decline-service', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.pass_obj
def console_hwmessage_decline_service(cmd_ctx, message_id):
    """
    Decline service from IBM for a Hardware Message for the targeted HMC and
    delete the hardware message.

    The hardware message's "service-supported" property must be True.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_console_hwmessage_decline_service(
        cmd_ctx, message_id))


def cmd_console_show(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    try:
        console.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(console.properties)

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'ec-mcl-description')
        hide_property(properties, 'network-info')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_console_restart(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    force = options['force']
    wait = options['wait']
    timeout = options['timeout']

    if wait:
        click.echo("Restarting the HMC and waiting for its availability "
                   "(timeout: {} s)".format(timeout))
    else:
        click.echo("Restarting the HMC")
    try:
        console.restart(force=force, wait_for_available=wait,
                        operation_timeout=timeout)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    if wait:
        click.echo("The HMC has restarted and is available again. Any earlier "
                   "session IDs have become invalid")
    else:
        click.echo("The HMC is currently restarting. Wait for it to be "
                   "available again before issuing any commands. Any earlier "
                   "session IDs will be invalid")


def cmd_get_audit_log(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    begin_time = options['begin'] or None
    if begin_time:
        begin_time = dateutil.parser.parse(begin_time)
    end_time = options['end'] or None
    if end_time:
        end_time = dateutil.parser.parse(end_time)

    try:
        log_items = console.get_audit_log(begin_time, end_time)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'timestamp',
        'event-name',
        'event-id',
        'userid',
        'event-message',
    ]

    ts_additions = {}
    for i, log_item in enumerate(log_items):
        hmc_ts = log_item['event-time']
        dt = zhmcclient.datetime_from_timestamp(hmc_ts)
        ts_additions[i] = str(dt)
    additions = {
        'timestamp': ts_additions,
    }

    cmd_ctx.spinner.stop()
    print_dicts(cmd_ctx, log_items, cmd_ctx.output_format,
                show_list=show_list, additions=additions)


def cmd_get_security_log(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    begin_time = options['begin'] or None
    if begin_time:
        begin_time = dateutil.parser.parse(begin_time)
    end_time = options['end'] or None
    if end_time:
        end_time = dateutil.parser.parse(end_time)

    try:
        log_items = console.get_security_log(begin_time, end_time)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'timestamp',
        'event-name',
        'event-id',
        'userid',
        'event-message',
    ]

    ts_additions = {}
    for i, log_item in enumerate(log_items):
        hmc_ts = log_item['event-time']
        dt = zhmcclient.datetime_from_timestamp(hmc_ts)
        ts_additions[i] = str(dt)
    additions = {
        'timestamp': ts_additions,
    }

    cmd_ctx.spinner.stop()
    print_dicts(cmd_ctx, log_items, cmd_ctx.output_format,
                show_list=show_list, additions=additions)


def cmd_list_api_features(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    name = options['name']
    try:
        features = console.list_api_features(name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_list(cmd_ctx, features, cmd_ctx.output_format)


def cmd_console_list_firmware(cmd_ctx, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    console.pull_properties('ec-mcl-description')
    ec_mcl = console.properties['ec-mcl-description']

    firmware_list = convert_ec_mcl_description(ec_mcl)

    # define order of columns in output table
    show_list = [
        'ec-number',
        'description',
        'retrieved',
        'installable-conc',
        'activated',
        'accepted',
        'removable-conc',
    ]

    print_dicts(cmd_ctx, firmware_list, cmd_ctx.output_format,
                show_list=show_list)


def cmd_console_upgrade(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    bundle_level = options['bundle_level']
    accept_firmware = options['accept_firmware']
    backup_location_type = options['backup_location_type']
    timeout = options['timeout']

    ftp_host = options['ftp_host']
    ftp_user = options['ftp_user']
    ftp_password = options['ftp_password']
    if ftp_host and ftp_password == '-':  # nosec: B105
        ftp_password = prompt_ftp_password(cmd_ctx, ftp_host, ftp_user)

    ec_mcl = console.prop('ec-mcl-description')
    hmc_bundle_level = ec_mcl.get('bundle-level', None)
    if hmc_bundle_level is None:
        hmc_version = console.prop('version')
        raise click_exception(
            "HMC version {v} does not support firmware upgrade through "
            "the Web Services API".format(v=hmc_version),
            cmd_ctx.error_format)

    level_str = get_level_str(bundle_level, ftp_host)
    click.echo("Upgrading the HMC to {lvl}, and waiting for completion "
               "(timeout: {t} s)".
               format(lvl=level_str, t=timeout))

    kwargs = dict(
        bundle_level=bundle_level,
        accept_firmware=accept_firmware,
        backup_location_type=backup_location_type,
        wait_for_completion=True,
        operation_timeout=timeout)
    if ftp_host:
        kwargs['ftp_host'] = ftp_host
        kwargs['ftp_protocol'] = options['ftp_protocol']
        kwargs['ftp_user'] = ftp_user
        kwargs['ftp_password'] = ftp_password
        kwargs['ftp_directory'] = options['ftp_directory']

    try:
        console.single_step_install(**kwargs)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 400 and exc.reason == 356:
            # HMC was already at that bundle level
            cmd_ctx.spinner.stop()
            click.echo("The HMC was already at {lvl} and did not need to be "
                       "upgraded".
                       format(lvl=level_str))
            return
        raise click_exception(exc, cmd_ctx.error_format)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The HMC has been upgraded to {lvl} and is available again. "
               "Any earlier session IDs have become invalid".
               format(lvl=level_str))


def cmd_console_hwmessage_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console

    begin_time = options['begin']
    end_time = options['end']
    service_supported = options['service_supported']

    if begin_time is not None:
        try:
            begin_time = parse_timestamp(begin_time, TIMESTAMP_BEGIN_DEFAULT)
        except (ValueError, OverflowError) as exc:
            raise click_exception(
                f"Invalid begin time: {exc}", cmd_ctx.error_format)
    if end_time is not None:
        try:
            end_time = parse_timestamp(end_time, TIMESTAMP_END_DEFAULT)
        except (ValueError, OverflowError) as exc:
            raise click_exception(
                f"Invalid end time: {exc}", cmd_ctx.error_format)

    filter_args = {}
    if service_supported is not None:
        filter_args['service-supported'] = service_supported

    try:
        messages = console.hw_messages.list(
            filter_args=filter_args,
            begin_time=begin_time,
            end_time=end_time,
        )
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    show_list = [
        'timestamp-utc',
        'message-id',
        'text',
    ]

    ts_additions = {}
    msgid_additions = {}
    for message in messages:
        hmc_ts = message.prop('timestamp')
        dt = zhmcclient.datetime_from_timestamp(hmc_ts)
        ts_additions[message.uri] = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        msgid_additions[message.uri] = message.name
    additions = {
        'timestamp-utc': ts_additions,
        'message-id': msgid_additions,
    }

    try:
        print_resources(cmd_ctx, messages, cmd_ctx.output_format,
                        show_list, additions=additions, all=options['all'])
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_console_hwmessage_show(cmd_ctx, message_id):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    message = find_console_hwmessage(cmd_ctx, console, message_id)
    message.pull_full_properties()

    message.update_properties_local({'message-id': message.name})
    hmc_ts = message.prop('timestamp')
    dt = zhmcclient.datetime_from_timestamp(hmc_ts)
    dt_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    message.update_properties_local({'timestamp-utc': dt_str})

    cmd_ctx.spinner.stop()
    print_properties(cmd_ctx, message.properties, cmd_ctx.output_format)


def cmd_console_hwmessage_delete(cmd_ctx, message_id):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    message = find_console_hwmessage(cmd_ctx, console, message_id)

    try:
        message.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"Hardware Message '{message.name}' has been deleted.")


def cmd_console_hwmessage_request_service(cmd_ctx, message_id, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    message = find_console_hwmessage(cmd_ctx, console, message_id)

    try:
        message.request_service(**options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"IBM service for Hardware Message '{message.name}' has been "
               "requested and the message has been deleted.")


def cmd_console_hwmessage_get_service_info(cmd_ctx, message_id, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    message = find_console_hwmessage(cmd_ctx, console, message_id)
    delete = options['delete']

    try:
        info = message.get_service_information(delete=delete)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    print_properties(cmd_ctx, info, cmd_ctx.output_format)
    if delete:
        click.echo(f"Hardware Message '{message.name}' has been deleted.")


def cmd_console_hwmessage_decline_service(cmd_ctx, message_id):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    console = client.consoles.console
    message = find_console_hwmessage(cmd_ctx, console, message_id)

    try:
        message.decline_service()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"IBM service for Hardware Message '{message.name}' has been "
               "declined and the message has been deleted.")
