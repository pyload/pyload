# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import configparser
import io
import logging
import os

import semver
from future import standard_library
from future.builtins import int, object

from pyload.__about__ import __version_info__
from pyload.config import default
from pyload.config.exceptions import (AlreadyExistsKeyError, InvalidValueError,
                                      VersionMismatchError)
from pyload.config.types import InputType
from pyload.utils import parse
from pyload.utils.check import isiterable
from pyload.utils.convert import to_bytes, to_str
from pyload.utils.fs import fullpath
from pyload.utils.layer.legacy.collections import OrderedDict
from pyload.utils.struct import InscDict
from pyload.utils.web.check import isendpoint
from pyload.utils.web.parse import endpoint, socket

standard_library.install_aliases()


def _parse_address(value):
    address = value.replace(',', ':')
    return (endpoint if isendpoint(address) else socket)(address)


convert_map = {
    InputType.NA: lambda x: x,
    InputType.Str: to_str,
    InputType.Int: int,
    InputType.File: fullpath,
    InputType.Folder: lambda x: os.path.dirname(fullpath(x)),
    InputType.Password: to_str,
    InputType.Bool: bool,
    InputType.Float: float,
    # InputType.Octal: lambda x: oct(int(x, 8)),
    InputType.Size: parse.bytesize,
    InputType.Address: _parse_address,
    InputType.Bytes: to_bytes,
    InputType.StrList: parse.entries
}


class ConfigOption(object):

    __slots__ = ['allowed_values', 'default', 'desc', 'label', 'parser',
                 'type', 'value']

    DEFAULT_TYPE = InputType.Str

    def __init__(self, parser, value, label=None, desc=None,
                 allowed_values=None, input_type=None):
        self.parser = parser
        self._setup_type(input_type)
        self._setup_value(value)
        self._setup_allowed(allowed_values)
        self._setup_info(label, desc)

    def _setup_info(self, label, desc):
        self.label = '' if label is None else to_str(label)
        self.desc = '' if desc is None else to_str(desc)

    def _setup_type(self, input_type):
        if input_type is None:
            self.type = self.DEFAULT_TYPE
        elif input_type in InputType:
            self.type = input_type
        else:
            raise InvalidValueError(input_type)

    def _setup_value(self, value):
        self.value = self.default = self._normalize_value(value)

    def _setup_allowed(self, allowed):
        if allowed is None:
            self.allowed_values = ()
        else:
            self.allowed_values = tuple(
                self._normalize_value(v) for v in allowed)

    def _normalize_value(self, value):
        return value if value is None else convert_map[self.type](value)

    def reset(self):
        self.value = self.default

    def get(self):
        return self.value

    def get_default(self):
        return self.default

    def set(self, value, store=False):
        norm_value = self._normalize_value(value)
        if self.allowed_values and norm_value not in self.allowed_values:
            raise InvalidValueError(value)
        if self.value == norm_value:
            return
        self.value = norm_value
        if store:
            self.parser.store()


class ConfigSection(InscDict):
    """Provides dictionary like access for configparser."""
    __slots__ = ['desc', 'label', 'parser']

    SEPARATOR = '|'

    def __init__(self, parser, config=None, label=None, desc=None):
        super(ConfigSection, self).__init__()

        self.parser = parser
        self.label = '' if label is None else to_str(label)
        self.desc = '' if desc is None else to_str(desc)

        if config is not None:
            self.update(config)

    def _to_configentry(self, value, sect=False):
        if isinstance(value, (ConfigOption, ConfigSection)):
            entry_obj = value
        else:
            func = ConfigSection if sect else ConfigOption
            entry_obj = func(self.parser, *value)
        return entry_obj

    def reset(self):
        for item in self.values():
            item.reset()

    def update(self, iterable):
        config = ((items[0], self._to_configentry(*items[1:]))
                  for items in dict(iterable).items())
        return super(ConfigSection, self).update(config)

    def is_section(self, name):
        return isinstance(self.__getitem__(name), ConfigSection)

    def is_option(self, name):
        return isinstance(self.__getitem__(name), ConfigOption)

    def set(self, name, arg, *args, **kwargs):
        item = self.__getitem__(name)
        item.set(arg, *args, **kwargs)

    def get(self, name, *names):
        item = self.__getitem__(name)
        try:
            return item.get(*names)
        except TypeError:
            return item

    def get_default(self, name, *names):
        return self.__getitem__(name).get_default(*names)

    def get_section(self, name):
        if not self.is_section(name):
            raise InvalidValueError(name)
        return self.__getitem__(name)

    def get_option(self, name):
        if self.is_section(name):
            raise InvalidValueError(name)
        return self.__getitem__(name)

    def add_section(self, name,
                    config=None, label=None, desc=None, store=None):

        if self.SEPARATOR in name:
            raise InvalidValueError(name)
        if name.lower() in self.lowerkeys():
            raise AlreadyExistsKeyError(name)
        if label is None:
            label = name.strip().capitalize()

        section = ConfigSection(self.parser, config, label, desc)
        self.__setitem__(name, section)

        if store or (store is None and config):
            self.parser.store()

        return section

    def add_option(self, name, value, label=None, desc=None,
                   allowed_values=None, input_type=None, store=True):
        if name.lower() in self.lowerkeys():
            raise AlreadyExistsKeyError(name)
        if label is None:
            label = name.strip().capitalize()

        option = ConfigOption(
            self.parser, value, label, desc, allowed_values, input_type)
        self.__setitem__(name, option)

        if store:
            self.parser.store()

        return option

    # def add(self, *args, **kwargs):
        # sectflag = kwargs.pop('section', False)
        # optflag = kwargs.pop('option', True)
        # func = self.add_section if sectflag or not optflag else self.add_option
        # return func(*args, **kwargs)

    # def __str__(self):
        # pass


class ConfigParser(InscDict):

    __slots__ = ['log', 'parser', 'path', 'version', 'version_info']

    DEFAULTSECT = configparser.DEFAULTSECT
    SEPARATOR = '|'

    def __init__(
            self,
            filename,
            config=default.config,
            version=__version_info__,
            logger=None):
        super(ConfigParser, self).__init__()
        if config is not None:
            self.update(config)

        self.path = fullpath(filename)
        self.version, self.version_info = self._parse_version(version)

        if logger is None:
            self.log = logging.getLogger('null')
            self.log.addHandler(logging.NullHandler())
        else:
            self.log = logger

        try:
            self.retrieve()

        except VersionMismatchError:
            self._backup_fileconfig()

        except IOError:
            pass

        else:
            self.store()
            return

    def _backup_fileconfig(self):
        path = self.path
        name, ext = os.path.splitext(path)
        rename = os.rename
        idx = 0
        while True:
            try:
                return rename(path, '{0}{1}{2}.old'.format(
                    name, '({0})'.format(idx) if idx else '', ext))
            except OSError:
                idx += 1

    def _parse_version(self, value):
        if isinstance(value, semver.VersionInfo):
            version_info = value
        else:
            version_info = semver.parse_version_info(value)

        version = semver.format_version(*tuple(version_info))
        return version, version_info

    def _make_sections(self, section_id):
        section_names = section_id.split(self.SEPARATOR)
        section = self

        for idx, name in enumerate(section_names):
            try:
                section = section.__getitem__(name)
            except KeyError:
                for subname in section_names[idx:]:
                    section = section.add_section(subname, store=False)
                break

        return section

    def _check_version(self, version):
        if not version:
            raise VersionMismatchError

        version_info = self._parse_version(version)[1]
        if version_info[:2] != self.version_info[:2]:
            raise VersionMismatchError

    def _new_parser(self, defaults=None):
        return configparser.ConfigParser(
            defaults=defaults,
            allow_no_value=True,
            default_section=self.DEFAULTSECT)

    def _make_options(self, section, section_config):
        for option_name, option_value in section_config.items():
            try:
                section.set(option_name, option_value)
            except KeyError:
                section.add_option(option_name, option_value, store=False)

    def _to_configentry(self, value):
        if isinstance(value, ConfigSection):
            entry_obj = value
        else:
            entry_obj = ConfigSection(self, *value)
        return entry_obj

    def reset(self):
        for item in self.values():
            item.reset()

    def set(self, name, arg, *args, **kwargs):
        item = self.__getitem__(name)
        item.set(arg, *args, **kwargs)

    def get(self, name, *names):
        item = self.__getitem__(name)
        try:
            return item.get(*names)
        except TypeError:
            return item

    def get_default(self, name, *names):
        return self.__getitem__(name).get_default(*names)

    def update(self, iterable):
        config = [(name, self._to_configentry(value))
                  for name, value in dict(iterable).items()]
        return super(ConfigParser, self).update(config)

    def add_section(self, name,
                    config=None, label=None, desc=None, store=None):

        if name.lower() == self.DEFAULTSECT.lower():
            raise InvalidValueError(name)
        if self.SEPARATOR in name:
            raise InvalidValueError(name)
        if name.lower() in self.lowerkeys():
            raise AlreadyExistsKeyError(name)
        if label is None:
            label = name.strip().capitalize()

        section = ConfigSection(self, config, label, desc)
        self.__setitem__(name, section)

        if store or (store is None and config):
            self.store()

        return section

    def retrieve(self):
        parser = self._new_parser()

        with io.open(self.path) as fp:
            parser.read_file(fp)

        version = parser.get(self.DEFAULTSECT, 'version', fallback=None)
        self._check_version(version)

        for section_id in parser.sections():
            section = self._make_sections(section_id)
            self._make_options(section, parser[section_id])

    def _to_filevalue(self, value):
        return ','.join(map(to_str, value)) if isiterable(value) else value

    def _to_fileconfig(self, section, section_name):
        config = OrderedDict()

        for name, item in section.loweritems():
            if section.is_section(name):
                sub_name = '{0}{1}{2}'.format(
                    section_name, self.SEPARATOR, name)
                fc = self._to_fileconfig(item, sub_name)
                config.update(fc)
            else:
                fv = self._to_filevalue(item.get())
                config.setdefault(section_name, OrderedDict())[name] = fv

        return config

    def _gen_fileconfig(self):
        config = OrderedDict()

        for name, item in self.loweritems():
            fc = self._to_fileconfig(item, name)
            config.update(fc)

        return config

    def store(self):
        config = self._gen_fileconfig()
        parser = self._new_parser({'version': self.version})
        parser.read_dict(config)
        with io.open(self.path, 'w') as fp:
            parser.write(fp)

    # def __str__(self):
        # pass
