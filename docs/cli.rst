.. Copyright 2016,2019 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`Command line interface`:

Command line interface
======================

This package provides a command line interface (CLI) that utilizes the API of
the zhmcclient package in order to support shell scripting or simply manual
command use in a terminal session.


.. _`Modes of operation`:

Modes of operation
------------------

The zhmc CLI supports two modes of operation:

* `Interactive mode`_: Invoking an interactive zhmc shell for typing zhmc
  sub-commands.
* `Command mode`_: Using it as a standalone non-interactive command.


.. _`Interactive mode`:

Interactive mode
----------------

In interactive mode, an interactive shell environment is brought up that allows
typing zhmc commands, internal commands (for operating the zhmc shell), and
external commands (that are executed in the standard shell for the user).

This zhmc shell is started when the ``zhmc`` command is invoked without
specifying any (sub-)commands:

.. code-block:: text

    $ zhmc [GENERAL-OPTIONS]
    > _

Alternatively, the zhmc shell can also be started by specifying the ``repl``
(sub-)command:

.. code-block:: text

    $ zhmc [GENERAL-OPTIONS] repl
    > _

The zhmc shell uses the ``>`` prompt, and the cursor is shown in the examples
above as an underscore ``_``.

General options may be specified on the ``zhmc`` command, and they serve as
defaults for the zhmc commands that can be typed in the zhmc shell.

The zhmc commands that can be typed in the zhmc shell are simply the command
line arguments that would follow the ``zhmc`` command when used in
`command mode`_:

.. code-block:: text

    $ zhmc -h zhmc.example.com -u hmcuser
    Enter password: <password>
    > cpc list
    . . . <list of CPCs managed by this HMC>
    > partition list JLSE1
    . . . <list of partitions in CPC JLSE1>
    > :q

For example, the zhmc shell command ``cpc list`` in the example above has the
same effect as the standalone command:

.. code-block:: text

    $ zhmc -h zhmc.example.com -u hmcuser cpc list
    Enter password: <password>
    . . . <list of CPCs managed by this HMC>

However, the zhmc shell will prompt for a password only once during its
invocation, while the standalone command will prompt for a password every time.
See also `Environment variables and avoiding password prompts`_.

The internal commands ``:?``, ``:h``, or ``:help`` display general help
information for external and internal commands:

.. code-block:: text

    > :help
    REPL help:

      External Commands:
        prefix external commands with "!"

      Internal Commands:
        prefix internal commands with ":"
        :?, :h, :help     displays general help information
        :exit, :q, :quit  exits the repl

In this help text, "REPL" stands for "Read-Execute-Print-Loop" which is a
term that denotes the approach used in the zhmc shell (or in any shell, for
that matter).

In addition to using one of the internal shell commands shown in the help text
above, you can also exit the zhmc shell by typing `Ctrl-D`.

Typing ``--help`` in the zhmc shell displays general help information for the
zhmc commands, which includes global options and a list of the supported
commands:

.. code-block:: text

    > --help
    Usage: zhmc  [OPTIONS] COMMAND [ARGS]...

      Command line interface for the IBM Z HMC.
      . . .

    Options:
      -h, --host TEXT                 Hostname or IP address of the HMC (Default:
                                      ZHMC_HOST environment variable).
      -u, --userid TEXT               Username for the HMC (Default: ZHMC_USERID
                                      environment variable).
      -p, --password TEXT             Password for the HMC (Default: ZHMC_PASSWORD
                                      environment variable).
      -n, --no-verify                 Do not verify the HMC certificate. (Default:
                                      ZHMC_NO_VERIFY environment variable, or
                                      verify the HMC certificate).
      -c, --ca-certs TEXT             Path name of certificate file or directory
                                      with CA certificates to be used for
                                      verifying the HMC certificate. (Default:
                                      Path name in ZHMC_CA_CERTS environment
                                      variable, or path name in REQUESTS_CA_BUNDLE
                                      environment variable, or path name in
                                      CURL_CA_BUNDLE environment variable, or the
                                      'certifi' Python package which provides the
                                      Mozilla CA Certificate List).
      -o, --output-format [[table|plain|simple|psql|rst|mediawiki|html|latex|
                          json]]
                                      Output format (Default: table).
      -x, --transpose                 Transpose the output table for metrics.
      -e, --error-format [msg|def]    Error message format (Default: msg).
      -t, --timestats                 Show time statistics of HMC operations.
      --log COMP=LEVEL,...            Set a component to a log level
                                      (COMP: [api|hmc|console|all],
                                       LEVEL: [error|warning|info|debug],
                                       Default: all=warning).
      --log-dest [stderr|syslog|none]
                                      Log destination for this command (Default:
                                      stderr).
      --syslog-facility [user|local0|local1|local2|local3|local4|local5|local6|local7]
                                      Syslog facility when logging to the syslog
                                      (Default: user).
      --version                       Show the versions of this command and of the
                                      zhmcclient package and exit.
      --help                          Show this message and exit.

    Commands:
      adapter           Command group for managing adapters (DPM mode only).
      capacitygroup     Command group for managing capacity groups.
      cpc               Command group for managing CPCs.
      hba               Command group for managing HBAs (DPM mode only).
      help              Show help message for interactive mode.
      info              Show information about the HMC.
      lpar              Command group for managing LPARs (classic mode only).
      metrics           Command group for reporting metrics.
      nic               Command group for managing NICs (DPM mode only).
      partition         Command group for managing partitions (DPM mode only).
      passwordrule      Command group for managing HMC password rules.
      port              Command group for managing adapter ports (DPM mode only).
      repl              Enter interactive (REPL) mode (default).
      session           Command group for managing sessions.
      storagegroup      Command group for managing storage groups (DPM mode only).
      storagevolume     Command group for managing storage volumes (DPM mode only).
      user              Command group for managing HMC users.
      userrole          Command group for managing HMC user roles.
      vfunction         Command group for managing virtual functions (DPM mode only).
      vstorageresource  Command group for managing virtual storage resources (DPM mode only).
      vswitch           Command group for managing virtual switches (DPM mode only).

The usage line in this help text show the standalone command use. Within the
zhmc shell, the ``zhmc`` word is ommitted and the remainder is typed in.

Typing ``COMMAND --help`` in the zhmc shell displays help information for the
specified zhmc command, for example:

.. code-block:: text

    > cpc --help
    Usage: zhmc  cpc [OPTIONS] COMMAND [ARGS]...

      Command group for managing CPCs.

    Options:
      --help  Show this message and exit.

    Commands:
      list  List the CPCs.
      show  Show details of a CPC.

The zhmc shell supports popup help text while typing, where the valid choices
are shown based upon what was typed so far, and where an item from the popup
list can be picked with <TAB> or with the cursor keys. In the following
examples, an underscore ``_`` is shown as the cursor:

.. code-block:: text

    > --_
        --host            Hostname or IP address of the HMC (Default: ZHMC_HOST environment variable).
        --userid          Username for the HMC (Default: ZHMC_USERID environment variable).
        --password        Password for the HMC (Default: ZHMC_PASSWORD environment variable).
        --no-verify       Do not verify the HMC certificate. (Default: ZHMC_NO_VERIFY ...
        --ca-certs        Path name of certificate file or directory with CA certificates ...
        --output-format   Output format (Default: table).
        --transpose       Transpose the output table for metrics.
        --error-format    Error message format (Default: msg).
        --timestats       Show time statistics of HMC operations.
        --log             Set a component to a log level (COMP: [api|hmc|console|all], LEVEL: [error|warning|info|debug], Default: all=warning).
        --log-dest        Log destination for this command (Default: stderr).
        --syslog-facility Syslog facility when logging to the syslog (Default: user).
        --version         Show the version of this command and exit.

    > c_
       cpc    Command group for managing CPCs.

The zhmc shell supports history (within one invocation of the shell, not
persisted across zhmc shell invocations).


.. _`Command mode`:

Command mode
------------

In command mode, the ``zhmc`` command performs its task and terminates, like any
other standalone non-interactive command.

This mode is used when the ``zhmc`` command is invoked with a (sub-)command:

.. code-block:: text

    $ zhmc [GENERAL-OPTIONS] COMMAND [ARGS...] [COMMAND-OPTIONS]

Examples:

.. code-block:: text

    $ zhmc -h zhmc.example.com -u hmcuser cpc list
    Enter password: <password>
    . . . <list of CPCs managed by this HMC>

    $ zhmc -h zhmc.example.com info
    Enter password: <password>
    . . . <information about this HMC>

In command mode, bash tab completion is also supported, but must be enabled
first as follows (in a bash shell):

.. code-block:: text

    $ eval "$(_ZHMC_COMPLETE=source zhmc)"

Bash tab completion for zhmc is used like any other bash tab completion:

.. code-block:: text

    $ zhmc --<TAB><TAB>
    ... <shows the global options to select from>

    $ zhmc <TAB><TAB>
    ... <shows the commands to select from>

    $ zhmc cpc <TAB><TAB>
    ... <shows the cpc sub-commands to select from>



Running in a Docker container
-----------------------------

If you want to run the zhmc command in a Docker container instead of installing
it into a Python environment, you can create the container as follows, using
the Dockerfile provided in the Git repository.

* Clone the Git repository and switch to the clone's root directory:

  .. code-block:: bash

      $ git clone https://github.com/zhmcclient/zhmccli
      $ cd zhmccli

* Build a local Docker image as follows:

  .. code-block:: bash

      $ make docker

  This builds a container image named ``zhmc:latest`` in your local Docker
  environment.

* Run the local Docker image as follows to get help for the zhmc command:

  .. code-block:: bash

      $ docker run --rm zhmc

When running it in the container, the zhmc command cannot be used in
:ref:`interactive mode`.


.. _`Environment variables and avoiding password prompts`:

Environment variables and avoiding password prompts
---------------------------------------------------

The zhmc CLI has command line options for specifying the HMC host, userid and
password to be used.

If the HMC operations performed by a particular zhmc command require a
password, and the password is not specified otherwise, the password is prompted
for (in both modes of operation):

.. code-block:: text

    $ zhmc -h zhmc.example.com -u hmcuser cpc list
    Enter password: <password>
    . . . <list of CPCs managed by this HMC>

If the HMC operations performed by a particular zhmc command do not require a
password, no password is prompted for:

.. code-block:: text

    $ zhmc -h zhmc.example.com info
    . . . <information about this HMC>

For script integration, it is important to have a way to avoid the interactive
password prompt, and still not being forced to specify the password on the
command line. This can be done in either of two ways:

* by storing the session-id string returned by the HMC when logging on, in an
  environment variable.

  The ``zhmc`` command supports a ``session create`` (sub-)command that outputs
  the (bash) shell commands to set all needed environment variables:

  .. code-block:: text

      $ zhmc -n -h zhmc.example.com -u acsadmin session create
      Enter password: <password>
      export ZHMC_HOST=zhmc.example.com
      export ZHMC_USERID=acsadmin
      export ZHMC_SESSION_ID=<session-id>
      export ZHMC_NO_VERIFY=TRUE
      unset ZHMC_CA_CERTS

  Note that the ``-n`` option is used to make this command work for
  demonstration purposes regardless of the actual HMC certificate setup. It is
  not recommended to use this option in production environments.
  See :ref:`Using HMC certificates` for details.

  This ability can be used to set those environment variables and thus to
  persist the session-id in the shell environment, from where it will be used
  in any subsequent zhmc commands:

  .. code-block:: text

      $ eval $(zhmc -n -h zhmc.example.com -u acsadmin session create)
      Enter password: <password>

      $ env |grep ZHMC
      ZHMC_HOST=zhmc.example.com
      ZHMC_USERID=acsadmin
      ZHMC_SESSION_ID=<session-id>
      ZHMC_NO_VERIFY=TRUE

      $ zhmc cpc list
      . . . <list of CPCs managed by this HMC>

  As you can see from this example, the password is only prompted for when
  creating the session, and the session-id stored in the shell environment is
  utilized in the ``zhmc cpc list`` command, avoiding another password prompt.

  Using the session-id from the environment is also a performance improvement,
  because it avoids the HMC Logon operation that otherwise would take place.

* by storing the HMC password in the ``ZHMC_PASSWORD`` environment variable.

The ``ZHMC_HOST``, ``ZHMC_USERID``, ``ZHMC_PASSWORD``, ``ZHMC_NO_VERIFY``, and
``ZHMC_CA_CERTS`` environment variables act as defaults for the corresponding
command line options.


.. _`Using HMC certificates`:

Using HMC certificates
----------------------

By default, the HMC is configured with a self-signed certificate. That is the
X.509 certificate presented by the HMC as the server certificate during SSL/TLS
handshake at its Web Services API.

Starting with version 0.22, the 'zhmc' command will reject self-signed
certificates by default.

The HMC should be configured to use a CA-verifiable certificate. This can be
done in the HMC task "Certificate Management". See also the :term:`HMC Security`
book and Chapter 3 "Invoking API operations" in the :term:`HMC API` book.

Starting with version 0.22, the zhmc command provides control knobs for the
verification of the HMC certificate via the ``-c`` / ``--ca-certs`` and
``-n`` / ``--no-verify`` command line options, as follows:

* None of the two options specified (default): Verify the HMC certificate using
  the CA certificates from the first of these locations:

  - The certificate file or directory in the ``ZHMC_CA_CERTS`` environment
    variable, if set
  - The certificate file or directory in the ``REQUESTS_CA_BUNDLE`` environment
    variable, if set
  - The certificate file or directory in the ``CURL_CA_BUNDLE`` environment
    variable, if set
  - The `Python 'certifi' package <https://pypi.org/project/certifi/>`_
    (which contains the
    `Mozilla Included CA Certificate List <https://wiki.mozilla.org/CA/Included_Certificates>`_).

* ``-c`` / ``--ca-certs`` specified: Verify the HMC certificate using the CA
  certificates in the specified certificate file or directory.

* ``-n`` / ``--no-verify`` specified or ``ZHMC_NO_VERIFY`` environment variable
  set: Do not verify the HMC certificate. Not verifying the HMC certificate
  means that hostname mismatches, expired certificates, revoked certificates,
  or otherwise invalid certificates will not be detected. Since this mode makes
  the connection vulnerable to man-in-the-middle attacks, it is insecure and
  should not be used in production environments.

If a certificate file is specified (using any of the ways listed above), that
file must be in PEM format and must contain all CA certificates that are
supposed to be used. Usually they are in the order from leaf to root, but
that is not a hard requirement. The single certificates are concatenated
in the file.

If a certificate directory is specified (using any of the ways listed above),
it must contain PEM files with all CA certificates that are supposed to be used,
and copies of the PEM files or symbolic links to them in the hashed format
created by the OpenSSL command ``c_rehash``.

An X.509 certificate in PEM format is base64-encoded, begins with the line
``-----BEGIN CERTIFICATE-----``, and ends with the line
``-----END CERTIFICATE-----``.
More information about the PEM format is for example on this
`www.ssl.com page <https://www.ssl.com/guide/pem-der-crt-and-cer-x-509-encodings-and-conversions>`_
or in this `serverfault.com answer <https://serverfault.com/a/9717/330351>`_.

Note that setting the ``REQUESTS_CA_BUNDLE`` or ``CURL_CA_BUNDLE`` environment
variables influences other programs that use these variables, too.

For more information, see the
`Security <https://python-zhmcclient.readthedocs.io/en/latest/security.html>`_
section in the documentation of the 'zhmcclient' package.


.. _`CLI commands`:

CLI commands
------------

For a description of the commands supported by the zhmc CLI, consult its
help system. For example:

.. code-block:: text

    $ zhmc --help
    . . . <general help, listing the general options and possible commands>

    $ zhmc cpc --help
    . . . <help for cpc command, listing its arguments and command-specific options>

Note that the help text for any zhmc (sub-)commands (such as ``cpc``) will
not show the general options again. This is caused by flaws in the tooling
environment used for the zhmc CLI.
The general options (listed by ``zhmc --help``) can still be specified together
with (sub-)commands even though they are not listed in their help text, but
they must be specified before the (sub-)command, and any command-specific
options (listed by ``zhmc COMMAND --help``) must be specified after the
(sub-)command, like shown here:

.. code-block:: text

      $ zhmc [GENERAL-OPTIONS] COMMAND [ARGS...] [COMMAND-OPTIONS]


.. _`Resource properties`:

Resource properties
-------------------

The properties of any resources (e.g. CPC or partition) are shown in any output
using the names and units documented in the HMC WS API book.

Some of the commands have additional help options to explain output that is not
documented in the HMC WS API book. For example, ``partition list`` command
has a ``--help-usage`` option that explains the output of the usage-related
options ``--memory-usage``, ``--ifl-usage`` and ``--cp-usage``.


.. _`Output formats`:

Output formats
--------------

The zhmc CLI supports various output formats for the results. The output format
can be selected with the ``-o`` or ``--output-format`` option. The following
output formats are supported:

* ``-o table``: Tables with a single-line border. This is the default:

  .. code-block:: text

      +----------+------------------+
      | name     | status           |
      |----------+------------------|
      | P0000P27 | operating        |
      | P0000P28 | service-required |
      | P0ZGMR12 | no-power         |
      +----------+------------------+

* ``-o psql``: Same as 'table'.

* ``-o simple``: Tables with a line between header row and data rows, but
  otherwise without borders:

  .. code-block:: text

      name      status
      --------  ----------------
      P0000P27  operating
      P0000P28  service-required
      P0ZGMR12  no-power

* ``-o plain``: Tables without borders:

  .. code-block:: text

      name      status
      P0000P27  operating
      P0000P28  service-required
      P0ZGMR12  no-power

* ``-o rst``: Simple tables in `reStructuredText`_ markup:

  .. code-block:: text

      ========  ================
      name      status
      ========  ================
      P0000P27  operating
      P0000P28  service-required
      P0ZGMR12  no-power
      ========  ================

* ``-o mediawiki``: Tables in `Mediawiki`_ markup:

  .. Note: The 'moin' language in the following code-block is used because
  .. Pygments does not specifically support the MediaWiki language.

  .. code-block:: moin

      {| class="wikitable" style="text-align: left;"
      |+ <!-- caption -->
      |-
      ! name     !! status
      |-
      | P0000P27 || operating
      |-
      | P0000P28 || service-required
      |-
      | P0ZGMR12 || no-power
      |}

* ``-o html``: Tables in `HTML`_ markup:

  .. code-block:: html

      <table>
      <thead>
      <tr><th>name    </th><th>status          </th></tr>
      </thead>
      <tbody>
      <tr><td>P0000P27</td><td>operating       </td></tr>
      <tr><td>P0000P28</td><td>service-required</td></tr>
      <tr><td>P0ZGMR12</td><td>no-power        </td></tr>
      </tbody>
      </table>

* ``-o latex``: Tables in `LaTeX`_ markup:

  .. code-block:: latex

      \begin{tabular}{ll}
      \hline
       name     & status           \\
      \hline
       P0000P27 & operating        \\
       P0000P28 & service-required \\
       P0ZGMR12 & no-power         \\
      \hline
      \end{tabular}

* ``-o json``: `JSON`_ objects:

  .. code-block:: json

      [{"name": "P0000P28", "status": "service-required"},
       {"name": "P0ZGMR12", "status": "no-power"},
       {"name": "P0000P27", "status": "operating"}]

* ``-o csv``: CSV spreadsheet format:

  The generated CSV output has a header line with the names of the fields and
  uses double quote (``"``) as the quote character and comma (``,``) as the
  field delimiter character.

  Which values are quoted in the CSV output depends on the Python version that
  is used.

  * On Python 3.13 and later:

    - ``None`` will not be quoted in the CSV output and thus appears as an
      unquoted empty string.
    - ``int``, ``float`` and ``bool`` typed values will be unquoted in the
      CSV output.
    - ``str`` typed values will be quoted in the CSV output.
    - Values with complex types (e.g. ``list``, ``dict``) will be represented
      as their Python string representation in the CSV output and will be
      quoted only when needed (e.g. when the string representation contains
      a quote character or a delimiter character).

  * On Python 3.12 and earlier:

    - ``None`` will be quoted in the CSV output and thus appears as a quoted
      empty string (``""``). That is not optimal since it cannot be
      distinguished from an empty string.
    - ``int``, ``float`` and ``bool`` typed values will remain unquoted in the
      CSV output.
    - ``str`` typed values will be quoted in the CSV output.
    - Values with complex types (e.g. ``list``, ``dict``) will be represented
      as their Python string representation in the CSV output and will always
      be quoted.

  Here is an example that uses values of different types to show the different
  quoting:

  * Given the following Python object:

    .. code-block:: python

        [
            {
                "str": "foo",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "none": None,
                "list": ["a", "b"],
                "dict": {"a": 1},
            }
        ]

  * The CSV output on Python 3.13 and later for this Python object would be:

    .. code-block:: text

        "str","int","float","bool","none","list","dict"
        "foo",42,3.14,True,,"['a', 'b']",{'a': 1}

  * The CSV output on Python 3.12 and earlier for this Python object would be:

    .. code-block:: text

        "str","int","float","bool","none","list","dict"
        "foo",42,3.14,True,"","['a', 'b']","{'a': 1}"

.. _`reStructuredText`: http://docutils.sourceforge.net/docs/user/rst/quickref.html#tables
.. _`Mediawiki`: http://www.mediawiki.org/wiki/Help:Tables
.. _`HTML`: https://www.w3.org/TR/html401/struct/tables.html
.. _`LaTeX`: https://en.wikibooks.org/wiki/LaTeX/Tables
.. _`JSON`: http://json.org/example.html


.. _`Error message formats`:

Error message formats
---------------------

In order to be able to programmatically process errors, the zhmc CLI supports
multiple formats for its error messages.

Error messages are always printed to stderr, and the zhmc command always ends
with a non-zero return code in case of errors.

The format of error messages can be selected with the ``-e`` or
``--error-format`` option. The following error message formats are supported:

* ``-e msg``: Human-readable message. This is the default. This format should
  not be parsed by scripts, because it may change. Example:

  .. code-block:: text

      Error: ConnectTimeout: Connection to 9.152.150.86 timed out. (connect timeout=30)

* ``-e def``: Definition-style (e.g. "name: value"). In this format, the
  instance variables of the exception object causing the error are shown as
  variables. This format is meant for parsing by scripts that invoke the zhmc
  CLI and that need to handle specific error situations.

  The format of each error message is:

  .. code-block:: text

      Error: {str-def-result}

  where ``{str-def-result}`` is the return value of the
  :meth:`~zhmcclient.Error.str_def` method of the exception causing the error
  message (or rather its implementations in derived exception classes).
  Example:

  .. code-block:: text

      Error: classname='ConnectTimeout'; connect_timeout=30; connect_retries=3; message=u'Connection to 9.152.150.86 timed out. (connect timeout=30)';

  The variables for any particular exception is documented in the ``str_def()``
  method of the exception class, in this case
  :meth:`zhmcclient.ConnectTimeout.str_def`:

  .. code-block:: text

      classname={}; connect_timeout={}; connect_retries={}; message={};

  The ``{}`` sequences contain the Python representations for the values
  (using ``repr()``).

  With the exception of the initial "Error:", this is in fact Python syntax
  for setting variables. Therefore, it is best to use Python for parsing it
  from within a shell script that invokes the zhmc CLI, for example as follows:

  .. code-block:: bash

      err_file=$(mktemp)
      cpc_list=$(zhmc -o json -e def cpc list 2>$err_file)
      rc=$?
      err=$(tail -n 1 <$err_file | sed -e 's/^Error: //')
      rm $err_file
      if [[ $rc != 0 ]]; then
          if [[ "$err" =~ "classname='ConnectTimeout';" ]]; then
              ct=$(python -c "$err print(connect_timeout)")
              echo "connect-timeout: $ct"
          fi
          msg=$(python -c "$err print(message)")
          echo "message: $msg"
          exit 1
      fi
      echo "$cpc_list"


.. _`CLI logging`:

CLI logging
-----------

The zhmc CLI supports logging to the standard error stream, and to the
system log.

By default, the zhmc CLI logs to the standard error stream. This can be changed
via the global option ``--log-dest`` which specifies the log destination:

* ``stderr`` - Standard error stream of the zhmc command.
* ``syslog`` - System log of the local system.
* ``none`` - No logging.

The global option ``--log`` allows specifying one or more combinations of log
component and log level. For example, the command:

.. code-block:: text

    $ zhmc --log hmc=debug,api=info ...

sets log level ``debug`` for the ``hmc`` component, and log level ``info`` for
the ``api`` component.

Valid log levels are: ``error``, ``warning``, ``info``, ``debug``. In case of
logging to the system log, this will also set the syslog priority accordingly.

Valid log components are:

* ``api`` - Enable the ``zhmcclient.api`` Python logger, which logs any API
  calls into the zhmcclient library that are made from the zhmc CLI.
* ``hmc`` - Enable the ``zhmcclient.hmc`` Python logger, which logs the
  interactions with the HMC.
* ``console`` - Enable the ``zhmccli.console`` Python logger, which logs the
  interactions with the console of the operating system running in a partition
  or LPAR.
* ``all`` - Enable the root Python logger, which logs anything that is
  propagated up to it. In case of the zhmc CLI, this will mostly be the
  ``requests`` package, plus the ``api`` and ``hmc`` components.

Logging to the system log
~~~~~~~~~~~~~~~~~~~~~~~~~

When specifying the ``syslog`` log destination, the enabled Python loggers
log to the system log of the local system.

In order to see something in the system log, one has to understand how the
log records are marked in terms of `facility` and `priority` and the
corresponding matching of these markers in the syslog demon, and the
mechanism that is used to write a record to the syslog needs to be enabled.

The write mechanism used by the zhmc CLI depends on the platform, as follows:

* On Linux: Via a Unix socket to ``/dev/log``, or if that fails via a UDP
  socket to ``localhost`` port 514
* On OS-X: Via a Unix socket to ``/var/run/syslog``, or if that fails via a
  UDP socket to ``localhost`` port 514
* On Windows (native): Via a UDP socket to ``localhost`` port 514
* On CygWin: Via a Unix socket to ``/dev/log``, or if that fails via a UDP
  socket to ``localhost`` port 514

The respective mechanism must be enabled on the platform for logging to work.
If the required mechanism is not enabled on a system, the log record will
simply be dropped silently.

The `facility` used for each log record can be specified with the global option
``--syslog-facility``, to be one of: ``user`` (default), ``local<N>`` with
N=[0..7].

This facility marker can be used in the configuration of the syslog demon on
the local system to direct log records into different files.

For example, on RHEL 7 and CentOS 7, the syslog demon's config file is
``/etc/rsyslog.conf`` and may contain this:

.. code-block:: text

    #### RULES ####
    *.info;mail.none;authpriv.none;cron.none                /var/log/messages

The first string is a semicolon-separated list of ``<facility>.<priority>``
markers, where ``*`` can be used for wildcarding. The first list item
``*.info`` means that any facility with priority ``info`` or higher will match
this line and will thus go into the ``/var/log/messages`` file.

Because the zhmc CLI uses the ``debug`` log level, one can see that only
if its corresponding priority is enabled in the syslog configuration:

.. code-block:: text

    #### RULES ####
    *.debug;mail.none;authpriv.none;cron.none                /var/log/messages
