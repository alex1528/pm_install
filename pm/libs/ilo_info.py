# -*- coding: utf-8 -*-


import pexpect
import sys
import os

from libs import utils
from web.const import ILO_PASSWDS


def ip(idc, sn):
    cmd = '''nslookup idrac-%s.ilo.nosa.me. ddns0.%s01.nosa.me ''' % (
        sn, idc)
    rc, so, se = utils.shell(cmd)

    if rc != 0:
        return False

    return so.strip().split("\n")[-1].split(":")[-1].strip()


def passwd(idc, ip, sn):
    for passwd in ILO_PASSWDS:
        cmd = '''/usr/bin/ssh -p 2222 -t -oStrictHostKeyChecking=no '''\
            '''%s-relay.nosa.me "ssh -oStrictHostKeyChecking=no root@%s '''\
            ''' 'racadm getsvctag' "''' % (idc, ip)
        # print cmd
        ssh = pexpect.spawn(cmd)
        try:
            i = ssh.expect(
                ["password:"], timeout=180)

            if i == 0:
                ssh.sendline(passwd)
                ret = ssh.read()
                # print ret
                if sn in ret:
                    return passwd
        except pexpect.EOF:
            ssh.close()
            # ret = -1
            pass
        except pexpect.TIMEOUT:
            ssh.close()
            # ret = -2
            pass

    return False