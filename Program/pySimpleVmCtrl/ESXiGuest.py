import logging

logger = logging.getLogger()

from pysphere.vi_virtual_machine import *
from pysphere.resources.vi_exception import *

from ESXiHost import *


class ESXiGuestClass:
    def __init__(self, esxihost, name):
        assert isinstance(esxihost, ESXiHostClass)
        self._host = esxihost
        self.name = name
        try:
            self.vm = self._host.get_connection().get_vm_by_name(name)
            logger.debug("%s:found guest named '%s'", __name__, name)
            self.config = self.vm.get_properties()
        except VIException, e:
            logger.warn("%s:%s", __name__, e.message)
            self.vm = None

    def create_snapshot(self):
        assert isinstance(self.vm, VIVirtualMachine)
        snapshot_name = raw_input("please input snapshot name:")
        self.vm.create_snapshot(name=snapshot_name)

    def delete_snapshot(self):
        assert isinstance(self.vm, VIVirtualMachine)
        snapshot_name = raw_input("please input snapshot name:")
        self.vm.delete_named_snapshot(name=snapshot_name)

    def revert_to_snapshot(self):
        assert isinstance(self.vm, VIVirtualMachine)
        snapshot_name = raw_input("please input snapshot name:")
        self.vm.revert_to_named_snapshot(name=snapshot_name)

    def get_snapshot_info(self):
        assert isinstance(self.vm, VIVirtualMachine)
        snapshot_list = self.vm.get_snapshots()
        for snapshot in snapshot_list:
            snaptext = 'Id: %s; Name: %s; Description: %s; State: %s; Path: %s' % (
                snapshot._mor, snapshot.get_name(), snapshot.get_description(),
                snapshot.get_state(), snapshot.get_path())
            print snaptext

    def get_status(self):
        assert isinstance(self.vm, VIVirtualMachine)
        netstat = 'N/A'
        ns = self.vm.get_property('net', from_cache=False)
        if ns is not None:
            netstat = ns[0]['network']
            netstat += '=' + ns[0]['mac_address']
            try:
                netstat += '=' + str(ns[0]['ip_addresses'][0])
            except IndexError:
                pass

        return self.vm.get_status(), netstat

    def power_on(self):
        assert isinstance(self.vm, VIVirtualMachine)
        try:
            self.vm.power_on()
            return True
        except VIException, e:
            logger.error("%s:'%s':%s ", __name__, self.name, e.message)
        return False

    def power_off(self):
        assert isinstance(self.vm, VIVirtualMachine)
        try:
            self.vm.shutdown_guest()
            return True
        except VIApiException, e:
            logger.error("%s:'%s':failed to shutdown, KILLING GUEST! %s ", __name__, self.name, e.fault)
        except TypeError, e:
            logger.critical("%s:'%s':API ERROR?! KILLING GUEST! %s ", __name__, self.name, str(e))
        try:
            self.vm.power_off()
            return True
        except VIException, e:
            logger.error("%s:'%s':%s ", __name__, self.name, e.message)
        return False

    def reboot(self):
        assert isinstance(self.vm, VIVirtualMachine)
        try:
            self.vm.reboot_guest()
            return True
        except VIApiException, e:
            logger.error("%s:'%s':failed to reboot, POWER-CYCLING GUEST! %s ", __name__, self.name, e.fault)
        except TypeError, e:
            logger.critical("%s:'%s':API ERROR?! KILLING GUEST! %s ", __name__, self.name, str(e))
        try:
            self.power_off()
            return self.power_on()
        except VIException, e:
            logger.error("%s:'%s':%s ", __name__, self.name, e.message)
        return False

    def remove_me(self):
        remove_vm_request = VI.Destroy_TaskRequestMsg()
        _this = remove_vm_request.new__this(self.vm._mor)
        _this.set_attribute_type(self.vm._mor.get_attribute_type())
        remove_vm_request.set_element__this(_this)
        ret = self._host._connection._proxy.Destroy_Task(remove_vm_request)._returnval

        # Wait for the task to finish
        task = VITask(ret, self._host._connection)

        status = task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])
        if status == task.STATE_SUCCESS:
            print "VM successfully deleted from disk"
        elif status == task.STATE_ERROR:
            print "Error removing vm:", task.get_error_message()

    def create_me(self, cpu=1, mem=1024, network=None, diskGB=2, datastore=None, os="rhel6_64Guest", enter_bios=False):

        if not network:
            network = self._host.get_networks()[-1]

        if not datastore:
            datastore = self._host.get_datastores()[-1]

        if not datastore.startswith('[') or not datastore.endswith(']'):
            datastore = '[' + datastore + ']'

        #
        #  prepare a VM Creation request
        #

        create_vm_request = VI.CreateVM_TaskRequestMsg()
        config = create_vm_request.new_config()

        # set the datastore path
        vm_files = config.new_files()
        vm_files.set_element_vmPathName(datastore)
        config.set_element_files(vm_files)

        # set some basics
        config.set_element_version("vmx-08")
        config.set_element_name(self.name)
        config.set_element_memoryMB(mem)
        config.set_element_memoryHotAddEnabled(True)
        config.set_element_numCPUs(cpu)
        config.set_element_cpuHotAddEnabled(True)
        config.set_element_guestId(os)

        if enter_bios:
            # set boot parameters
            vmboot = config.new_bootOptions()
            vmboot.set_element_enterBIOSSetup(True)
            config.set_element_bootOptions(vmboot)

        # -> add devices
        devices = []

        # add network interface
        if network:
            nic_spec = config.new_deviceChange()
            nic_spec.set_element_operation("add")
            nic_ctlr = VI.ns0.VirtualVmxnet3_Def("nic_ctlr").pyclass()
            nic_backing = VI.ns0.VirtualEthernetCardNetworkBackingInfo_Def("nic_backing").pyclass()
            nic_backing.set_element_deviceName(network)
            nic_ctlr.set_element_addressType("generated")
            nic_ctlr.set_element_backing(nic_backing)
            nic_ctlr.set_element_key(4)
            nic_spec.set_element_device(nic_ctlr)
            devices.append(nic_spec)

        if diskGB:
            # add controller to devices
            disk_ctrl_key = 1
            scsi_ctrl_spec = config.new_deviceChange()
            scsi_ctrl_spec.set_element_operation('add')
            scsi_ctrl = VI.ns0.ParaVirtualSCSIController_Def("scsi_ctrl").pyclass()

            scsi_ctrl.set_element_busNumber(0)
            scsi_ctrl.set_element_key(disk_ctrl_key)
            scsi_ctrl.set_element_sharedBus("noSharing")
            scsi_ctrl_spec.set_element_device(scsi_ctrl)
            devices.append(scsi_ctrl_spec)

            # add disk
            disk_spec = config.new_deviceChange()
            disk_spec.set_element_fileOperation("create")
            disk_spec.set_element_operation("add")
            disk_ctlr = VI.ns0.VirtualDisk_Def("disk_ctlr").pyclass()
            disk_backing = VI.ns0.VirtualDiskFlatVer2BackingInfo_Def("disk_backing").pyclass()
            disk_backing.set_element_fileName(datastore)
            disk_backing.set_element_diskMode("persistent")
            disk_ctlr.set_element_key(0)
            disk_ctlr.set_element_controllerKey(disk_ctrl_key)
            disk_ctlr.set_element_unitNumber(3)
            disk_ctlr.set_element_backing(disk_backing)
            guest_disk_size = diskGB * 1024 * 1024
            disk_ctlr.set_element_capacityInKB(guest_disk_size)
            disk_spec.set_element_device(disk_ctlr)
            devices.append(disk_spec)

        # place where the new Guest shall shall go to
        config_target, host_mor, dc_props, cr_props = self._host._get_host_config()
        vmf_mor = dc_props.vmFolder._obj  # get vmFolder
        rp_mor = cr_props.resourcePool._obj  # get resource pool MOR

        # append devices to the new config
        config.set_element_deviceChange(devices)

        # assemble the request
        create_vm_request.set_element_config(config)
        new_vmf_mor = create_vm_request.new__this(vmf_mor)
        new_vmf_mor.set_attribute_type(vmf_mor.get_attribute_type())
        new_rp_mor = create_vm_request.new_pool(rp_mor)
        new_rp_mor.set_attribute_type(rp_mor.get_attribute_type())
        new_host_mor = create_vm_request.new_host(host_mor)
        new_host_mor.set_attribute_type(host_mor.get_attribute_type())
        create_vm_request.set_element__this(new_vmf_mor)
        create_vm_request.set_element_pool(new_rp_mor)
        create_vm_request.set_element_host(new_host_mor)

        # finally actually create the guest :)
        task_mor = self._host._connection._proxy.CreateVM_Task(create_vm_request)._returnval
        task = VITask(task_mor, self._host._connection)
        task.wait_for_state([task.STATE_SUCCESS, task.STATE_ERROR])

        if task.get_state() == task.STATE_ERROR:
            print "Cannot create guest: ", task.get_info(), task.get_error_message()
        else:
            print "Succesfully created guest! "
            self.__init__(self._host, self.name)
