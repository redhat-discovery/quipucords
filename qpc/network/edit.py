#!/usr/bin/env python
#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""NetworkEditCommand is used to edit existing profiles for system scans."""

from __future__ import print_function
import sys
from requests import codes
from qpc.request import PATCH, GET, request
from qpc.clicommand import CliCommand
from qpc.utils import read_in_file
import qpc.auth as auth
import qpc.network as network
from qpc.network.utils import validate_port, build_profile_payload
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class NetworkEditCommand(CliCommand):
    """Defines the edit command.

    This command is for editing existing network profiles  which can be used
    for system scans to gather facts.
    """

    SUBCOMMAND = network.SUBCOMMAND
    ACTION = network.EDIT

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PATCH,
                            network.NETWORK_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.PROFILE_NAME_HELP),
                                 required=True)
        self.parser.add_argument('--hosts', dest='hosts', nargs='+',
                                 metavar='HOSTS', default=[],
                                 help=_(messages.PROFILE_HOSTS_HELP),
                                 required=False)
        self.parser.add_argument('--auth', dest='auth', metavar='AUTH',
                                 nargs='+', default=[],
                                 help=_(messages.PROFILE_AUTHS_HELP),
                                 required=False)
        self.parser.add_argument('--sshport', dest='ssh_port',
                                 metavar='SSHPORT', type=validate_port,
                                 help=_(messages.PROFILE_SSH_PORT_HELP))

    # pylint: disable=too-many-branches
    def _validate_args(self):
        CliCommand._validate_args(self)

        if not(self.args.hosts or self.args.auth or self.args.ssh_port):
            print(_(messages.PROFILE_EDIT_NO_ARGS % (self.args.name)))
            self.parser.print_help()
            sys.exit(1)

        if self.args.hosts and len(self.args.hosts) == 1:
            # check if a file and read in values
            try:
                self.args.hosts = read_in_file(self.args.hosts[0])
            except ValueError:
                pass

        # check for existence of profile
        response = request(parser=self.parser, method=GET,
                           path=network.NETWORK_URI,
                           params={'name': self.args.name},
                           payload=None)
        if response.status_code == codes.ok:  # pylint: disable=no-member
            json_data = response.json()
            if len(json_data) == 1:
                profile_entry = json_data[0]
                self.req_path = self.req_path + str(profile_entry['id']) + '/'
            else:
                print(_(messages.PROFILE_DOES_NOT_EXIST % self.args.name))
                sys.exit(1)
        else:
            print(_(messages.PROFILE_DOES_NOT_EXIST % self.args.name))
            sys.exit(1)

        # check for valid auth values
        if len(self.args.auth) > 0:  # pylint: disable=len-as-condition
            auth_list = ','.join(self.args.auth)
            response = request(parser=self.parser, method=GET,
                               path=auth.AUTH_URI,
                               params={'name': auth_list},
                               payload=None)
            if response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = response.json()
                if len(json_data) == len(self.args.auth):
                    self.args.credentials = []
                    for cred_entry in json_data:
                        self.args.credentials.append(cred_entry['id'])
                else:
                    for cred_entry in json_data:
                        cred_name = cred_entry['name']
                        self.args.auth.remove(cred_name)
                    not_found_str = ','.join(self.args.auth)
                    print(_(messages.PROFILE_EDIT_AUTHS_NOT_FOUND %
                            (not_found_str, self.args.name)))
                    sys.exit(1)
            else:
                print(_(messages.PROFILE_EDIT_AUTH_PROCESS_ERR %
                        self.args.name))
                sys.exit(1)

    def _build_data(self):
        """Construct the dictionary auth given our arguments.

        :returns: a dictionary representing the auth being added
        """
        self.req_payload = build_profile_payload(self.args, add_none=False)

    def _handle_response_success(self):
        print(_(messages.PROFILE_UPDATED % self.args.name))
