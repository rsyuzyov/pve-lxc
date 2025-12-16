"""Тесты для lib/platform.py."""

import sys
from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st

from lib.platform import OSType, _detect_os, OS_TYPE


class TestOSType:
    """Тесты для OSType enum."""

    def test_os_type_is_valid_enum_member(self):
        """OS_TYPE должен быть валидным членом OSType enum."""
        assert isinstance(OS_TYPE, OSType)
        assert OS_TYPE in OSType

    def test_all_enum_values_exist(self):
        """Все ожидаемые значения должны существовать."""
        assert OSType.WINDOWS.value == "windows"
        assert OSType.LINUX.value == "linux"
        assert OSType.MACOS.value == "macos"


class TestDetectOS:
    """Тесты для _detect_os()."""

    def test_detect_windows(self):
        """win32 -> WINDOWS."""
        with patch.object(sys, 'platform', 'win32'):
            assert _detect_os() == OSType.WINDOWS

    def test_detect_macos(self):
        """darwin -> MACOS."""
        with patch.object(sys, 'platform', 'darwin'):
            assert _detect_os() == OSType.MACOS

    def test_detect_linux(self):
        """linux -> LINUX."""
        with patch.object(sys, 'platform', 'linux'):
            assert _detect_os() == OSType.LINUX

    def test_detect_unknown_defaults_to_linux(self):
        """Неизвестная платформа -> LINUX."""
        with patch.object(sys, 'platform', 'freebsd'):
            assert _detect_os() == OSType.LINUX


class TestPropertyBased:
    """Property-based тесты.
    
    **Feature: cross-platform, Property 1: OS_TYPE is always valid**
    """

    @given(platform=st.sampled_from(['win32', 'darwin', 'linux', 'freebsd', 'cygwin', 'aix']))
    def test_detect_os_always_returns_valid_ostype(self, platform: str):
        """
        *For any* sys.platform value, _detect_os() SHALL return a valid OSType enum member.
        
        **Feature: cross-platform, Property 1: OS_TYPE is always valid**
        **Validates: Requirements 1.1, 1.2**
        """
        with patch.object(sys, 'platform', platform):
            result = _detect_os()
            assert isinstance(result, OSType)
            assert result in OSType
