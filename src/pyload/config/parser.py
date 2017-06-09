# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import configparser
import logging
import os
from builtins import bytes, int, object, oct, range, str
from contextlib import closing

from future import standard_library

import semver
from pyload.utils import parse
from pyload.utils.check import isiterable, ismapping
from pyload.utils.fs import fullpath, open
from pyload.utils.layer.legacy.collections_ import OrderedDict
from pyload.utils.struct import InscDict
from pyload.utils.web.check import isendpoint
from pyload.utils.web.parse import endpoint, socket

from .__about__ import __version_info__
from .exceptions import (AlreadyExistsKeyError, InvalidValueError,
                         VersionMismatchError)
from .types import InputType

standard_library.install_aliases()


class ConfigOption(object):

    __slots__ = ['allowed_values', 'default', 'desc', 'label', 'parser',
                 'type', 'value']

    DEFAULT_TYPE = InputType.Str

    _convert_map = {
        InputType.NA: lambda x: x,
        InputType.Str: lambda x: "" if x is None else str(x),
        InputType.Int: lambda x: 0 if x is None else int(x),
        InputType.File: lambda x: "" if x is None else fullpath(x),
        InputType.Folder:
            lambda x: "" if x is None else os.path.dirname(fullpath(x)),
        InputType.Password: lambda x: "" if x is None else str(x),
        InputType.Bool:
            lambda x: parse.boolean(x) if isinstance(x, str) else bool(x),
        InputType.Float: lambda x: 0.0 if x is None else float(x),
        InputType.Tristate: lambda x: x if x is None else bool(x),
        InputType.Octal: lambda x: 0 if x is None else oct(x),
        InputType.Size: lambda x: 0 if x is None else parse.bytesize(x),
        InputType.Address:
            lambda x: (None, None) if x is None else (
                endpoint if isendpoint(x) else socket)(x),
        InputType.Bytes: lambda x: b"" if x is None else bytes(x),
        InputType.StrList:
            lambda l: [
                str(x) for x in l] if isiterable(l) else parse.entries(l)
    }

    def __init__(self, parser, value, label=None, desc=None,
                 allowed_values=None, input_type=None):
        self.__parser = parser

        self.type = None
        self.value = None
        self.default = None
        self.allowed_values = None
        self.label = None
        self.desc = None

        self._set_type(input_type)
        self._set_value(value)
        self._set_allowed(allowed_values)
        self._set_info(label, desc)

    def _set_info(self, label, desc):
        self.label = "" if label is None else str(label)
        self.desc = "" if desc is None else str(desc)

    def _set_type(self, input_type):
        if not input_type:
            input_type = self.DEFAULT_TYPE
        if input_type not in InputType:
            raise InvalidValueError(input_type)
        self.type = input_type

    def _set_value(self, value):
        self.value = self.default = self._normalize_value(value)

    def _set_allowed(self, allowed):
        if allowed:
            values = (self._normalize_value(v) for v in allowed)
        else:
            values = ()
        self.allowed_values = range(values)

    def _normalize_value(self, value):
        return self._convert_map[self.type](value)

    def reset(self):
        self.value = self.default

    def get(self):
        return self.value

    def get_default(self):
        return self.default

    def set(self, value, store=True):
        norm_value = self._normalize_value(value)
        if self.allowed_values:
            if norm_value not in self.allowed_values:
                raise InvalidValueError(value)
        if self.value == norm_value:
            return None
        self.value = norm_value
        if store:
            self.__parser.store()

    # def __str__(self):
        # pass


class ConfigSection(InscDict):
    """
    Provides dictionary like access for configparser.
    """
    __slots__ = ['desc', 'label', 'parser']

    SECTION_SEP = ':'

    def __init__(self, parser, config=None, label=None, desc=None):
        """
        Constructor.
        """
        self.__parser = parser
        self.label = "" if label is None else str(label)
        self.desc = "" if desc is None else str(desc)
        self.update(config or ())

    def _to_configentry(self, value):
        if isinstance(value, ConfigOption) or isinstance(value, ConfigSection):
            entry_obj = value
        else:
            entry_type = value[0]
            entry_args = value[1:]
            func = ConfigSection if entry_type == 'section' else ConfigOption
            entry_obj = func(self.__parser, *entry_args)
        return entry_obj

    def reset(self):
        for item in self.values():
            item.reset()

    def update(self, iterable):
        if ismapping(iterable):
            iterable = iterable.items()
        config = (
            (name, self._to_configentry(value)) for name, value in iterable)
        InscDict.update(self, config)

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

    def add_section(
            self, name, config=None, label=None, desc=None, store=None):
        if self.SECTION_SEP in name:
            raise InvalidValueError(name)
        if name.lower() in self.lowerkeys():
            raise AlreadyExistsKeyError(name)
        if label is None:
            label = name.strip().capitalize()
        section = ConfigSection(self.__parser, config, label, desc)
        self.__setitem__(name, section)
        if store or (store is None and config):
            self.__parser.store()
        return section

    def add_option(self, name, value, label=None, desc=None,
                   allowed_values=None, input_type=None, store=True):
        if name.lower() in self.lowerkeys():
            raise AlreadyExistsKeyError(name)
        if label is None:
            label = name.strip().capitalize()
        option = ConfigOption(
            self.__parser, value, label, desc, allowed_values, input_type)
        self.__setitem__(name, option)
        if store:
            self.__parser.store()
        return option

    def add(self, section, *args, **kwargs):
        func = self.add_section if section == 'section' else self.add_option
        return func(*args, **kwargs)

    # def __str__(self):
        # pass


class ConfigParser(ConfigSection):

    __slots__ = ['fp', 'lock', 'log', 'parser', 'path', 'version',
                 'version_info']

    DEFAULT_SECTION = configparser.DEFAULTSECT
    SELF_SECTION = ''

    def __init__(self, filename, config=None, version=__version_info__,
                 logger=None):
        self.path = fullpath(filename)
        self.version, self.version_info = self._parse_version(version)

        self.log = self._get_logger(logger)
        self.fp = open(filename, mode='ab+')

        ConfigSection.__init__(self, self, config)
        self._retrieve_fileconfig()

    def close(self):
        with closing(self.fp):
            self.store()

    def _get_logger(self, value):
        if value is False:
            logger = lambda *args, **kwgs: None
        else:
            logger = logging.getLogger(value)
        return logger

    def _retrieve_fileconfig(self):
        try:
            return self.retrieve()
        except VersionMismatchError:
            self.fp.close()
            os.rename(self.path, self.path + '.old')
            self.fp = open(self.path, mode='ab+')
        except Exception as e:
            self.log.error(str(e))
        self.log.warning(
            'Unable to parse configuration from `{0}`'.format(self.path))

    def _parse_version(self, value):
        if isinstance(value, semver.VersionInfo):
            version_info = value
        else:
            version_info = semver.parse_version_info(value)
        version = semver.format_version(*tuple(version_info))
        return version, version_info

    def _make_sections(self, section_id):
        section_names = section_id.split(self.SECTION_SEP)
        section = self
        for idx, name in enumerate(section_names):
            try:
                section = section.get_section(name)
            except KeyError:
                for name in section_names[idx:]:
                    section = section.add_section(name, store=False)
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
            default_section=self.DEFAULT_SECTION)

    def _make_options(self, section, section_config):
        for option_name, option_value in section_config.items():
            try:
                section.set(option_name, option_value)
            except KeyError:
                section.add_option(option_name, option_value, store=False)

    def add_section(
            self, name, config=None, label=None, desc=None, store=None):
        na = (self.DEFAULT_SECTION.lower(), self.SELF_SECTION.lower())
        if name.lower() in na:
            raise InvalidValueError(name)
        return ConfigSection.add_section(
            self, name, config, label, desc, store)

    def retrieve(self):
        parser = self._new_parser()
        parser.read_file(self.fp)

        version = parser.get(self.DEFAULT_SECTION, 'version', fallback=None)
        self._check_version(version)

        self._make_options(self, parser.pop(self.SELF_SECTION, {}))

        for section_id in parser.sections():
            section = self._make_sections(section_id)
            self._make_options(section, parser[section_id])

    def _to_filevalue(self, value):
        return ','.join(value) if isiterable(value) else value

    def _to_fileconfig(self, section, section_name):
        config = OrderedDict()
        for name, item in section.loweritems():
            if section.is_section(name):
                sub_name = '{0}{1}{2}'.format(
                    section_name, self.SECTION_SEP, name)
                fc = self._to_fileconfig(item, sub_name)
                config.update(fc)
            else:
                fv = self._to_filevalue(item.get())
                config.setdefault(section_name, OrderedDict())[name] = fv
        return config

    def _gen_fileconfig(self):
        config = OrderedDict((self.SELF_SECTION, OrderedDict()))
        for name, item in self.loweritems():
            if self.is_section(name):
                fc = self._to_fileconfig(item, name)
                config.update(fc)
            else:
                fv = self._to_filevalue(item.get())
                config[self.SELF_SECTION][name] = fv
        return config

    def store(self):
        config = self._gen_fileconfig()
        parser = self._new_parser({'version': self.version})
        parser.read_dict(config)
        parser.write(self.fp)

    # def __str__(self):
        # pass
