"""Property-based tests для ConfigLoader."""

import sys
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

sys.path.insert(0, ".")
from lib.config import ConfigLoader, ConfigError


# **Feature: pve-lxc-v2, Property 3: Приоритет конфигурации**
@settings(max_examples=100)
@given(
    default_val=st.integers(min_value=1, max_value=100),
    override_val=st.integers(min_value=101, max_value=200)
)
def test_config_priority(default_val, override_val):
    """Значение из более позднего слоя перезаписывает более ранний."""
    loader = ConfigLoader()
    # Первый слой
    loader.layers.append({"test_key": default_val})
    # Второй слой (должен перезаписать)
    loader.layers.append({"test_key": override_val})
    
    result = loader.merge()
    assert result["test_key"] == override_val


# **Feature: pve-lxc-v2, Property 4: Дефолты при отсутствии параметров**
@settings(max_examples=100)
@given(key=st.sampled_from(["container.cores", "container.memory", "network.bridge"]))
def test_defaults_when_not_specified(key):
    """Если параметр не указан, возвращается встроенное значение."""
    loader = ConfigLoader()
    value = loader.get(key)
    
    # Проверяем что значение не None (есть дефолт)
    assert value is not None
    
    # Проверяем конкретные дефолты
    if key == "container.cores":
        assert value == 2
    elif key == "container.memory":
        assert value == 2048
    elif key == "network.bridge":
        assert value == "vmbr0"


# **Feature: pve-lxc-v2, Property 12: Ошибка YAML содержит номер строки**
def test_yaml_error_contains_line_number():
    """Невалидный YAML должен выдать ошибку с номером строки."""
    invalid_yaml = """
valid_key: value
  invalid_indent: broken
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(invalid_yaml)
        f.flush()
        
        loader = ConfigLoader()
        try:
            loader._load_yaml(Path(f.name))
            assert False, "Should raise ConfigError"
        except ConfigError as e:
            # Ошибка должна содержать номер строки
            assert e.line is not None
            assert "Line" in str(e)


# Дополнительный тест для глубокого слияния
@settings(max_examples=100)
@given(
    base_val=st.integers(min_value=1, max_value=50),
    nested_val=st.integers(min_value=51, max_value=100)
)
def test_deep_merge_preserves_nested(base_val, nested_val):
    """Глубокое слияние сохраняет вложенные значения."""
    loader = ConfigLoader()
    loader.layers.append({"parent": {"child1": base_val, "child2": 999}})
    loader.layers.append({"parent": {"child1": nested_val}})
    
    result = loader.merge()
    # child1 перезаписан
    assert result["parent"]["child1"] == nested_val
    # child2 сохранён
    assert result["parent"]["child2"] == 999
