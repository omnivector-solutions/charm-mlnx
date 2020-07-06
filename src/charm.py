#!/usr/bin/env python3
import requests
import subprocess
from pathlib import Path


from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus


def get_os_release_ctxt():
    os_release_ctxt = {}
    with open("/etc/os-release", 'r') as f:
        for line in f.readlines():
            os_release_ctxt[line.split("=")[0]] = line.split("=")[1]
    return os_release_ctxt


class MLNXCharm(CharmBase):

    _ID = get_os_release_ctxt['ID']
    _VERSION_ID = get_os_release_ctxt['VERSION_ID']

    _MLNX_REPO = ("https://linux.mellanox.com/public/repo/"
                  "mlnx_ofed/latest/{self._ID}{self._VERSION_ID}/"
                  "mellanox_mlnx_ofed.list")
    _APT_SOURCE_PATH = Path("/etc/apt/sources.list.d/mellanox_mlnx_ofed.list")

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.start, self._on_start)


    def _on_install(self, event):
        """Prepare for the installation of mlnx repo and packages."""
        # Add the mlnx key
        subprocess.call(
            ("get -qO - https://www.mellanox.com/downloads/ofed/RPM-GPG-KEY-Mellanox "
             "| apt-key add -"),
            shell=True
        )

        # Add the mlnx apt repo
        resp = requests.get(self._MLNX_REPO)
        self._APT_SOURCE_PATH.write_text(resp.text)
        subprocess.call(["apt", "update", "-y"])
 
        # Remove conflicting apt packages
        subprocess.call(
            ("apt-get remove libipathverbs1 librdmacm1 libibverbs1 "
             "libmthca1 libopenmpi-dev openmpi-bin openmpi-common "
             "openmpi-doc libmlx4-1 rdmacm-utils ibverbs-utils "
             "infiniband-diags ibutils perftest -y"),
            shell=True
        )
        subprocess.call(["apt", "install", "mlnx-ofed-all", "-y"])
        self.unit.status = ActiveStatus("MLNX ready")

    def _on_start(self, event):
        pass

if __name__ == "__main__":
    main(MLNXCharm)
