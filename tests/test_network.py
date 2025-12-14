"""Property-based tests для Network."""

import sys
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings, assume

sys.path.insert(0, ".")
from cli.core.network import Network, HostNetwork
from lib.logger import Logger


def make_mock_network():
    """Создать Network с замоканными системными вызовами."""
    logger = Logger(json_output=False)
    network = Network(logger)
    return network


# **Feature: pve-lxc-v2, Property 1: IP диапазон возвращает IP в диапазоне**
@settings(max_examples=100)
@given(
    start=st.integers(min_value=1, max_value=200),
    end=st.integers(min_value=1, max_value=254)
)
def test_ip_range_returns_ip_in_range(start, end):
    """IP из диапазона должен иметь последний октет в [start, end]."""
    assume(start <= end)
    
    network = make_mock_network()
    
    # Мокаем get_host_network
    mock_host = HostNetwork(ip="192.168.1.10", mask="24", gateway="192.168.1.1", interface="vmbr0")
    
    # Мокаем ping чтобы первый IP был свободен
    with patch.object(network, 'get_host_network', return_value=mock_host):
        with patch.object(network, 'ping', return_value=False):  # IP свободен
            ip, mask, gateway = network.resolve_ip(f"{start}-{end}")
            
            # Проверяем что последний октет в диапазоне
            last_octet = int(ip.split(".")[-1])
            assert start <= last_octet <= end
            assert ip.startswith("192.168.1.")


# **Feature: pve-lxc-v2, Property 2: Полный IP возвращается без изменений**
@settings(max_examples=100)
@given(
    a=st.integers(min_value=1, max_value=254),
    b=st.integers(min_value=0, max_value=255),
    c=st.integers(min_value=0, max_value=255),
    d=st.integers(min_value=1, max_value=254),
    mask=st.integers(min_value=8, max_value=30)
)
def test_full_ip_returned_unchanged(a, b, c, d, mask):
    """Полный IP с маской возвращается без изменений."""
    network = make_mock_network()
    
    input_ip = f"{a}.{b}.{c}.{d}/{mask}"
    ip, returned_mask, gateway = network.resolve_ip(input_ip)
    
    assert ip == f"{a}.{b}.{c}.{d}"
    assert returned_mask == str(mask)
