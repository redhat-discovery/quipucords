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
"""NetworkShowCommand is used to show network profiles for system scans."""

from __future__ import print_function
import sys
from requests import codes
from qpc.utils import pretty_print
from qpc.clicommand import CliCommand
import qpc.network as network
from qpc.request import GET
from qpc.translation import _
import qpc.messages as messages


# pylint: disable=too-few-public-methods
class NetworkShowCommand(CliCommand):
    """Defines the show command.

    This command is for showing a network which can later be used with a scan
    to gather facts.
    """

    SUBCOMMAND = network.SUBCOMMAND
    ACTION = network.SHOW

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            network.NETWORK_URI, [codes.ok])
        self.parser.add_argument('--name', dest='name', metavar='NAME',
                                 help=_(messages.PROFILE_NAME_HELP),
                                 required=True)

    def _build_req_params(self):
        self.req_params = {'name': self.args.name}

    def _handle_response_success(self):
        json_data = self.response.json()
        if len(json_data) == 1:
            cred_entry = json_data[0]
            data = pretty_print(cred_entry)
            print(data)
        else:
            print(_(messages.PROFILE_DOES_NOT_EXIST % self.args.name))
            sys.exit(1)
