"""
Azure Functions Boot - A powerful framework for building Azure Functions applications
with built-in dependency injection and hexagonal architecture support.
"""

# Bootstrap
from azfunc_boot.bootstrap.app_factory import AppFactory, create_app

# Dependency Injection
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.di.scope import ScopeManager

# MVC
from azfunc_boot.mvc.base_controller import BaseController
from azfunc_boot.mvc.controller_discovery import ControllerDiscovery

# Registry
from azfunc_boot.registry.base_service_registry import (
    BaseServiceRegistry,
    register_service,
)
from azfunc_boot.registry.discovery import RegistryManager

# Common
from azfunc_boot.common.disposable import IDisposable
from azfunc_boot.common.exceptions.not_found_error import NotFoundError
from azfunc_boot.common.exceptions.validation_error import ValidationError
from azfunc_boot.config.configuration import Configuration
__version__ = "0.1.0"
__all__ = [
    # Bootstrap
    "AppFactory",
    "create_app",
    # Dependency Injection
    "DependencyContainer",
    "ScopeManager",
    # MVC
    "BaseController",
    "ControllerDiscovery",
    # Registry
    "BaseServiceRegistry",
    "register_service",
    "RegistryManager",
    # Common
    "IDisposable",
    "NotFoundError",
    "ValidationError",
    # Configuration
    "Configuration",
]
