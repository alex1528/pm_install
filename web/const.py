# -*- coding: utf-8 -*-

# 绑定的 IP 和 端口.
BIND_IP = "0.0.0.0"
BIND_PORT = "8090"

# 日志路径.
LOG_DIR = './logs'
LOG_FILE = "pm_install.log"

# REDIS 信息.
REDIS_HOST = ""
REDIS_PORT = 6379
REDIS_PASSWD = ""
REDIS_DB_PM = 0
# 用于存储 user_data 信息, 单独放在一个 db 中.
REDIS_DB_COMMON = 3

# 资产和DNS信息.
ASSET_HOST = ""
ASSET_AUTH_USERNAME = ""
ASSET_AUTH_PASSWD = ""

ASSET_AUTH_API = ""
ASSET_SERVER_QUERY = ""
ASSET_SERVER_MODIFY = ""
ASSET_QUERY_API = ""
ASSET_VMH_QUERY = ""
ASSET_HOSTNAME_APPLY = ""
ASSET_IPBLOCK_QUERY = ""
ASSET_IP_APPLY = ""
ASSET_NETWORKDEVICE_QUERY = ""

DNS_HOST = ""
DNS_AUTH_API = ""
DNS_AUTH_USERNAME = ""
DNS_AUTH_PASSWD = ""


# 物理机信息
# 可能的控制卡密码, 会自动尝试出正确的密码.
ILO_PASSWDS = ['calvin']

# 系统类型和系统版本号.
OS_TYPES = ['kvm', 'raw', 'docker']
OS_VERSIONS = ['centos6.3', 'centos7.0']

# 系统类型和系统版本号 分别对应的 pxelinux.cfg 文件路径.
PXELINUX_CFGS = {
    "raw": {
        "centos6.3": "/home/work/pxe/pxelinux.cfg/centos_6.3_x64_raw_clean",
        "centos7.0": "/home/work/pxe/pxelinux.cfg/centos_7.0_raw_clean"
    },
    "kvm": {
        "centos6.3": "/home/work/pxe/pxelinux.cfg/centos_6.3_x64_kvm_host",
        "centos7.0": "/home/work/pxe/pxelinux.cfg/centos_7.0_kvm_host"
    },
    "docker": {
        "centos7.0": "/home/work/pxe/pxelinux.cfg/centos_7.0_docker_host"
    }
}

# 装机并发数, 一个任务最多支持的同时装机数量.
MAX_THREAD_NUM = 10