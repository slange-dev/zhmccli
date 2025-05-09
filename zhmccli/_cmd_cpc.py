# Copyright 2016,2019 IBM Corp. All Rights Reserved.
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
Commands for CPCs.
"""


from datetime import datetime, timezone
import json

import click
import yaml
import yamlloader
import zhmcclient
from tabulate import tabulate

from ._helper import print_properties, print_resources, print_list, \
    options_to_properties, original_options, COMMAND_OPTIONS_METAVAR, \
    click_exception, add_options, LIST_OPTIONS, FILTER_OPTIONS, \
    build_filter_args, SORT_OPTIONS, build_sort_props, TABLE_FORMATS, \
    hide_property, required_option, validate, print_dicts, get_level_str, \
    prompt_ftp_password, convert_ec_mcl_description, get_mcl_str, \
    parse_ec_levels, parse_timestamp, TIMESTAMP_BEGIN_DEFAULT, \
    TIMESTAMP_END_DEFAULT
from ._version import __version__
from .zhmccli import cli

POWER_SAVING_TYPES = ['high-performance', 'low-power', 'custom']
DEFAULT_POWER_SAVING_TYPE = 'high-performance'
POWER_CAPPING_STATES = ['disabled', 'enabled', 'custom']

# Data formats of DPM configuration file
DPM_FORMATS = ['yaml', 'json']
DEFAULT_DPM_FORMAT = 'yaml'


# JSON schema for adapter mapping file
MAPPING_SCHEMA = {
    "title": "adapter mapping file schema",
    "description":
        "JSON schema that defines the structure of an adapter mapping file.",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "adapter-mapping"
    ],
    "properties": {
        "adapter-mapping": {
            "description":
                "List of PCHID mappings from config file to import into CPC.",
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "old-adapter-id",
                    "new-adapter-id",
                ],
                "properties": {
                    "old-adapter-id": {
                        "description":
                            "PCHID of adapter in DPM configuration file.",
                        "type": "string"
                    },
                    "new-adapter-id": {
                        "description":
                            "PCHID of adapter when imported into the CPC.",
                        "type": "string"
                    }
                }
            }
        }
    }
}


def help_dpm_file(cmd_ctx, param, value):
    # pylint: disable=unused-argument
    """
    Click callback function for --help-dpm-file option, that displays
    help for the format of the DPM configuration file and exits.
    """
    if not value or cmd_ctx.resilient_parsing:
        return
    print("""
Format of DPM configuration file:

The DPM configuration file contains the properties of a single CPC and all of
its child objects (such as partitions or adapters) and all of its CPC-specific
related objects (such as storage groups associated with the CPC).

The DPM configuration file is written by the 'zhmc cpc dpm-export' command
and read by the 'zhmc cpc dpm-import' command.

The DPM configuration file is in YAML or JSON format and has the structure of
the payload of the 'Import DPM Configuration' operation described in the
HMC API book.

When including any of following properties, remember that the
'zhmc cpc dpm-import' command may overwrite these properties based on the
corresponding options when issuing the 'Import DPM Configuration' operation:

* 'preserve-uris' - Boolean controlling whether to preserve object URIs and IDs.

* 'preserve-wwpns' - Boolean controlling whether to preserve HBA WWPNs.

* 'adapter-mapping' - List of mappings of adapter PCHIDs between the CPC from
  which the DPM configuration was exported and the new CPC to which it is
  imported.
""")
    cmd_ctx.exit()


def help_mapping_file(cmd_ctx, param, value):
    # pylint: disable=unused-argument
    """
    Click callback function for --help-dpm-file option, that displays
    help for the format of the adapter mapping file and exits.
    """
    if not value or cmd_ctx.resilient_parsing:
        return
    print("""
Format of adapter mapping file:

The adapter mapping file specifies how PCHIDs of adapters in a DPM
configuration file need to be replaced when importing the DPM configuration
into a new CPC. If you do not provide a mapping for an adapter, DPM uses a
one-to-one mapping of adapters in the configuration file to adapters on the
target system.

The adapter mapping file is created manually and is read by the
'zhmc cpc dpm-import' command.

The adapter mapping file is in YAML format and has the following structure:

    adapter-mapping:
      - old-adapter-id:  A11  # PCHID in the DPM configuration file
        new-adapter-id: "911" # PCHID in the new system that maps to A11
      - old-adapter-id: "11c"
        new-adapter-id: "12C"
      - ... # More mappings, one for each adapter PCHID you intend to map

The values of the 'old-adapter-id' and 'new-adapter-id' properties are the
PCHID values as a hexadecimal string. Therefore, hexadecimal values that consist
only of decimal digits (like '911' in the example above) must be put into double
quotes. The characters in the hexadecimal string may be in upper or lower case.
""")
    cmd_ctx.exit()


def find_cpc(cmd_ctx, client, cpc_name):
    """
    Find a CPC by name and return its resource object.
    """
    try:
        cpc = client.cpcs.find(name=cpc_name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return cpc


def find_cpc_hwmessage(cmd_ctx, cpc, message_id):
    """
    Find a Hardware messae of a CPC and return its resource object.
    """
    try:
        message = cpc.hw_messages.find(**{'element-id': message_id})
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    return message


@cli.group('cpc', options_metavar=COMMAND_OPTIONS_METAVAR)
def cpc_group():
    """
    Command group for managing CPCs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@cpc_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.option('--type', is_flag=True, required=False, hidden=True)
@click.option('--mach', is_flag=True, required=False, hidden=True)
@add_options(LIST_OPTIONS)
@add_options(FILTER_OPTIONS)
@add_options(SORT_OPTIONS)
@click.pass_obj
def cpc_list(cmd_ctx, **options):
    """
    List the CPCs managed by the HMC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_list(cmd_ctx, options))


@cpc_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--all', is_flag=True, required=False,
              help='Show all properties. Default: Hide some properties in '
              'table output formats')
@click.pass_obj
def cpc_show(cmd_ctx, cpc, **options):
    """
    Show details of a CPC.

    \b
    In table output formats, the following properties are hidden by default
    but can be shown by using the --all option:
      - auto-start-list
      - available-features-list
      - cpc-power-saving-state
      - ec-mcl-description
      - network1-ipv6-info
      - network2-ipv6-info
      - stp-configuration

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_show(cmd_ctx, cpc, options))


@cpc_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--description', type=str, required=False,
              help='The new description of the CPC. '
              '(DPM mode only).')
@click.option('--acceptable-status', type=str, required=False,
              help='The new set of acceptable operational status values, as a '
              'comma-separated list. The empty string specifies an empty list.')
@click.option('--next-activation-profile', type=str, required=False,
              help='The name of the new next reset activation profile. '
              '(not in DPM mode).')
@click.option('--processor-time-slice', type=int, required=False,
              help='The new time slice (in ms) for logical processors. '
              'A value of 0 causes the time slice to be dynamically '
              'determined by the system. A positive value causes a constant '
              'time slice to be used. '
              '(not in DPM mode).')
@click.option('--wait-ends-slice/--no-wait-ends-slice', default=None,
              required=False,
              help='The new setting for making logical processors lose their '
              'time slice when they enter a wait state. '
              '(not in DPM mode).')
@click.pass_obj
def cpc_update(cmd_ctx, cpc, **options):
    """
    Update the properties of a CPC.

    Only the properties will be changed for which a corresponding option is
    specified, so the default for all options is not to change properties.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_update(cmd_ctx, cpc, options))


@cpc_group.command('set-power-save', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--power-saving', type=click.Choice(POWER_SAVING_TYPES),
              required=False, default=DEFAULT_POWER_SAVING_TYPE,
              help='Defines the type of power saving. Default: {pd}'.
              format(pd=DEFAULT_POWER_SAVING_TYPE))
@click.pass_obj
def set_power_save(cmd_ctx, cpc, **options):
    """
    Set the power save settings of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_set_power_save(cmd_ctx, cpc, options))


@cpc_group.command('set-power-capping',
                   options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--power-capping-state', type=click.Choice(POWER_CAPPING_STATES),
              required=True,
              help='Defines the state of power capping.')
@click.option('--power-cap-current', type=int, required=False,
              help='Specifies the current cap value for the CPC in watts (W). '
              'Required if power capping state is enabled.')
@click.pass_obj
def set_power_capping(cmd_ctx, cpc, **options):
    """
    Set the power capping settings of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_set_power_capping(cmd_ctx, cpc,
                                                          options))


@cpc_group.command('get-em-data', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def get_em_data(cmd_ctx, cpc):
    """
    Get all energy management data of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_get_em_data(cmd_ctx, cpc))


@cpc_group.command('dpm-export', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC', required=True)
@click.option('--dpm-file', '-d', metavar='FILE', type=str, required=True,
              help='Path name of the DPM configuration file to be written.')
@click.option('--dpm-format', '-f', type=click.Choice(DPM_FORMATS),
              required=False, default=DEFAULT_DPM_FORMAT,
              help='Controls in which data format the DPM configuration file '
              'is written. Default: {d}.'.format(d=DEFAULT_DPM_FORMAT))
@click.option('--exclude-meta-fields', '-e', is_flag=True, default=False,
              help='Controls whether additional meta information should be '
              'added after a successful export operation, regarding details '
              'of the export operation itself: CPC name, exporting user, '
              'timestamp of export. All corresponding fields are named '
              '"zhmccli-meta-xxx". Default: included')
@click.option('--help-dpm-file', is_flag=True, is_eager=True,
              callback=help_dpm_file, expose_value=False,
              help='Show help on the format of the DPM configuration file '
              'and exit.')
@click.option('--include-unused-adapters', '-i', is_flag=True, default=False,
              help='Controls whether the full set of adapters should be '
              'returned, vs. only those that are referenced by other DPM '
              'objects that are part of the return data. Default: not included')
@click.pass_obj
def dpm_export(cmd_ctx, cpc, **options):
    """
    Export a DPM configuration from a CPC.

    The DPM configuration of the CPC is exported and written to a DPM
    configuration file (in YAML or JSON format). Note: the configuration
    file contains additional meta information, use --exclude-meta-fields in
    case you intend to import the configuration file with other tooling than
    zhmc. For details about the format of that file, use --help-dpm-file.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_dpm_export(cmd_ctx, cpc, options))


@cpc_group.command('dpm-import', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC', required=True)
@click.option('-y', '--yes', is_flag=True,
              help='Skip prompt to confirm import of the DPM configuration.')
@click.option('--dpm-file', '-d', metavar='FILE', type=str, required=True,
              help='Path name of the DPM configuration file to be used.')
@click.option('--dpm-format', '-f', type=click.Choice(DPM_FORMATS),
              required=False, default=DEFAULT_DPM_FORMAT,
              help='Controls in which data format the DPM configuration file '
              'is read. Default: {d}.'.format(d=DEFAULT_DPM_FORMAT))
@click.option('--preserve-uris/--generate-uris',
              'preserve_uris', default=None,
              help='Controls whether existing URIs and IDs of objects in the '
              'DPM configuration file are preserved or ignored and new ones '
              'are generated. If either flag is present, zhmc overwrites any '
              'potential corresponding setting within the configuration data.')
@click.option('--preserve-wwpns/--generate-wwpns',
              'preserve_wwpns', default=None,
              help='Controls whether existing WWPNs of HBAs in the DPM '
              'configuration file are preserved or ignored and new ones '
              'are generated. If either flag is present, zhmc overwrites any '
              'potential corresponding setting within the configuration data.')
@click.option('--mapping-file', '-m', metavar='FILE', type=str, required=False,
              help='Path name of the adapter mapping file to be used. If '
              'present, zhmc overwrites any potential corresponding setting '
              'within the configuration data. Default: Use 1:1 adapter '
              'mapping.')
@click.option('--help-dpm-file', is_flag=True, is_eager=True,
              callback=help_dpm_file, expose_value=False,
              help='Show help on the format of the DPM configuration file '
              'and exit.')
@click.option('--help-mapping-file', is_flag=True, is_eager=True,
              callback=help_mapping_file, expose_value=False,
              help='Show help on the format of the adapter mapping file '
              'and exit.')
@click.pass_obj
def dpm_import(cmd_ctx, cpc, **options):
    """
    Import a DPM configuration into a CPC.

    The DPM configuration of the CPC is read from a DPM configuration file
    (in YAML or JSON format) and imported into the CPC, replacing the current
    DPM configuration of the CPC.
    For details about the format of that file, use --help-dpm-file.

    Optionally, an adapter mapping file (in YAML format) can be specified that
    can be used to accommodate different adapter PCHIDs (plug positions) between
    the CPC represented in the DPM configuration and the CPC targeted for the
    import. By default, the adapters are assumed to be in the same plug
    positions, i.e. the PCHIDs will be unchanged.
    For details about the format of that file, use --help-mapping-file.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    Importing a configuration can potentially result in significant changes to
    the corresponding CPC. To reduce the risk of importing unwanted data,
    this method is more verbose than usual and summarizes the key elements
    of the configuration that is subject to be imported.
    """
    cmd_ctx.execute_cmd(lambda: cmd_dpm_import(cmd_ctx, cpc, options))


@cpc_group.group('autostart', options_metavar=COMMAND_OPTIONS_METAVAR)
def cpc_autostart_group():
    """
    Command group for managing the auto-start list of a CPC (in DPM mode).

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@cpc_autostart_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def cpc_autostart_show(cmd_ctx, cpc):
    """
    Show the auto-start list of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_autostart_show(cmd_ctx, cpc))


@cpc_autostart_group.command('add', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITIONS_DELAY', type=(str, int), metavar='PARTITIONS DELAY')
@click.option('--group', type=str, metavar='GROUP',
              required=False,
              help='Add the partition(s) as a partition group with this name. '
              'Required when adding a group.')
@click.option('--description', type=str, metavar='TEXT',
              required=False,
              help='Description of partition group. '
              'Default: No description.')
@click.option('--before', type=str, metavar='PARTITION_OR_GROUP',
              required=False,
              help='Insert the new partition or group before this '
              'partition/group. '
              'Default: Append new partition or group to the end.')
@click.option('--after', type=str, metavar='PARTITION_OR_GROUP',
              required=False,
              help='Insert the new partition or group after this '
              'partition/group. '
              'Default: Append new partition or group to the end.')
@click.pass_obj
def cpc_autostart_add(cmd_ctx, cpc, partitions_delay, **options):
    """
    Add a partition or group to the auto-start list of a CPC.

    A partition group exists only in context of the auto-start list; it has
    nothing to do with Group objects.

    PARTITIONS is the partition name or a comma-separated list of partition
    names in case of adding a partition group.

    DELAY is the delay afer starting this partition or group, in seconds.

    The updated auto-start list is shown.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_autostart_add(cmd_ctx, cpc, partitions_delay, options))


@cpc_autostart_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('PARTITION_OR_GROUP', type=str, metavar='PARTITION_OR_GROUP')
@click.pass_obj
def cpc_autostart_delete(cmd_ctx, cpc, partition_or_group):
    """
    Delete a partition or group from the auto-start list of a CPC.

    The updated auto-start list is shown.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_autostart_delete(cmd_ctx, cpc, partition_or_group))


@cpc_autostart_group.command('clear', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def cpc_autostart_clear(cmd_ctx, cpc):
    """
    Clear the auto-start list of a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_autostart_clear(cmd_ctx, cpc))


@cpc_group.command('list-api-features', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--name', type=str, metavar='NAME',
              required=False,
              help='A regular expression used to limit returned objects to '
                   'those that have a matching name field.')
@click.pass_obj
def cpc_list_api_features(cmd_ctx, cpc, **options):
    """
    List the Web Services API features available on a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_list_api_features(cmd_ctx, cpc, options))


@cpc_group.command('list-firmware', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def cpc_list_firmware(cmd_ctx, cpc, **options):
    """
    List the firmware level on the Support Element (SE) of a CPC.

    The firmware levels are listed for each EC stream of the SE as MCL levels
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
        lambda: cmd_cpc_list_firmware(cmd_ctx, cpc, options))


@cpc_group.command('upgrade', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--bundle-level', '-b', type=str, required=False,
              help="Name of the bundle to be installed on the SE "
              "(e.g. 'S71'). "
              "Default: When --ftp-host is specified, all code changes on "
              "the FTP server will be installed. Otherwise, all locally "
              "available code changes will be installed.")
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
@click.option('--accept-firmware', '-a', type=bool, required=False,
              default=True,
              help="Boolean indicating to accept the previous bundle level "
              "before installing the new level. Default: true")
@click.option('--timeout', '-T', type=int, required=False, default=1200,
              help='Timeout (in seconds) when waiting for the SE upgrade '
              'to be complete. Default: 1200.')
@click.pass_obj
def cpc_upgrade(cmd_ctx, cpc, **options):
    """
    Upgrade the firmware in a single step on the Support Element (SE) of a CPC.

    This is done by performing the "CPC Single Step Install" operation
    which performs the following steps:

    \b
    * A backup of the target CPC is performed to its SE hard drive.
    * If `accept_firmware` is True, the firmware currently installed on the SE
      of this CPC is accepted. Note that once firmware is accepted, it cannot be
      removed.
    * The new firmware for the specified bundle level is retrieved from the IBM
      support site or from an FTP server. If no bundle level is specified, but
      an FTP server, all firmware available on the FTP server is retrieved.
      If no bundle level is specified and no FTP server, the already locally
      available firmware is used and no additional firmware is retrieved.
    * The specified firmware is installed.
    * The newly installed firmware is activated, which includes rebooting the SE
      of this CPC.

    If an error occurrs when installing the upgrades for the components of
    the new bundle, any components that were successfully installed are
    rolled back.

    If an error occurs after the firmware is accepted, the firmware remains
    accepted.

    Note that it is not possible to downgrade the SE firmware with this
    operation.

    If the SE firmware is already at the requested bundle level, nothing is
    changed and the command succeeds.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_upgrade(cmd_ctx, cpc, options))


@cpc_group.command('install-firmware',
                   options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--bundle-level', '-b', type=str, required=False,
              help="Selects the updates to be installed to be those in a "
              "specific SE bundle (e.g. 'S71'). Disruptive updates will fail.")
@click.option('--ec-levels', '-e', type=str, required=False,
              help="Selects the updates to be installed to be specific EC "
              "levels, as a list in YAML Flow Collection style. "
              "The list items are strings of the form 'EC.MCL' where EC is "
              "the EC number of the EC stream, and MCL is the MCL number "
              "within the EC stream. "
              "Example: --ec-levels \"[P30719.015, P30730.007]\"")
@click.option('--all-concurrent', '-c', is_flag=True, required=False,
              help="Selects the updates to be installed to be all "
              "concurrent (= non-disruptive) updates that are locally "
              "available on the SE.")
@click.option('--all', '-a', is_flag=True, required=False,
              help="Selects the updates to be installed to be all updates "
              "that are locally available on the SE, including disruptive "
              "updates.")
@click.option('--install-disruptive', is_flag=True, required=False,
              help="Install any disruptive updates that are encountered. "
              "Only allowed with --ec-levels. "
              "Default: Fail when encountering disruptive updates.")
@click.option('--timeout', '-T', type=int, required=False, default=1200,
              help='Timeout (in seconds) when waiting for the firmware '
              'installation to be complete. Default: 1200.')
@click.pass_obj
def cpc_install_firmware(cmd_ctx, cpc, **options):
    """
    Install retrieved firmware updates on the Support Element (SE) of a CPC.

    This is done by performing the "CPC Install and Activate" operation
    which performs the following steps:

    \b
    * The specified updates are installed.
    * If all updates are installed successfully, they are activated, which
      includes rebooting the SE.

    The updates to be installed must already be available on the SE; they are
    *not* automatically downloaded from the IBM support site or from an FTP
    server.

    If an error occurs when installing the updates, any updates that were
    successfully installed are rolled back.

    If --bundle-level is specified and the SE firmware is already at the
    requested bundle level, nothing is changed and the command succeeds. For
    the other options to select firmware, it is not currently possible to
    distinguish failure from no need to upgrade, so a failure is reported.

    Notes:

    \b
    * This operation does *not* perform a backup, an accept of previously
      activated updates, or an accept of the newly installed updates.
    * This operation does not require that previously activated updates are
      first accepted before invoking this operation.
    * It is not possible to downgrade the SE firmware with this operation.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_install_firmware(cmd_ctx, cpc, options))


@cpc_group.command('delete-uninstalled-firmware',
                   options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.option('--ec-levels', '-e', type=str, required=False,
              help="Selects the updates to be deleted to be specific EC "
              "levels, as a list in YAML Flow Collection style. "
              "The list items are strings of the form 'EC.MCL' where EC is "
              "the EC number of the EC stream, and MCL is the MCL number "
              "within the EC stream. "
              "Example: --ec-levels \"[P30719.015, P30730.007]\"")
@click.option('--all', '-a', is_flag=True, required=False,
              help="Selects the updates to be deleted to be all retrieved but "
              "uninstalled updates.")
@click.option('--timeout', '-T', type=int, required=False, default=1200,
              help='Timeout (in seconds) when waiting for the deletion of '
              'updates to be complete. Default: 1200.')
@click.pass_obj
def cpc_delete_uninstalled_firmware(cmd_ctx, cpc, **options):
    """
    Delete retrieved but uninstalled firmware updates on the Support Element
    (SE) of a CPC.

    This is done by performing the "CPC Delete Retrieved Internal Code"
    operation which performs the following steps:

    * The specified updates are deleted from the SE.

    Notes:

    \b
    * This operation does *not* perform a backup.
    * It is not possible to delete installed updates with this command.
    * It is not possible to downgrade the SE firmware with this command.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(
        lambda: cmd_cpc_delete_uninstalled_firmware(cmd_ctx, cpc, options))


@cpc_group.group('hw-message', options_metavar=COMMAND_OPTIONS_METAVAR)
def cpc_hwmessage_group():
    """
    Command group for managing Hardware Messages for a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@cpc_hwmessage_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
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
def cpc_hwmessage_list(cmd_ctx, cpc, **options):
    """
    List the Hardware Messages for a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_hwmessage_list(cmd_ctx, cpc, options))


@cpc_hwmessage_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.pass_obj
def cpc_hwmessage_show(cmd_ctx, cpc, message_id):
    """
    Show a Hardware Message for a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_hwmessage_show(
        cmd_ctx, cpc, message_id))


@cpc_hwmessage_group.command('delete', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.pass_obj
def cpc_hwmessage_delete(cmd_ctx, cpc, message_id):
    """
    Delete a Hardware Message for a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_hwmessage_delete(
        cmd_ctx, cpc, message_id))


@cpc_hwmessage_group.command(
    'request-service', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
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
def cpc_hwmessage_request_service(cmd_ctx, cpc, message_id, **options):
    """
    Request service from IBM for a Hardware Message for a CPC and delete the
    hardware message.

    The hardware message's "service-supported" property must be True.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_hwmessage_request_service(
        cmd_ctx, cpc, message_id, options))


@cpc_hwmessage_group.command(
    'get-service-info', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.option('--delete', is_flag=True, required=False,
              help='Controls whether the hardware message will be deleted '
              'upon successful completion of the operation.')
@click.pass_obj
def cpc_hwmessage_get_service_info(cmd_ctx, cpc, message_id, **options):
    """
    Get problem information and a telephone number for requesting service from
    IBM for a hardware message for a CPC and optionally delete the hardware
    message.

    The hardware message's "service-supported" property must be True.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_hwmessage_get_service_info(
        cmd_ctx, cpc, message_id, options))


@cpc_hwmessage_group.command(
    'decline-service', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('message_id', type=str, metavar='MESSAGE_ID')
@click.pass_obj
def cpc_hwmessage_decline_service(cmd_ctx, cpc, message_id):
    """
    Decline service from IBM for a Hardware Message for a CPC and delete
    the hardware message.

    The hardware message's "service-supported" property must be True.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_cpc_hwmessage_decline_service(
        cmd_ctx, cpc, message_id))


def cmd_cpc_list(cmd_ctx, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)

    filter_args = build_filter_args(cmd_ctx, options['filter'])
    try:
        cpcs = client.cpcs.list(filter_args=filter_args)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    if options['type']:
        click.echo("The --type option is deprecated and type information "
                   "is now always shown.")
    if options['mach']:
        click.echo("The --mach option is deprecated and machine information "
                   "is now always shown.")

    show_list = [
        'name',
    ]
    if not options['names_only']:
        show_list.extend([
            'status',
            'dpm-enabled',
            'se-version',
            'machine-type',
            'machine-model',
            'machine-serial-number',
            'description',
        ])
    if options['uri']:
        show_list.extend([
            'object-uri',
        ])

    sort_props = build_sort_props(cmd_ctx, options['sort'], default=['name'])
    try:
        print_resources(cmd_ctx, cpcs, cmd_ctx.output_format, show_list,
                        all=options['all'], sort_props=sort_props)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)


def cmd_cpc_show(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    try:
        cpc.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    properties = dict(cpc.properties)

    # Hide some long or deeply nested properties in table output formats.
    if not options['all'] and cmd_ctx.output_format in TABLE_FORMATS:
        hide_property(properties, 'auto-start-list')
        hide_property(properties, 'available-features-list')
        hide_property(properties, 'cpc-power-saving-state')
        hide_property(properties, 'ec-mcl-description')
        hide_property(properties, 'network1-ipv6-info')
        hide_property(properties, 'network2-ipv6-info')
        hide_property(properties, 'stp-configuration')

    print_properties(cmd_ctx, properties, cmd_ctx.output_format)


def cmd_cpc_update(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name_map = {
        'next-activation-profile': 'next-activation-profile-name',
        'processor-time-slice': None,
        'wait-ends-slice': None,
        'no-wait-ends-slice': None,  # sets 'wait-ends-slice' option
        'acceptable-status': None,
    }
    org_options = original_options(options)
    properties = options_to_properties(org_options, name_map)

    time_slice = org_options['processor-time-slice']
    if time_slice is None:
        # 'processor-running-time*' properties not changed
        pass
    elif time_slice < 0:
        raise click_exception("Value for processor-time-slice option must "
                              "be >= 0", cmd_ctx.error_format)
    elif time_slice == 0:
        properties['processor-running-time-type'] = 'system-determined'
    else:  # time_slice > 0
        properties['processor-running-time-type'] = 'user-determined'
        properties['processor-running-time'] = time_slice

    if org_options['wait-ends-slice'] is not None:
        properties['does-wait-state-end-time-slice'] = \
            org_options['wait-ends-slice']

    if org_options['acceptable-status'] is not None:
        status_list = org_options['acceptable-status'].split(',')
        status_list = [item for item in status_list if item]
        properties['acceptable-status'] = status_list

    if not properties:
        cmd_ctx.spinner.stop()
        click.echo("No properties specified for updating CPC '{c}'.".
                   format(c=cpc_name))
        return

    try:
        cpc.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()

    # Name changes are not supported for CPCs.
    click.echo(f"CPC '{cpc_name}' has been updated.")


def cmd_cpc_set_power_save(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    org_options = original_options(options)
    power_saving = org_options['power-saving']
    cpc.set_power_save(power_saving)
    cmd_ctx.spinner.stop()
    click.echo("The power save settings of CPC '{c}' have been set to {s}.".
               format(c=cpc_name, s=power_saving))


def cmd_cpc_set_power_capping(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    org_options = original_options(options)
    power_capping_state = org_options['power-capping-state']
    power_cap_current = None
    if org_options['power-cap-current']:
        power_cap_current = org_options['power-cap-current']
    cpc.set_power_capping(org_options['power-capping-state'], power_cap_current)
    cmd_ctx.spinner.stop()
    click.echo("The power capping settings of CPC '{c}' have been set to {s}.".
               format(c=cpc_name, s=power_capping_state))


def cmd_cpc_get_em_data(cmd_ctx, cpc_name):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    energy_props = cpc.get_energy_management_properties()
    print_properties(cmd_ctx, energy_props, cmd_ctx.output_format)


def cmd_dpm_export(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    dpm_file = required_option(options['dpm_file'], '--dpm-file')
    dpm_format = options['dpm_format']

    include_unused_adapters = options['include_unused_adapters']

    config_dict = cpc.export_dpm_configuration(include_unused_adapters)
    if not options['exclude_meta_fields']:
        now = datetime.now(timezone.utc)
        config_dict['zhmccli-meta-exported-by'] = cmd_ctx.session.userid
        config_dict['zhmccli-meta-exported-from-cpc-name'] = cpc_name
        config_dict['zhmccli-meta-exported-when'] = f'{now} UTC'
        config_dict['zhmccli-meta-zhmccli-version'] = __version__
        # pylint: disable=no-member
        config_dict['zhmccli-meta-zhmcclient-version'] = zhmcclient.__version__

    try:
        with open(dpm_file, 'w', encoding='utf-8') as fp:
            if dpm_format == 'yaml':
                yaml.dump(config_dict, fp, encoding=None, allow_unicode=True,
                          default_flow_style=False, indent=2,
                          Dumper=yamlloader.ordereddict.CSafeDumper)
            else:
                assert dpm_format == 'json'
                json.dump(config_dict, fp, indent=2, sort_keys=True)
    except OSError as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Exported DPM configuration of CPC '{c}' into DPM config "
               "file {f} in {ff} format.".
               format(c=cpc_name, f=dpm_file, ff=dpm_format.upper()))
    _dump_config(config_dict, 'Export data summary:')


def cmd_dpm_import(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    # process options first, without the spinner running
    cmd_ctx.spinner.stop()

    dpm_file = required_option(options['dpm_file'], '--dpm-file')
    dpm_format = options['dpm_format']
    mapping_file = options['mapping_file']
    preserve_uris = options['preserve_uris']
    preserve_wwpns = options['preserve_wwpns']

    try:
        with open(dpm_file, encoding='utf-8') as fp:
            if dpm_format == 'yaml':
                try:
                    config_dict = yaml.safe_load(fp)
                except (yaml.parser.ParserError, yaml.scanner.ScannerError) \
                        as exc:
                    raise click_exception(
                        "Error parsing DPM configuration file {} in YAML "
                        "format: {}".format(dpm_file, exc),
                        cmd_ctx.error_format)
            else:
                assert dpm_format == 'json'
                try:
                    config_dict = json.load(fp)
                except ValueError as exc:
                    raise click_exception(
                        "Error parsing DPM configuration file {} in JSON "
                        "format: {}".format(dpm_file, exc),
                        cmd_ctx.error_format)
    except OSError as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    # we collect information about the preserve flags, adapter mapping, and
    # meta fields as list of lists, to then print via tabulate()
    summary_info = []
    summary_info.append(_fetch_and_handle_preserve_flag(
        config_dict, 'preserve-uris', preserve_uris, dpm_file))
    summary_info.append(_fetch_and_handle_preserve_flag(
        config_dict, 'preserve-wwpns', preserve_wwpns, dpm_file))
    if mapping_file:
        try:
            with open(mapping_file, encoding='utf-8') as fp:
                try:
                    mapping_obj = yaml.safe_load(fp)
                except (yaml.parser.ParserError, yaml.scanner.ScannerError) \
                        as exc:
                    raise click_exception(
                        "Error parsing adapter mapping file {} in YAML "
                        "format: {}".format(dpm_file, exc),
                        cmd_ctx.error_format)
        except OSError as exc:
            raise click_exception(exc, cmd_ctx.error_format)
    else:
        mapping_obj = None

    summary_info.append(_fetch_and_handle_mapping(
        cmd_ctx, config_dict, mapping_obj, dpm_file, mapping_file))
    summary_info.append([])
    summary_info.extend(_fetch_and_drop_meta_fields(config_dict))
    summary_info.append([])
    click.echo(tabulate(summary_info, [], "plain"))

    _dump_config(config_dict, "Import data summary:")
    cmd_ctx.spinner.stop()

    if not options["yes"]:
        message = ("Are you sure you want to import the DPM configuration "
                   "from {f} into CPC {c}, replacing its current DPM "
                   "configuration?").format(c=cpc_name, f=dpm_file)

        if not click.confirm(message):
            return

    cmd_ctx.spinner.start()

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    result = cpc.import_dpm_configuration(config_dict)

    cmd_ctx.spinner.stop()

    if result:
        click.echo("Partially imported DPM configuration from DPM config file "
                   "{f} into CPC '{c}'. The following parts were not restored:"
                   .format(c=cpc_name, f=dpm_file))
        try:
            print_dicts(cmd_ctx, result['output'], cmd_ctx.output_format)
        except zhmcclient.Error as exc:
            raise click_exception(exc, cmd_ctx.error_format)
    else:
        click.echo("Imported DPM configuration from DPM config file {f} into "
                   "CPC '{c}'.".format(c=cpc_name, f=dpm_file))


def _fetch_and_handle_preserve_flag(config_dict, key, options_field, dpm_file):
    """
    Checks whether key is specified as zhmc option.
    If so, the corresponding value is read and stored within config_dict.
    Returns: list with 2 values (field name and field value with its "source")
    """
    flag = f'{key}:'
    if options_field is not None:
        # zhmc takes precedence over configuration file
        config_dict[key] = bool(options_field)
        return [flag, f'{bool(options_field)} from zhmc option']

    if key in config_dict:
        return [flag, f'{config_dict[key]} from {dpm_file}']

    return [flag, 'False from HMC default']


def _fetch_and_handle_mapping(cmd_ctx, config_dict, mapping_obj,
                              dpm_file, mapping_file):
    """
    Checks whether adapter-mapping is specified as zhmc option.
    If so, the mapping file is read and stored within config_dict.
    Returns: list with 2 values (field name and field value with its "source")
    """
    if mapping_obj:
        # zhmc takes precedence over configuration file
        config_dict['adapter-mapping'] = \
            convert_adapter_mapping(cmd_ctx, mapping_obj)
        return ['adapter-mapping:', f'from {mapping_file}']

    if 'adapter-mapping' in config_dict:
        return ['adapter-mapping:', f'from {dpm_file}']

    return ['adapter-mapping:', '1 to 1 from HMC default']


def _fetch_and_drop_meta_fields(config_dict):
    """
    Prints all dict keys starting with 'zhmccli-' and drops them from the dict.
    Returns: list with value pairs: field name and field value
    """
    summary = []
    for k in sorted(config_dict):
        if k.startswith('zhmccli-'):
            summary.append([f'{k}:', config_dict[k]])
            config_dict.pop(k)
    return summary


def convert_adapter_mapping(cmd_ctx, mapping_obj):
    """
    Convert the adapter mapping from the format used in the adapter mapping file
    to the format needed by the adapter-mapping property in the Import DPM
    Configuration operation.
    """
    try:
        validate(mapping_obj, MAPPING_SCHEMA, "adapter mapping file")
    except ValueError as exc:
        raise click_exception(exc, cmd_ctx.error_format)
    ret_mapping = []
    mapping_list = mapping_obj['adapter-mapping']
    for mapping in mapping_list:
        ret_item = {}
        ret_item['new-adapter-id'] = mapping['new-adapter-id']
        ret_item['old-adapter-id'] = mapping['old-adapter-id']
        ret_mapping.append(ret_item)
    return ret_mapping


def _dump_config(config_dict, message):
    """
    Summarizes the key elements of a dict-based DPM configuration
    """
    counts = []
    values = []
    for k in config_dict:
        v = config_dict[k]
        if isinstance(v, list):
            counts.append((f'{len(v):>3}', k))
        else:
            if isinstance(v, (bool, str)):
                values.append((f'{k}:', v))
    click.echo(message)
    click.echo(tabulate(counts, [], "plain"))
    click.echo(tabulate(values, [], "plain"))


def get_auto_start_list(cpc):
    """
    Helper function that converts the 'auto-start-list' property of a CPC
    to a list suitable for the zhmcclient.Cpc.set_auto_start_list() method.

    Returns:
        None - if the CPC is in classic mode
        list, with items that are one of:
          - tuple(partition, post_start_delay)
          - tuple(partition_list, name, description, post_start_delay)
    """
    auto_start_list = cpc.prop('auto-start-list', None)
    if auto_start_list is None:
        # CPC is in classic mode
        return None

    as_list = []
    for auto_start_item in auto_start_list:
        if auto_start_item['type'] == 'partition':
            # item is a partition
            uri = auto_start_item['partition-uri']
            delay = auto_start_item['post-start-delay']
            partition = cpc.partitions.resource_object(uri)
            as_item = (partition, delay)
            as_list.append(as_item)
        if auto_start_item['type'] == 'partition-group':
            # item is a partition group
            name = auto_start_item['name']
            description = auto_start_item['description']
            delay = auto_start_item['post-start-delay']
            partitions = []
            for uri in auto_start_item['partition-uris']:
                partition = cpc.partitions.resource_object(uri)
                partitions.append(partition)
            as_item = (partitions, name, description, delay)
            as_list.append(as_item)
    return as_list


def auto_start_table_str(as_list, output_format):
    """
    Return a string with the auto-start list table in the specified output
    format.
    """
    headers = ['Partition/Group', 'Post start delay', 'Partitions in group',
               'Group description']
    table = []
    for as_item in as_list:
        if isinstance(as_item[0], zhmcclient.Partition):
            # item is a partition
            partition, delay = as_item
            row = [partition.name, delay]
            table.append(row)
        else:
            # item is a partition group
            partitions, name, description, delay = as_item
            partition_names = ', '.join([p.name for p in partitions])
            row = [name, delay, partition_names, description]
            table.append(row)
    table_str = tabulate(table, headers, tablefmt=output_format)
    return table_str


def cmd_cpc_autostart_show(cmd_ctx, cpc_name):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    as_list = get_auto_start_list(cpc)

    if as_list is None:
        # The HMC WS API book documents that only CPCs in DPM mode have
        # the 'auto-start-list' property.
        cmd_ctx.spinner.stop()
        click.echo("CPC '{c}' is in classic mode and has no auto-start list.".
                   format(c=cpc_name))
        return

    table_str = auto_start_table_str(as_list, cmd_ctx.output_format)
    cmd_ctx.spinner.stop()
    click.echo(table_str)


def cmd_cpc_autostart_add(cmd_ctx, cpc_name, partitions_delay, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    partition_names, delay = partitions_delay

    # pylint: disable=import-outside-toplevel,cyclic-import
    from ._cmd_partition import find_partition

    as_list = get_auto_start_list(cpc)

    if as_list is None:
        # The HMC WS API book documents that only CPCs in DPM mode have
        # the 'auto-start-list' property.
        cmd_ctx.spinner.stop()
        click.echo("CPC '{c}' is in classic mode and has no auto-start list.".
                   format(c=cpc_name))
        return

    group_name = options['group']
    if group_name:
        # A partition group is added (with one or more partitions)
        partition_names = partition_names.split(',')
        partitions = []
        for partition_name in partition_names:
            partition = find_partition(cmd_ctx, client, cpc_name,
                                       partition_name)
            partitions.append(partition)
        description = options['description']
        new_as_item = (partitions, group_name, description, delay)
    else:
        # A partition is added
        partition_name = partition_names
        partition = find_partition(cmd_ctx, client, cpc_name, partition_name)
        new_as_item = (partition, delay)

    # TODO: Add support for --before and --after
    as_list.append(new_as_item)
    try:
        cpc.set_auto_start_list(as_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    table_str = auto_start_table_str(as_list, cmd_ctx.output_format)
    cmd_ctx.spinner.stop()
    click.echo(table_str)


def cmd_cpc_autostart_delete(cmd_ctx, cpc_name, partition_or_group):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    as_list = get_auto_start_list(cpc)

    if as_list is None:
        # The HMC WS API book documents that only CPCs in DPM mode have
        # the 'auto-start-list' property.
        cmd_ctx.spinner.stop()
        click.echo("CPC '{c}' is in classic mode and has no auto-start list.".
                   format(c=cpc_name))
        return

    as_item_idx = None
    for i, as_item in enumerate(as_list):
        if isinstance(as_item[0], zhmcclient.Partition):
            # item is a partition
            partition = as_item[0]
            if partition.name == partition_or_group:
                as_item_idx = i
                break
        else:
            # item is a partition group
            name = as_item[1]
            if name == partition_or_group:
                as_item_idx = i
                break

    if as_item_idx is None:
        raise click_exception(
            "Could not find partition or group '{p}' in CPC '{c}'.'".
            format(p=partition_or_group, c=cpc_name),
            cmd_ctx.error_format)

    del as_list[as_item_idx]
    try:
        cpc.set_auto_start_list(as_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    table_str = auto_start_table_str(as_list, cmd_ctx.output_format)
    cmd_ctx.spinner.stop()
    click.echo(table_str)


def cmd_cpc_autostart_clear(cmd_ctx, cpc_name):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    as_list = []
    try:
        cpc.set_auto_start_list(as_list)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("Auto-start list for CPC '{c}' has been cleared.".
               format(c=cpc_name))


def cmd_cpc_list_api_features(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    name = options['name']
    try:
        features = cpc.list_api_features(name)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    print_list(cmd_ctx, features, cmd_ctx.output_format)


def cmd_cpc_list_firmware(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring,unused-argument

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    cpc.pull_properties('ec-mcl-description')
    ec_mcl = cpc.properties['ec-mcl-description']

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


def cmd_cpc_upgrade(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    console = client.consoles.console

    bundle_level = options['bundle_level']
    accept_firmware = options['accept_firmware']
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
    click.echo("Upgrading the SE of CPC {c} to {lvl}, and waiting for "
               "completion (timeout: {t} s)".
               format(c=cpc_name, lvl=level_str, t=timeout))

    kwargs = dict(
        bundle_level=bundle_level,
        accept_firmware=accept_firmware,
        wait_for_completion=True,
        operation_timeout=timeout)
    if ftp_host:
        kwargs['ftp_host'] = ftp_host
        kwargs['ftp_protocol'] = options['ftp_protocol']
        kwargs['ftp_user'] = ftp_user
        kwargs['ftp_password'] = ftp_password
        kwargs['ftp_directory'] = options['ftp_directory']

    try:
        cpc.single_step_install(**kwargs)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 400 and exc.reason == 356:
            # HMC was already at that bundle level
            cmd_ctx.spinner.stop()
            click.echo("The SE of CPC {c} was already at {lvl} and did not "
                       "need to be upgraded".
                       format(c=cpc_name, lvl=level_str))
            return
        raise click_exception(exc, cmd_ctx.error_format)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The SE of CPC {c} has been upgraded to {lvl}".
               format(c=cpc_name, lvl=level_str))


def cmd_cpc_install_firmware(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    bundle_level = options['bundle_level']
    ec_levels = options['ec_levels']
    all_ = options['all']
    concurrent = options['all_concurrent']
    install_disruptive = options['install_disruptive']
    timeout = options['timeout']

    num_mcl_options = bool(bundle_level) + bool(ec_levels) + all_ + concurrent
    if num_mcl_options != 1:
        raise click_exception(
            "Exactly one option for specifying the firmware to be installed "
            "must be specified, but there were {}".format(num_mcl_options),
            cmd_ctx.error_format)

    if bundle_level and install_disruptive:
        raise click_exception(
            "--install-disruptive and --bundle-level cannot both be specified",
            cmd_ctx.error_format)

    if concurrent and install_disruptive:
        raise click_exception(
            "--install-disruptive and --concurrent cannot both be specified",
            cmd_ctx.error_format)

    if all_ and install_disruptive:
        raise click_exception(
            "--install-disruptive and --all cannot both be specified",
            cmd_ctx.error_format)

    if ec_levels:
        ec_levels_parm = parse_ec_levels(cmd_ctx, '--ec-levels', ec_levels)

    if all_:
        bundle_level = None
        ec_levels_parm = None
        install_disruptive = True

    if concurrent:
        bundle_level = None
        ec_levels_parm = None
        install_disruptive = False

    level_str, dis_str = get_mcl_str(
        bundle_level, ec_levels, all_, concurrent, install_disruptive)
    click.echo("Upgrading the SE of CPC {c} to {lvl}{dis}, and waiting for "
               "completion (timeout: {t} s)".
               format(c=cpc_name, lvl=level_str, dis=dis_str, t=timeout))

    kwargs = dict(
        wait_for_completion=True,
        operation_timeout=timeout,
    )
    if install_disruptive:
        kwargs['install_disruptive'] = True
    if bundle_level:
        kwargs['bundle_level'] = bundle_level
    if ec_levels:
        kwargs['ec_levels'] = ec_levels_parm

    try:
        cpc.install_and_activate(**kwargs)
    except zhmcclient.HTTPError as exc:
        if bundle_level and exc.http_status == 500 and exc.reason == 263:
            # --bundle-level was specified, and the SE was already at the
            # requested bundle level.
            cmd_ctx.spinner.stop()
            click.echo("The SE of CPC {c} was already at {lvl} and did not "
                       "need to be upgraded".
                       format(c=cpc_name, lvl=level_str))
            return
        if ec_levels and exc.http_status == 400 and exc.reason == 379:
            # --ec-levels was specified, but we cannot distinguish failure from
            # the case where the SE was already at the requested EC levels.
            # TODO: Get EC/MCL info and figure out which case it is.
            cmd_ctx.spinner.stop()
            raise click_exception(
                "The SE of CPC {c} either was already at {lvl}, or above "
                "(cannot downgrade), or the firmware is not available on the "
                "SE: HTTPError: {exc}".
                format(c=cpc_name, lvl=level_str, exc=exc),
                cmd_ctx.error_format)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo("The SE of CPC {c} has been upgraded to {lvl}".
               format(c=cpc_name, lvl=level_str))


def cmd_cpc_delete_uninstalled_firmware(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring

    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

    ec_levels = options['ec_levels']
    all_ = options['all']
    timeout = options['timeout']

    num_mcl_options = bool(ec_levels) + all_
    if num_mcl_options != 1:
        raise click_exception(
            "Exactly one option for specifying the firmware to be deleted must "
            "be specified, but there were {}".format(num_mcl_options),
            cmd_ctx.error_format)

    if ec_levels:
        ec_levels_parm = parse_ec_levels(cmd_ctx, '--ec-levels', ec_levels)

    if all_:
        ec_levels_parm = None

    level_str, _ = get_mcl_str(None, ec_levels, all_, None, False)
    click.echo("Deleting {lvl} from the SE of CPC {c}, and waiting for "
               "completion (timeout: {t} s)".
               format(c=cpc_name, lvl=level_str, t=timeout))

    kwargs = dict(
        wait_for_completion=True,
        operation_timeout=timeout,
    )
    if ec_levels:
        kwargs['ec_levels'] = ec_levels_parm

    try:
        cpc.delete_retrieved_internal_code(**kwargs)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    level_str = level_str[0].upper() + level_str[1:]
    click.echo("{lvl} have been deleted from the SE of CPC {c}".
               format(c=cpc_name, lvl=level_str))


def cmd_cpc_hwmessage_list(cmd_ctx, cpc_name, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)

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
        messages = cpc.hw_messages.list(
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


def cmd_cpc_hwmessage_show(cmd_ctx, cpc_name, message_id):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    message = find_cpc_hwmessage(cmd_ctx, cpc, message_id)
    message.pull_full_properties()

    message.update_properties_local({'message-id': message.name})
    message.update_properties_local({'parent-name': cpc.name})
    hmc_ts = message.prop('timestamp')
    dt = zhmcclient.datetime_from_timestamp(hmc_ts)
    dt_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    message.update_properties_local({'timestamp-utc': dt_str})

    cmd_ctx.spinner.stop()
    print_properties(cmd_ctx, message.properties, cmd_ctx.output_format)


def cmd_cpc_hwmessage_delete(cmd_ctx, cpc_name, message_id):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    message = find_cpc_hwmessage(cmd_ctx, cpc, message_id)

    try:
        message.delete()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"Hardware Message '{message.name}' has been deleted.")


def cmd_cpc_hwmessage_request_service(cmd_ctx, cpc_name, message_id, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    message = find_cpc_hwmessage(cmd_ctx, cpc, message_id)

    try:
        message.request_service(**options)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"IBM service for Hardware Message '{message.name}' has been "
               "requested and the message has been deleted.")


def cmd_cpc_hwmessage_get_service_info(cmd_ctx, cpc_name, message_id, options):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    message = find_cpc_hwmessage(cmd_ctx, cpc, message_id)
    delete = options['delete']

    try:
        info = message.get_service_information(delete=delete)
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    print_properties(cmd_ctx, info, cmd_ctx.output_format)
    if delete:
        click.echo(f"Hardware Message '{message.name}' has been deleted.")


def cmd_cpc_hwmessage_decline_service(cmd_ctx, cpc_name, message_id):
    # pylint: disable=missing-function-docstring
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(cmd_ctx, client, cpc_name)
    message = find_cpc_hwmessage(cmd_ctx, cpc, message_id)

    try:
        message.decline_service()
    except zhmcclient.Error as exc:
        raise click_exception(exc, cmd_ctx.error_format)

    cmd_ctx.spinner.stop()
    click.echo(f"IBM service for Hardware Message '{message.name}' has been "
               "declined and the message has been deleted.")
