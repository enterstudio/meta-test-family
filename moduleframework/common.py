#
# Meta test family (MTF) is a tool to test components of a modular Fedora:
# https://docs.pagure.org/modularity/
# Copyright (C) 2017 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Jan Scotka <jscotka@redhat.com>
#

"""
Custom configuration and debugging library.
"""

import netifaces
import socket
import os
import urllib
import yaml
import warnings

from avocado.utils import process

from moduleframework.exceptions import *
from moduleframework.compose_info import ComposeParser

defroutedev = netifaces.gateways().get('default').values(
)[0][1] if netifaces.gateways().get('default') else "lo"
hostipaddr = netifaces.ifaddresses(defroutedev)[2][0]['addr']
hostname = socket.gethostname()
dusername = "test"
dpassword = "test"
ddatabase = "basic"
guestpackager = "dnf"
hostpackager = "yum -y"
__rh_release = '/etc/redhat-release'
if os.path.exists(__rh_release) and os.path.exists('/usr/bin/dnf'):
    hostpackager = "dnf -y"
else:
    hostpackager = "apt-get -y"
ARCH = "x86_64"

# translation table for {VARIABLE} in the config.yaml file
trans_dict = {"HOSTIPADDR": hostipaddr,
              "GUESTIPADDR": hostipaddr,
              "DEFROUTE": defroutedev,
              "HOSTNAME": hostname,
              "ROOT": "/",
              "USER": dusername,
              "PASSWORD": dpassword,
              "DATABASENAME": ddatabase,
              "HOSTPACKAGER": hostpackager,
              "GUESTPACKAGER": guestpackager,
              "GUESTARCH": ARCH,
              "HOSTARCH": ARCH
              }


BASEPATHDIR = "/opt"
PDCURL = "https://pdc.fedoraproject.org/rest_api/v1/unreleasedvariants"
URLBASECOMPOSE = "https://kojipkgs.fedoraproject.org/compose/latest-Fedora-Modular-26/compose/Server"
REPOMD = "repodata/repomd.xml"
MODULEFILE = 'tempmodule.yaml'
# default value of process timeout in seconds
DEFAULTPROCESSTIMEOUT = 2 * 60
DEFAULTRETRYCOUNT = 3
# time in seconds
DEFAULTRETRYTIMEOUT = 30
DEFAULTNSPAWNTIMEOUT = 10


def is_debug():
    """
    Return the **DEBUG** envvar.

    :return: bool
    """
    return bool(os.environ.get("DEBUG"))


def is_not_silent():
    """
    Return the opposite of the **DEBUG** envvar.

    :return: bool
    """
    return is_debug()


def print_info(*args):
    """
    Print information from the expected stdout and
    stderr files from the native test scope.

    See `Test log, stdout and stderr in native Avocado modules
    <https://avocado-framework.readthedocs.io/en/latest/WritingTests.html
    #test-log-stdout-and-stderr-in-native-avocado-modules>`_ for more information.

    :param args: object
    :return: None
    """
    for arg in args:
        result = arg
        if isinstance(arg, basestring):
            try:
                result = arg.format(**trans_dict)
            except KeyError:
                raise ModuleFrameworkException(
                    "String is formatted by using trans_dict. If you want to use "
                    "brackets { } in your code, please use double brackets {{  }}."
                    "Possible values in trans_dict are: %s"
                    % trans_dict)
        print >> sys.stderr, result


def print_debug(*args):
    """
    Print information from the expected stdout and
    stderr files from the native test scope if
    the **DEBUG** envvar is set to True.

    See `Test log, stdout and stderr in native Avocado modules
    <https://avocado-framework.readthedocs.io/en/latest/WritingTests.html
    #test-log-stdout-and-stderr-in-native-avocado-modules>`_ for more information.

    :param args: object
    :return: None
    """
    if is_debug():
        print_info(*args)

def is_recursive_download():
    """
    Return the **MTF_RECURSIVE_DOWNLOAD** envvar.

    :return: bool
    """
    return bool(os.environ.get("MTF_RECURSIVE_DOWNLOAD"))

def get_if_do_cleanup():
    """
    Return the **MTF_DO_NOT_CLEANUP** envvar.

    :return: bool
    """
    cleanup = os.environ.get('MTF_DO_NOT_CLEANUP')
    return not bool(cleanup)

def get_if_reuse():
    """
        Return the **MTF_REUSE** envvar.

        :return: bool
        """
    reuse = os.environ.get('MTF_REUSE')
    return bool(reuse)

def get_if_remoterepos():
    """
    Return the **MTF_REMOTE_REPOS** envvar.

    :return: bool
    """
    remote_repos = os.environ.get('MTF_REMOTE_REPOS')
    return bool(remote_repos)


def get_if_module():
    """
    Return the **MTF_DISABLE_MODULE** envvar.

    :return: bool
    """
    disable_module = os.environ.get('MTF_DISABLE_MODULE')
    return not bool(disable_module)


def sanitize_text(text, replacement="_", invalid_chars=["/", ";", "&", ">", "<", "|"]):

    """
    Replace invalid characters in a string.

    invalid_chars=["/", ";", "&", ">", "<", "|"]

    :param (str): text to sanitize
    :param (str): replacement char, default: "_"
    :return: str
    """
    for char in invalid_chars:
        if char in text:
            text = text.replace(char, replacement)
    return text


def sanitize_cmd(cmd):
    """
    Escape apostrophes in a command line.

    :param (str): command to sanitize
    :return: str
    """

    if '"' in cmd:
        cmd = cmd.replace('"', r'\"')
    return cmd


def get_profile():
    """
    Return a profile name.

    If the **PROFILE** envvar is not set, a profile name is
    set to be `default`.

    :return: str
    """
    profile = os.environ.get('PROFILE')
    if not profile:
        profile = "default"
    return profile


def get_url():
    """
    Return the **URL** envvar.

    :return: str
    """
    url = os.environ.get('URL')
    return url


def get_config():
    """
    Read the module's configuration file.

    :default: ``./config.yaml`` in the ``tests`` directory of the module's root
     directory
    :envvar: **CONFIG=path/to/file** overrides default value.
    :return: str
    """
    cfgfile = os.environ.get('CONFIG')
    if cfgfile:
        if os.path.exists(cfgfile):
            print_debug("Config file defined via envvar: %s" % cfgfile)
        else:
            raise ("File does not exist although defined CONFIG envvar: %s" % cfgfile)
    else:
        cfgfile = "./config.yaml"
        if os.path.exists(cfgfile):
            print_debug("Using module config file: %s" % cfgfile)
        else:
            cfgfile = "/usr/share/moduleframework/docs/example-config-minimal.yaml"
            print_debug("Using default minimal config, you have to use URL envvar for testing "
                        "your images or repos: %s" % cfgfile)

    try:
        with open(cfgfile, 'r') as ymlfile:
            xcfg = yaml.load(ymlfile.read())
        doc_name = ['modularity-testing', 'meta-test-family', 'meta-test']
        if xcfg.get('document') not in doc_name:
            raise ConfigExc("bad yaml file: item (%s)" %
                            doc_name, xcfg.get('document'))
        if not xcfg.get('name'):
            raise ConfigExc("Missing (name:) in config file")
        return xcfg
    except IOError:
        raise ConfigExc(
            "Error: File '%s' doesn't appear to exist or it's not a YAML file. "
            "Tip: If the CONFIG envvar is not set, mtf-generator looks for './config'."
            % cfgfile)
    return None


def get_compose_url():
    """
    Return Compose URL.

    If the **COMPOSEURL** ennvar is not set, it's defined from the ``./config.yaml``.

    :return: str
    """
    compose_url = os.environ.get('COMPOSEURL')
    if not compose_url:
        readconfig = CommonFunctions()
        readconfig.loadconfig()
        try:
            if readconfig.config.get("compose-url"):
                compose_url = readconfig.config.get("compose-url")
            elif readconfig.config['module']['rpm'].get("repo"):
                compose_url = readconfig.config['module']['rpm'].get("repo")
            else:
                compose_url = readconfig.config['module']['rpm'].get("repos")[0]
        except AttributeError:
            return None
    return compose_url


def get_modulemdurl():
    """
    Read a moduleMD file.

    If the **MODULEMDURL** envvar is not set, module-url section of
    the ``config.yaml`` file is checked. If none of them is set, then
    the ***COMPOSE_URL* envvar is checked.

    :return: string
    """
    mdf = os.environ.get('MODULEMDURL')
    return mdf


class CommonFunctions(object):
    """
    Basic class to read configuration data and execute commands on a host machine.
    """
    config = None
    modulemdConf = None

    def __init__(self, *args, **kwargs):
        self.config = None
        self.modulemdConf = None
        self.moduleName = None
        self.source = None
        self.arch = None
        self.sys_arch = None
        self.dependencylist = {}
        self.moduledeps = None
        self.is_it_module = False
        # general use case is to have forwarded services to host (so thats why it is same)
        self.ipaddr = trans_dict["HOSTIPADDR"]
        trans_dict["GUESTARCH"] = self.getArch()
        self.loadconfig()

    def loadconfig(self):
        """
        Load configuration from config.yaml file.

        :return: None
        """
        self.config = get_config()
        self.info = self.config.get("module",{}).get(get_backend_parent_config_module())
        # if there is inheritance join both dictionary
        self.info.update(self.config.get("module",{}).get(get_module_type()))
        if not self.info:
            raise ConfigExc("There is no section for (module: -> %s:) in the configuration file." %
                            get_base_module())

        if self.config.get('modulemd-url') and get_if_module():
            self.is_it_module = True
            self.getModulemdYamlconfig()
        else:
            trans_dict["GUESTPACKAGER"] = "yum -y"

        self.moduleName = sanitize_text(self.config['name'])
        self.source = self.config.get('source')
        self.set_url()

    def set_url(self, url=None, force=False):
        """
        Set url via parameter or via URL envvar
        It is repo or image name.

        :envvar: **URL=url://localtor or docker url locator** overrides default value.
        :param url:
        :param force:
        :return:
        """
        url = url or get_url()
        if url and (not self.info.get("url") or force):
                self.info["url"] = url
        else:
            if get_backend_parent_config_module() == "docker":
                self.info["url"]=self.info.get("container")
            elif get_backend_parent_config_module() == "rpm":
                self.info["url"] = self.info.get("repo") or self.info.get("repos")
        # url has to be dict in case of rpm/nspanw (it is allowed to use ; as separator for more repositories)
        if get_backend_parent_config_module() == "rpm" and isinstance(self.info["url"], str):
            self.info["url"] = self.info["url"].split(";")

    def get_url(self):
        """
        get location of repo(s) or image

        :return:
        """
        return self.info.get("url")


    def getArch(self):
        """
        Get system architecture.

        :return: str
        """
        if not self.sys_arch:
            self.sys_arch = self.runHost(command='uname -m', verbose=False).stdout.strip()
        return self.sys_arch

    def runHost(self, command="ls /", **kwargs):
        """
        Run commands on a host.

        :param (str): command to exectute
        ** kwargs: avocado process.run params like: shell, ignore_status, verbose
        :return: avocado.process.run
        """
        try:
            formattedcommand = command.format(**trans_dict)
        except KeyError:
            raise ModuleFrameworkException(
                "Command is formatted by using trans_dict. If you want to use "
                "brackets { } in your code, please use {{ }}. Possible values "
                "in trans_dict are: %s. \nBAD COMMAND: %s"
                % (trans_dict, command))
        return process.run("%s" % formattedcommand, **kwargs)


    def get_test_dependencies(self):
        """
        Get test dependencies from a configuration file

        :return: list of test dependencies
        """
        return self.config.get('testdependencies', {}).get('rpms', [])

    def installTestDependencies(self, packages=None):
        """
        Install packages on a host machine to prepare a test environment.

        :param (list): packages to install. If not specified, rpms from config.yaml
                       will be installed.
        :return: None
        """
        if not packages:
            packages = self.get_test_dependencies()

        if packages:
            print_info("Installs test dependencies: ", packages)
            # you have to have root permission to install packages:
            try:
                self.runHost(
                    "{HOSTPACKAGER} install " +
                    " ".join(packages),
                    ignore_status=False, verbose=is_debug())
            except process.CmdError as e:
                raise CmdExc("Installation failed; Do you have permission to do that?", e)


    def getPackageList(self, profile=None):
        """
        Return list of packages what has to be installed inside module

        :param profile: get list for intended profile instead of default method for searching
        :return: list of packages (rpms)
        """
        package_list = []
        if not profile:
            if 'packages' in self.config:
                packages_rpm = self.config.get('packages',{}).get('rpms', [])
                packages_profiles = []
                for profile_in_conf in self.config.get('packages',{}).get('profiles',[]):
                    packages_profiles += self.getModulemdYamlconfig()['data']['profiles'][profile_in_conf]['rpms']
                package_list += packages_rpm + packages_profiles
        else:
            package_list += self.getModulemdYamlconfig()['data']['profiles'][profile]['rpms']
        print_info("PCKGs to install inside module:", package_list)
        return package_list

    def getModuleDependencies(self):
        """
        Return module dependencies.

        :return: list
        """

        return self.dependencylist

    def getModulemdYamlconfig(self, urllink=None):
        """
        Return moduleMD file yaml object.
        It can be used also for loading another yaml file via url parameter

        :param (str): url link to load. Default url defined in the `config.yaml` file,
                      can be overridden by the **CONFIG** envvar.
        :return: dict
        """
        link = {"data": {}}
        if urllink:
            modulemd = urllink
        elif self.is_it_module:
            if self.modulemdConf:
                return self.modulemdConf
            else:
                modulemd = get_modulemdurl()
                if not modulemd:
                    modulemd = self.config.get("modulemd-url")
        else:
            return link
        try:
            ymlfile = urllib.urlopen(modulemd)
            link = yaml.load(ymlfile)
        except IOError as e:
            raise ConfigExc("File '%s' cannot be load" % modulemd, e)
        except yaml.parser.ParserError as e:
            raise ConfigExc("Module MD file contains errors: '%s'" % e, modulemd)
        if not urllink:
            self.modulemdConf = link
        return link


    def getIPaddr(self):
        """
        Return protocol (IP or IPv6) address on a guest machine.

        In many cases it should be same as a host machine's and a port
        should be forwarded to a host.

        :return: str
        """
        return self.ipaddr

    def _callSetupFromConfig(self):
        """
        Internal method, do not use it anyhow

        :return: None
        """
        if self.info.get("setup"):
            self.runHost(self.info.get("setup"), shell=True, ignore_bg_processes=True, verbose=is_not_silent())

    def _callCleanupFromConfig(self):
        """
        Internal method, do not use it anyhow

        :return: None
        """
        if self.info.get("cleanup"):
            self.runHost(self.info.get("cleanup"), shell=True, ignore_bg_processes=True, verbose=is_not_silent())

    def run(self, command, **kwargs):
        """
        Run command inside module, for local based it is same as runHost

        :param command: str of command to execute
        :param kwargs: dict from avocado.process.run
        :return: avocado.process.run
        """

        return self.runHost('bash -c "%s"' % sanitize_cmd(command), **kwargs)

    def status(self, command="/bin/true"):
        """
        Return status of module

        :param command: which command used for do that. it could be defined inside config
        :return: bool
        """
        try:
            command = self.info.get('status') or command
            a = self.run(command, shell=True, ignore_bg_processes=True, verbose=is_not_silent())
            print_debug("command:", a.command, "stdout:", a.stdout, "stderr:", a.stderr)
            return True
        except BaseException:
            return False

    def start(self, command="/bin/true"):
        """
        start the RPM based module (like systemctl start service)

        :param command: Do not use it directly (It is defined in config.yaml)
        :return: None
        """
        command = self.info.get('start') or command
        self.run(command, shell=True, ignore_bg_processes=True, verbose=is_not_silent())
        self.status()

    def stop(self, command="/bin/true"):
        """
        stop the RPM based module (like systemctl stop service)

        :param command: Do not use it directly (It is defined in config.yaml)
        :return: None
        """
        command = self.info.get('stop') or command
        self.run(command, shell=True, ignore_bg_processes=True, verbose=is_not_silent())


    def install_packages(self, packages=None):
        """
        Install packages in config (by config or via parameter)

        :param packages:
        :return:
        """
        if not packages:
            packages = self.getPackageList()
        if packages:
            a = self.run("%s install %s" % (trans_dict["GUESTPACKAGER"]," ".join(packages)),
                         ignore_status=True,
                         verbose=False)
            if a.exit_status == 0:
                print_info("Packages installed via {GUESTPACKAGER}", a.stdout)
            else:
                print_info(
                    "Nothing installed via {GUESTPACKAGER}, but package list is not empty",
                    packages)
                raise CmdExc("ERROR: Unable to install packages inside: %s" % packages)

    def tearDown(self):
        """
        cleanup enviroment and call cleanup from config

        :return: None
        """
        if get_if_do_cleanup():
            self.stop()
            self._callCleanupFromConfig()
        else:
            print_info("TearDown phase skipped.")


def list_modules_from_config():
    modulelist = get_config().get("module").keys()
    if "rpm" in modulelist and "nspawn" not in modulelist:
        modulelist.append("nspawn")
    return modulelist


def get_base_module():
    module_type = get_module_type()
    parent = module_type
    if module_type not in get_backend_list():
        parent = get_config().get("module",{}).get(module_type, {}).get("parent")
        if not parent:
            raise ModuleFrameworkException("Module (%s) does not provide parent backend parameter (there are: %s)" %
                                           (module_type, get_backend_list()))
    return parent


def get_backend_list():
    base_module_list = ["rpm", "nspawn", "docker"]
    return base_module_list


def get_backend_parent_config_module():
    module = get_base_module()
    if module == "nspawn":
        module = "rpm"
    return module


def get_module_type():
    """
    Return which module are you actually using.

    :return: str
    """
    amodule = os.environ.get('MODULE')
    readconfig = get_config()
    if "default_module" in readconfig and readconfig[
        "default_module"] is not None and amodule is None:
        amodule = readconfig["default_module"]
    if amodule in list_modules_from_config():
        return amodule
    else:
        raise ModuleFrameworkException("Unsupported MODULE={0}".format(amodule),
                                       "supported are: %s" % list_modules_from_config())
