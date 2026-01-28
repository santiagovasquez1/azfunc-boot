import os
from unittest.mock import patch

from azfunc_boot.config.configuration import Configuration


class TestConfiguration:
    def test_inherits_from_dict(self):
        config = Configuration()
        assert isinstance(config, dict)

    def test_initializes_with_environment_variables(self):
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}, clear=True):
            config = Configuration()
            assert config["TEST_KEY"] == "test_value"

    def test_getitem_case_insensitive(self):
        with patch.dict(os.environ, {"MY_VAR": "my_value"}, clear=True):
            config = Configuration()
            assert config["my_var"] == "my_value"
            assert config["MY_VAR"] == "my_value"
            assert config["My_Var"] == "my_value"

    def test_getitem_returns_none_when_key_not_found(self):
        with patch.dict(os.environ, {}, clear=True):
            config = Configuration()
            assert config["NON_EXISTENT_KEY"] is None

    def test_behaves_like_dict(self):
        test_env = {"VAR1": "value1", "VAR2": "value2"}
        with patch.dict(os.environ, test_env, clear=True):
            config = Configuration()
            assert len(config) == len(test_env)
            assert "VAR1" in config
            assert config.get("VAR1") == "value1"
            assert list(config.keys()) == list(test_env.keys())
