import ssl

default_context = ssl._create_default_https_context

import logging

logger = logging.getLogger()

from pysphere import VIServer, VIProperty
from pysphere.resources import VimService_services as VI
from pysphere.vi_mor import VIMor


class ESXiHostClass:
    def __init__(self, host, user, passwd):
        self._connection = VIServer()
        logger.info("%s:connecting to '%s' as '%s'", __name__, host, user)
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            self._connection.connect(host, user, passwd)
            logger.debug("%s:host reports '%s V.%s'", __name__,
                         self._connection.get_server_type(), self._connection.get_api_version())
            self.host_config, n, n, n = self._get_host_config()
        except Exception, err:
            logger.critical("%s:%s", __name__, err)
            quit(2)

    def get_connection(self):
        return self._connection

    def get_guests(self):
        ret = []
        for each in self._connection.get_registered_vms():
            entry = self._connection.get_vm_by_path(each)
            ret.append(entry.get_properties()['name'])
        logger.debug("%s:found %s guests", __name__, len(ret))
        return ret

    def _get_host_config(self):
        # -> get Datacenter and it's properties
        dc_mor = [k for k, v in self._connection.get_datacenters().items()][-1]  # just take the last one .... good?
        dc_props = VIProperty(self._connection, dc_mor)

        # -> get computer resources MORs
        cr_mors = self._connection._retrieve_properties_traversal(property_names=['name', 'host'],
                                                                  from_node=dc_props.hostFolder._obj,  # hostfolder mor
                                                                  obj_type='ComputeResource')

        # -> get host MOR
        host_mor = [k for k, v in self._connection.get_hosts().items()][-1]  # just take the last one .... good?

        # -> get computer resource MOR for host
        cr_mor = None
        for cr in cr_mors:
            if cr_mor:
                break
            for p in cr.PropSet:
                if p.Name == "host":
                    for h in p.Val.get_element_ManagedObjectReference():
                        if h == host_mor:
                            cr_mor = cr.Obj
                            break
                    if cr_mor:
                        break

        # -> get Computer Ressources
        cr_props = VIProperty(self._connection, cr_mor)

        # -> create configuration request()
        request = VI.QueryConfigTargetRequestMsg()
        _this = request.new__this(cr_props.environmentBrowser._obj)
        _this.set_attribute_type(cr_props.environmentBrowser._obj.get_attribute_type())
        request.set_element__this(_this)

        # -> get answer back!
        config_target = self._connection._proxy.QueryConfigTarget(request)._returnval
        return config_target, host_mor, dc_props, cr_props

    def get_networks(self):
        ret = []
        for net in self.host_config.Network:
            ret.append(net.Network.Name)
        logger.debug("%s:found %s networks", __name__, len(ret))
        return ret

    def get_datastores(self):
        ret = []
        for d in self.host_config.Datastore:
            if d.Datastore.Accessible:
                ret.append(d.Datastore.Name)
        logger.debug("%s:found %s datastores", __name__, len(ret))
        return ret
