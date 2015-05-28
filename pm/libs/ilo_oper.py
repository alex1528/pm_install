# -*- coding: utf-8 -*-


import time
import re

import pexpect

from web.const import PXELINUX_CFGS
from libs import log, utils


logger = log.get_logger("pm ilo oper")


class generate(object):

    def __init__(self, idc, ip, passwd):
        self.idc = idc
        self.ip = ip
        self.passwd = passwd

    def ssh_cmd(self, cmd):
        ssh = pexpect.spawn(
            '''ssh -t -p 2222 -o StrictHostKeyChecking=no '''\
            '''-t %s-relay.nosa.me " ssh -o StrictHostKeyChecking=no '''\
            '''-o ConnectTimeout=600 root@%s '%s' " ''' % (
                self.idc, self.ip, cmd), timeout=600)
        ssh.expect([pexpect.TIMEOUT, 'password: '])
        ssh.sendline(self.passwd)
        time.sleep(1)
        ret = ssh.read()

        return ret

    def get_nic_name(self, device):
        cmd = r"racadm get NIC.NICConfig"
        r = self.ssh_cmd(cmd)
        ret = r.find("NIC.Integrated")

        if ret != -1:
            if device == "em1":
                return "NIC.Integrated.1-1-1"
            return "NIC.Integrated.1-2-1"
        else:
            ret1 = r.find("NIC.Embedded")
            if ret1 != -1:
                if device == "em1":
                    return "NIC.Embedded.1-1-1"
                return "NIC.Embedded.2-1-1"

        # setup a default nic
        default = "NIC.Integrated.1-2-1"
        logger.error(
            "cann't get %s nic name,using default - %s" % (self.ip, default))
        return default
        # return False

    def get_nic_config(self, nic):
        cmd = r"racadm get NIC.NICConfig"
        tmp = self.ssh_cmd(cmd)
        for i in tmp.split("\n"):
            if nic in i:
                NicConfig = i.split(" ")[0]
                break
        if "NicConfig" not in locals():
            return False
        return NicConfig

    def check_boot_order(self, nic_seq):
        cmd = r"racadm get BIOS.BiosBootSettings.BootSeq"
        lines = self.ssh_cmd(cmd)
        ret = lines.find("BootSeq=%s" % nic_seq)

        if ret != -1:
            return True
        else:
            return False

    def get_boot_order(self, nic):
        return "HardDisk.List.1-1,%s" % nic

    def setup_boot_order(self, nic_seq):
        cmd = r"racadm set BIOS.BiosBootSettings.BootSeq %s" % nic_seq
        r = self.ssh_cmd(cmd)
        index = r.find("Successfully", 0)
        if index == -1:
            return False

        cmd = r"racadm jobqueue delete --all"
        self.ssh_cmd(cmd)

        cmd = r"racadm jobqueue create BIOS.Setup.1-1 -r pwrcycle -s TIME_NOW"
        r = self.ssh_cmd(cmd)
        index = r.find("Successfully", 0)
        if index == -1:
            return False

        # 这个时间是为了让机器重启使配置生效,不设置的話这个 jobqueue 
        # 可能会后面的代码清掉,导致安装失败。
        time.sleep(600)

        return True

    def get_nic_pxeboot(self, nic):
        NicConfig = self.get_nic_config(nic)
        if not NicConfig:
            return False

        if nic == "NIC.Embedded.2-1-1":
            cmd = r"racadm get %s.LegacyBootProto" % NicConfig
        elif nic == "NIC.Embedded.1-1-1":
            cmd = r"racadm get %s.LegacyBootProto" % NicConfig
        elif nic == "NIC.Integrated.1-2-1":
            cmd = r"racadm get %s.LegacyBootProto" % NicConfig
        elif nic == "NIC.Integrated.1-1-1":
            cmd = r"racadm get %s.LegacyBootProto" % NicConfig
        else:
            # return "nic not support"
            return False

        r = self.ssh_cmd(cmd)
        index = r.find("LegacyBootProto=PXE", 0)
        if index == -1:
            return False

        return True

    def setup_nic_pxeboot(self, nic):
        NicConfig = self.get_nic_config(nic)
        if not NicConfig:
            return False

        cmd1 = r"racadm set %s.LegacyBootProto PXE" % NicConfig

        if nic == "NIC.Embedded.2-1-1":
            cmd2 = r"racadm jobqueue create NIC.Embedded.2-1-1 -r pwrcycle -s TIME_NOW"
        elif nic == "NIC.Embedded.1-1-1":
            cmd2 = r"racadm jobqueue create NIC.Embedded.1-1-1 -r pwrcycle -s TIME_NOW"
        elif nic == "NIC.Integrated.1-2-1":
            cmd2 = r"racadm jobqueue create NIC.Integrated.1-2-1 -r pwrcycle -s TIME_NOW"
        elif nic == "NIC.Integrated.1-1-1":
            cmd2 = r"racadm jobqueue create NIC.Integrated.1-1-1 -r pwrcycle -s TIME_NOW"
        else:
            # return "nic not support"
            return False

        cmd = r"racadm jobqueue delete --all"
        self.ssh_cmd(cmd)

        r = self.ssh_cmd(cmd1)
        index = r.find("Successfully", 0)
        if index == -1:
            return False

        r = self.ssh_cmd(cmd2)
        index = r.find("Successfully", 0)
        if index == -1:
            return False

        # 这个时间是为了让机器重启使配置生效,不设置的話这个 jobqueue 
        # 可能会后面的代码清掉,导致安装失败。
        time.sleep(600)

        return True

    def setup_pxeboot_once(self):
        cmd = r"racadm config -g cfgServerInfo -o cfgServerBootOnce 1"
        r = self.ssh_cmd(cmd)
        ret = r.find("Object value modified successfully")
        if ret != -1:
            pass
        else:
            return False
        cmd = r"racadm config -g cfgServerInfo -o cfgServerFirstBootDevice PXE"
        r = self.ssh_cmd(cmd)
        ret = r.find("Object value modified successfully")
        if ret != -1:
            return True
        else:
            return False

    def get_sn(self):
        cmd = r"racadm getsvctag"
        r = self.ssh_cmd(cmd)
        second_line = r.split("\n")[1]
        ret = second_line.strip()
        return ret

    def get_mac(self, nic):
        cmd = "racadm getsysinfo -s"
        r = self.ssh_cmd(cmd)
        mac = 'echo "%s" | grep "%s" | awk \'{print $4}\'' % (r, nic)
        rc, so, se = utils.shell(mac)
        format_mac = so.replace(":", "-").lower()
        constract_mac = "01-%s" % format_mac
        return constract_mac.strip()

    def constract_tftp(self, _type, version, mac):
        """ 拷贝 pxelinux.cfg 配置文件到目标目录.

        """
        cmd = r"sudo /bin/cp -f %s /var/lib/tftpboot/pxelinux.cfg/%s" % (
                PXELINUX_CFGS[_type][version], mac)
        rc, so, se = utils.shell(cmd)
        if rc != 0:
            return False

        return True

    def del_tftp(self, mac):
        cmd = r"sudo /bin/rm -f /var/lib/tftpboot/pxelinux.cfg/%s" % (mac)
        rc, so, se = utils.shell(cmd)
        if rc != 0:
            return False

        return True

    def reboot(self):
        cmd = r"racadm serveraction powercycle"
        r = self.ssh_cmd(cmd)
        ret = r.find("Server power operation successfu")
        if ret != -1:
            return True
        return False
