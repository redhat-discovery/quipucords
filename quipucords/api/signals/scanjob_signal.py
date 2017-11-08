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

"""Signal manager to handle scan triggering."""

import logging
import django.dispatch
from api.models import ScanJob
from scanner.discovery import DiscoveryScanner
from scanner.host import HostScanner


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PAUSE = 'pause'
CANCEL = 'cancel'
RESTART = 'restart'


# pylint: disable=W0613
def handle_scan(sender, instance, fact_endpoint, **kwargs):
    """Handle incoming scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was triggered
    :param fact_endpoint: The API endpoint to send collect fact to
    :param kwargs: Other args
    :returns: None
    """
    if instance.scan_type == ScanJob.DISCOVERY:
        scan = DiscoveryScanner(instance)
        scan.start()
    else:
        scan = HostScanner(instance, fact_endpoint)
        scan.start()


def scan_action(sender, instance, action, **kwargs):
    """Handle action on scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param action: The action to take on the scan (pause, cancel, resume)
    :param kwargs: Other args
    :returns: None
    """
    logger.info('Handling %s action on scan %s', action, instance)


def scan_pause(sender, instance, **kwargs):
    """Pause a scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param kwargs: Other args
    :returns: None
    """
    scan_action(sender, instance, PAUSE, **kwargs)


# pylint: disable=C0103
start_scan = django.dispatch.Signal(providing_args=['instance',
                                                    'fact_endpoint'])
pause_scan = django.dispatch.Signal(providing_args=['instance',
                                                    'action'])

start_scan.connect(handle_scan)
pause_scan.connect(scan_pause)