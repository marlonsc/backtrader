#!/usr/bin/env python
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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


__all__ = ["BacktraderError", "StrategySkipError"]


class BacktraderError(Exception):
    """Base exception for all other exceptions."""


class StrategySkipError(BacktraderError):
    """Requests the platform to skip this strategy for backtesting.

    To be
    raised during the initialization (``__init__``) phase of the instance
    """


class ModuleImportError(BacktraderError):
    """Raised if a class requests a module to be present to work and it cannot be
    imported."""

    def __init__(self, message, *args):
        super().__init__(message)
        self.args = args


class FromModuleImportError(ModuleImportError):
    """Raised if a class requests a module to be present to work and it cannot be
    imported."""

    def __init__(self, message, *args):
        super().__init__(message, *args)
