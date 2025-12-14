"""Property-based tests для Logger."""

import json
import sys
from io import StringIO
from hypothesis import given, strategies as st, settings

sys.path.insert(0, ".")
from lib.logger import Logger, LogLevel


# **Feature: pve-lxc-v2, Property 5: JSON логирование валидно**
@settings(max_examples=100)
@given(message=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
def test_json_logging_valid(message):
    """JSON вывод должен быть валидным с полями level, message, timestamp."""
    logger = Logger(json_output=True)
    
    captured = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    
    try:
        logger.info(message)
    finally:
        sys.stdout = old_stdout
    
    output = captured.getvalue().strip()
    data = json.loads(output)
    
    assert "level" in data
    assert "message" in data
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["message"] == message


# **Feature: pve-lxc-v2, Property 6: Результат команды содержит статус**
@settings(max_examples=100)
@given(success=st.booleans())
def test_result_contains_status(success):
    """result() должен содержать поле success и при failure - error_code."""
    logger = Logger(json_output=True)
    
    captured = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    
    try:
        logger.result(success)
    finally:
        sys.stdout = old_stdout
    
    output = captured.getvalue().strip()
    data = json.loads(output)
    
    assert "success" in data
    assert data["success"] == success
    if not success:
        assert "error_code" in data


# **Feature: pve-lxc-v2, Property 7: Ошибка содержит контекст**
@settings(max_examples=100)
@given(
    message=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    cmd=st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),
    param=st.text(min_size=1, max_size=30).filter(lambda x: x.strip())
)
def test_error_contains_context(message, cmd, param):
    """Ошибка должна содержать context с командой и параметрами."""
    logger = Logger(json_output=True)
    logger.set_context(command=cmd, params=param)
    
    captured = StringIO()
    old_stderr = sys.stderr
    sys.stderr = captured
    
    try:
        logger.error(message)
    finally:
        sys.stderr = old_stderr
    
    output = captured.getvalue().strip()
    data = json.loads(output)
    
    assert "context" in data
    assert "command" in data["context"]
    assert data["context"]["command"] == cmd


# **Feature: pve-lxc-v2, Property 13: Прогресс содержит current и total**
@settings(max_examples=100)
@given(
    message=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    current=st.integers(min_value=1, max_value=100),
    total=st.integers(min_value=1, max_value=100)
)
def test_progress_contains_current_total(message, current, total):
    """step() с прогрессом должен содержать current/total."""
    logger = Logger(json_output=True)
    
    captured = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    
    try:
        logger.step(message, current=current, total=total)
    finally:
        sys.stdout = old_stdout
    
    output = captured.getvalue().strip()
    data = json.loads(output)
    
    assert "current" in data
    assert "total" in data
    assert data["current"] == current
    assert data["total"] == total
