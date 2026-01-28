from unittest.mock import patch

from azfunc_boot.registry.base_service_registry import BaseServiceRegistry, register_service


class MockServiceRegistry(BaseServiceRegistry):
    def __init__(self):
        self.services_called = []
        super().__init__()

    @register_service
    def service_one(self):
        self.services_called.append("service_one")

    @register_service
    def service_two(self):
        self.services_called.append("service_two")

    def not_registered_service(self):
        self.services_called.append("not_registered_service")


class TestBaseServiceRegistry:
    def setup_method(self):
        self.service_registry = MockServiceRegistry()

    def test_register_service_decorator(self):
        assert getattr(self.service_registry.service_one, "_is_register_service", False) is True
        assert getattr(self.service_registry.service_two, "_is_register_service", False) is True
        assert getattr(self.service_registry.not_registered_service, "_is_register_service", False) is False

    def test_register_all_services_called(self):
        assert "service_one" in self.service_registry.services_called
        assert "service_two" in self.service_registry.services_called
        assert "not_registered_service" not in self.service_registry.services_called

    def test_register_all_services_with_exception(self):
        class FaultyServiceRegistry(BaseServiceRegistry):
            @register_service
            def good_service(self):
                # Intentionally empty for testing
                pass

            @register_service
            def faulty_service(self):
                raise ValueError("Error en el servicio")

        with patch("azfunc_boot.registry.base_service_registry.logging.error") as mock_error, patch(
            "azfunc_boot.registry.base_service_registry.logging.info"
        ) as mock_info:
            FaultyServiceRegistry()

            mock_info.assert_called_with("Service registered successfully: good_service")
            mock_error.assert_called_once_with("Error registering service 'faulty_service': Error en el servicio")
