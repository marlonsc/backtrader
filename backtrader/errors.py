#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2024 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

__all__ = ["BacktraderError", "StrategySkipError"]


class BacktraderError(Exception):
    """Base exception for all other exceptions"""


class StrategySkipError(BacktraderError):
    """Requests the platform to skip this strategy for backtesting. To be"""


class ModuleImportError(BacktraderError):
    """


    :raises be: imported

    """

    def __init__(self, message, *args):
        """

        :param message:
        :param *args:

        """
        super(ModuleImportError, self).__init__(message)
        self.args = args


class FromModuleImportError(ModuleImportError):
    """


    :raises be: imported

    """

    def __init__(self, message, *args):
        """

        :param message:
        :param *args:

        """
        super(FromModuleImportError, self).__init__(message, *args)
