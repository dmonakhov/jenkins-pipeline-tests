#!/usr/bin/env python

import os
import re
import json
import shutil

from StringIO import StringIO

from avocado import Test
from avocado import main
from avocado.utils import kernel
from avocado.utils import archive
from avocado.utils import process
from avocado.core import data_dir


class LinuxBase(Test):
    """
    :avocado: enable
    """
    def do_config(self):
        self.kernel_version = self.params.get('linux_version', default='AUTODETECT')
        self.kernel_git_url = self.params.get('linux_git_url',
                                              default='https://github.com/torvalds/linux.git')
        self.kernel_git_base_url = self.params.get('linux_git_base_url',
                                                   default='rsync://autotest.qa.sw.ru:/git-mirror/kernel/linux.git')
        self.linux_git_commit = self.params.get('linux_git_commit', default=None)
        self.linux_config_url = self.params.get('linux_config', default=None)
        self.linux_patch_mbox_url = self.params.get('linux_patch_mbox', default=None)

        self.linux_config = self.fetch_asset(self.linux_config_url)
        if self.linux_patch_mbox_url is not None:
            self.linux_patch_mbox = self.fetch_asset(self.linux_patch_mbox_url)
        else:
            self.linux_patch_mbox = None

        # Read dynamic config
        self.config_dir = os.path.join(self.datadir, "../../artifacts")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.config_file = os.path.join(self.config_dir, "dynconfig.json")
        self.config = {}
        if os.path.exists(self.config_file):
            self.config = json.loads(open(self.config_file, "r").read())

    def save_config(self):
        json.dump(self.config, open(self.config_file, "w"), indent=4)
        tcfg = os.path.join(self.outputdir, "dynconfig.json")
        json.dump(self.config, open(tcfg, "w"), indent=4)

    def require_linux_src(self):
        if 'linux_src' not in self.config.keys():
            self.skip("Linux config has no key 'linux_src'")
        self.log.info('config :%s ' % self.config)

        self.linux_arc = self.config['linux_src']
        self.linux_arc_orig = None

        if 'linux_src_orig' in self.config.keys():
            self.linux_arc_orig = self.config['linux_src_orig']

        self.log.info('linux_arc :%s ' % self.linux_arc)
        self.log.info('linux_arc_orig :%s ' % self.linux_arc_orig)
        self.kernel_version = os.path.basename(self.linux_arc)
        self.log.info('basename kernel_version :%s ' % self.kernel_version)
        self.kernel_version = self.kernel_version[len('linux-'):-len('.tar.gz')]
        self.log.info('basename.strip kernel_version :%s ' % self.kernel_version)

        self.kb = kernel.KernelBuild(self.kernel_version,
                                     self.linux_config,
                                     self.srcdir,
                                     self.cache_dirs)
        self.kb.download("file://" + self.linux_arc)
        self.kb.uncompress()
        self.kb.configure()


class Linux02Build(LinuxBase):
    """
    TODO_RM:avocado: enable
    """

    def setUp(self):
        self.do_config()
        self.require_linux_src()

    def test_build(self):
        #TODO Save bzImage some where

        self.kb.build()
        ksrc= os.path.join(self.kb.build_dir,'arch/x86_64/boot/bzImage')
        kdst= os.path.join(self.config_dir, 'bzImage')
        self.log.info("copy %s -> %s" %( ksrc, kdst))
        shutil.copy(ksrc, kdst)
        

if __name__ == "__main__":
    main()
