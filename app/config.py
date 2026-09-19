"""Central, environment-driven application configuration.

No third-party settings library is required so configuration can be tested before
the GIS stack is installed. Values in the process environment override ``.env``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_VEHICLE_PROFILES = frozenset({"car", "motorbike"})


class ConfigurationError(ValueError):
    """Raised when application configuration is invalid."""


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read a conservative KEY=VALUE subset of dotenv syntax.

    This intentionally does not interpolate variables or execute shell syntax.
    """

    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"Invalid .env entry at {path}:{line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum():
            raise ConfigurationError(f"Invalid .env key at {path}:{line_number}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _as_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be true or false, got {value!r}")


def _as_positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {value!r}") from exc
    if parsed <= 0:
        raise ConfigurationError(f"{name} must be positive, got {parsed}")
    return parsed


def _resolve_path(raw_path: str, root: Path) -> Path:
    path = Path(raw_path).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


@dataclass(frozen=True, slots=True)
class MapConfig:
    """Settings that uniquely determine an OSM road graph download."""

    place: str = "Hanoi, Vietnam"
    vehicle_profile: str = "car"
    simplify: bool = True
    retain_all: bool = False
    truncate_by_edge: bool = True
    request_timeout_seconds: int = 180

    def __post_init__(self) -> None:
        if not self.place.strip():
            raise ConfigurationError("OSM_PLACE cannot be empty")
        if self.vehicle_profile not in SUPPORTED_VEHICLE_PROFILES:
            allowed = ", ".join(sorted(SUPPORTED_VEHICLE_PROFILES))
            raise ConfigurationError(
                f"OSM_VEHICLE_PROFILE must be one of {allowed}, got {self.vehicle_profile!r}"
            )
        if self.request_timeout_seconds <= 0:
            raise ConfigurationError("OSM_REQUEST_TIMEOUT_SECONDS must be positive")


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings and filesystem locations."""

    project_root: Path
    app_env: str
    log_level: str
    random_seed: int
    graph_cache_dir: Path
    traffic_provider: str
    tomtom_api_key: str | None
    here_api_key: str | None
    map: MapConfig

    def ensure_directories(self) -> None:
        self.graph_cache_dir.mkdir(parents=True, exist_ok=True)


def load_settings(
    *,
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
    project_root: Path = PROJECT_ROOT,
) -> Settings:
    """Load settings from defaults, a dotenv file, then process environment."""

    file_values = _read_dotenv(env_file or project_root / ".env")
    process_values = dict(os.environ if environ is None else environ)
    values = {**file_values, **process_values}

    profile = values.get("OSM_VEHICLE_PROFILE", "car").strip().lower()
    map_config = MapConfig(
        place=values.get("OSM_PLACE", "Hanoi, Vietnam").strip(),
        vehicle_profile=profile,
        simplify=_as_bool(values.get("OSM_SIMPLIFY", "true"), "OSM_SIMPLIFY"),
        retain_all=_as_bool(values.get("OSM_RETAIN_ALL", "false"), "OSM_RETAIN_ALL"),
        truncate_by_edge=_as_bool(
            values.get("OSM_TRUNCATE_BY_EDGE", "true"), "OSM_TRUNCATE_BY_EDGE"
        ),
        request_timeout_seconds=_as_positive_int(
            values.get("OSM_REQUEST_TIMEOUT_SECONDS", "180"),
            "OSM_REQUEST_TIMEOUT_SECONDS",
        ),
    )
    seed_raw = values.get("RANDOM_SEED", "42")
    try:
        random_seed = int(seed_raw)
    except ValueError as exc:
        raise ConfigurationError(f"RANDOM_SEED must be an integer, got {seed_raw!r}") from exc

    return Settings(
        project_root=project_root.resolve(),
        app_env=values.get("APP_ENV", "development").strip(),
        log_level=values.get("LOG_LEVEL", "INFO").strip().upper(),
        random_seed=random_seed,
        graph_cache_dir=_resolve_path(values.get("OSM_CACHE_DIR", "data/graph"), project_root),
        traffic_provider=values.get("TRAFFIC_PROVIDER", "synthetic").strip().lower(),
        tomtom_api_key=values.get("TOMTOM_API_KEY") or None,
        here_api_key=values.get("HERE_API_KEY") or None,
        map=map_config,
    )
