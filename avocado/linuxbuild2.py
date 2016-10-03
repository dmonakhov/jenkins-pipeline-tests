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
        self.config_dir = os.path.abspath(self.config_dir)
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


class Linux01Download(LinuxBase):
    """
    :avocado: enable
    Fetch and patch linux tree
    """
    def setUp(self):
        self.do_config()

    def test(self):

        #asset.Asset(name, asset_hash, algorithm, locations,
        #                   self.cache_dirs, expire).fetch()
        #
        # Quesion!! How to pass config file
        #if linux_config is not None:
        #    linux_config = os.path.join(self.datadir, linux_config)
        #if linux_patch_mbox is not None:
        #    linux_patch_mbox = os.path.join(self.datadir, linux_patch_mbox)

        linux_build = kernel.KernelBuild(self.kernel_version,
                                         self.linux_config,
                                         self.srcdir,
                                         self.cache_dirs)
        linux_build.fetch_git_repo(self.kernel_git_url,
                                   commit=self.linux_git_commit,
                                   base_uri=self.kernel_git_base_url)
        linux_build.configure()
        bname = "linux-%s.tar.gz" % linux_build.version
        linux_archive = os.path.join(self.config_dir, bname)
        self.config['linux_src'] = linux_archive
        process.run("find %s -ls" % self.config_dir)
        #process.run("find %s/../ -ls" % self.config_dir)
        linux_build.git_archive(linux_archive)
        process.run("find %s/../ -ls" % self.config_dir)
        if self.linux_patch_mbox is None:
            # Create archive for other tests
            self.config['linux_src'] = linux_archive
            self.save_config()
            return

        # Save mbox to result directory
        afname = os.path.join(self.outputdir, 'patch-mbox.tar.gz')
        self.log.info("mbox: %s" % self.linux_patch_mbox)
        archive.create(afname, self.linux_patch_mbox)

        # Finally to apply patches
        pq = linux_build.apply_mbox(self.linux_patch_mbox)
        pq_archive = os.path.join(self.config_dir, 'linux-patch-queue.tar.gz')
        archive.create(pq_archive, pq)
        self.config['linux_patch_queue'] = pq_archive

        linux_build.configure()
        orig_linux_archive = linux_archive
        bname = "linux-%s.tar.gz" % linux_build.version
        linux_archive = os.path.join(self.config_dir, bname)
        linux_build.git_archive(linux_archive)
        self.config['linux_src_orig'] = orig_linux_archive
        self.config['linux_src'] = linux_archive
        self.save_config()


if __name__ == "__main__":
    main()
