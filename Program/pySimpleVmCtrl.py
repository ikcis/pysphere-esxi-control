import argparse
from pySimpleVmCtrl.ESXiGuest import *

logger = logging.getLogger()

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-v', action='store_true', default=False,
                    dest='verbosity',
                    help='be verbose [%(default)s]')

parser.add_argument('-H', action='store', default='localhost',
                    dest='host',
                    help='hostname esxi server [%(default)s]')

parser.add_argument('-U', action='store', default='root',
                    dest='user',
                    help='username to connect to esx [%(default)s]')

parser.add_argument('-P', action='store',
                    dest='passwd',
                    help='password [read from stdin]')

parser.add_argument('-A', action='append', dest='action',
                    help="what to do [list-host|list-guest|off|on|reboot|del|create]",
                    )

parser.add_argument('-g', action='store',
                    dest='guest',
                    help='Guest virtual machine name')

parser.add_argument('--store', action='store', default=None,
                    dest='datastore',
                    help='(create) datastore to use')

parser.add_argument('--net', action='store', default=None,
                    dest='network',
                    help='(create) network to connect to')

parser.add_argument('--disk', action='store', default=8,
                    dest='disksize',
                    help='(create) disksize in GB [%(default)s]')

parser.add_argument('--cpu', action='store', default="1",
                    dest='cpu',
                    help='(create) cpu count [%(default)s]')

parser.add_argument('--mem', action='store', default="1024",
                    dest='memory',
                    help='(create) memory in MB [%(default)s]')

parser.add_argument('--os', action='store', default="rhel6_64Guest",
                    dest='operatingsystem',
                    help='(create) Operating system [%(default)s]')


def execute_arguments(esx_host, action, args):
    logger.debug('%s:execute_arguments(%s, %s, %s)', __name__, 'ESXiHostClass', action, args.guest)
    if action == "list-host":
        print "--- available datastores ---"
        for each in esx_host.get_datastores():
            print "[" + each + "]"
        print "--- available networks ---"
        for each in esx_host.get_networks():
            print "'" + each + "'"
        return True

    elif action == "list-guest":
        print "--- available guests ---"
        for each in esx_host.get_guests():
            each_guest = ESXiGuestClass(esx_host, each)
            power, net = each_guest.get_status()
            print each, ' ', power, ' ', net
        return True

    if args.guest is None:
        logger.critical('%s:execute_arguments(): either illegal action or specify guest name', __name__)
        return False

    guest = ESXiGuestClass(esx_host, args.guest)

    assert isinstance(guest, ESXiGuestClass)

    if action == "off":
        return guest.power_off()
    if action == "on":
        return guest.power_on()
    if action in ["reset", "reboot"]:
        return guest.reboot()

    if action in ["add", "create"]:
        return guest.create_me(cpu=int(argparser.cpu), mem=int(argparser.memory), os=argparser.operatingsystem,
                               datastore=argparser.datastore, network=argparser.network, diskGB=int(argparser.disksize))

    if action in ["rem", "del"]:
        guest.power_off()
        return guest.remove_me()

    if action in ["create_snapshot"]:
        return guest.create_snapshot()

    if action in ["delete_snapshot"]:
        return guest.delete_snapshot()

    if action in ["revert_to_snapshot"]:
        return guest.revert_to_snapshot()

    if action in ["get_snapshot_info"]:
        return guest.get_snapshot_info()


if __name__ == "__main__":
    argparser = parser.parse_args()

    if argparser.action is None:
        parser.print_help()
        quit(2)

    esx_host = ESXiHostClass(argparser.host, argparser.user, argparser.passwd)

    for each_action in argparser.action:
        execute_arguments(esx_host, each_action, argparser)
