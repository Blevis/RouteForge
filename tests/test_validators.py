import pytest

from src.core.validators import validate_node_name, validate_weight


def test_validate_node_name_rejects_empty():
    with pytest.raises(ValueError):
        validate_node_name("")


def test_validate_node_name_rejects_invalid_chars():
    with pytest.raises(ValueError):
        validate_node_name("node space")


def test_validate_weight_rejects_negative():
    with pytest.raises(ValueError):
        validate_weight(-1)


def test_validate_weight_rejects_nan():
    with pytest.raises(ValueError):
        validate_weight(float("nan"))


def test_validate_weight_accepts_zero():
    validate_weight(0.0)
