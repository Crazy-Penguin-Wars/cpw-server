import importlib.util
import inspect
import os
import pkgutil

__all__ = []
AVAILABLE_COMMANDS = {}

for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    spec = loader.find_spec(name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        full_path = inspect.getsourcefile(module)
        file_name = os.path.basename(full_path)[:-3]

        for member_name, value in inspect.getmembers(module):
            if member_name.startswith("__"):
                continue

            globals()[member_name] = value
            __all__.append(member_name)

            if (
                callable(value)
                and getattr(value, "__module__", None) == module.__name__
                and member_name.startswith("handle_")
            ):
                if file_name in AVAILABLE_COMMANDS:
                    raise ValueError(
                        f"Duplicate handler in {file_name}: "
                        f"{AVAILABLE_COMMANDS[file_name].__name__} and {member_name}"
                    )
                AVAILABLE_COMMANDS[file_name] = value