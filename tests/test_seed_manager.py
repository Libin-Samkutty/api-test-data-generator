"""Tests for seed management utilities."""
import random
import pytest
from api_test_data_generator.utils.seed_manager import set_seed, get_seed, reset_seed


class TestSeedManager:
    def setup_method(self):
        reset_seed()

    def test_set_and_get_seed(self):
        set_seed(123)
        assert get_seed() == 123

    def test_reset_seed(self):
        set_seed(42)
        reset_seed()
        assert get_seed() is None

    def test_deterministic_random(self):
        set_seed(0)
        val1 = random.random()

        set_seed(0)
        val2 = random.random()

        assert val1 == val2

    def test_default_seed_is_none(self):
        reset_seed()
        assert get_seed() is None
