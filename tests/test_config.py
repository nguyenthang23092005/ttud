import pytest

from app.config import PROJECT_ROOT, ConfigurationError, load_settings


def test_defaults_target_hanoi_and_local_cache() -> None:
    settings = load_settings(environ={}, project_root=PROJECT_ROOT)

    assert settings.map.place == "Hanoi, Vietnam"
    assert settings.map.vehicle_profile == "car"
    assert settings.graph_cache_dir == (PROJECT_ROOT / "data" / "graph").resolve()


def test_process_environment_overrides_dotenv() -> None:
    settings = load_settings(
        env_file=PROJECT_ROOT / "tests" / "fixtures" / "test.env",
        environ={"OSM_PLACE": "Ho Chi Minh City, Vietnam", "OSM_VEHICLE_PROFILE": "motorbike"},
        project_root=PROJECT_ROOT,
    )

    assert settings.map.place == "Ho Chi Minh City, Vietnam"
    assert settings.map.vehicle_profile == "motorbike"


def test_rejects_unknown_vehicle_profile() -> None:
    with pytest.raises(ConfigurationError, match="OSM_VEHICLE_PROFILE"):
        load_settings(environ={"OSM_VEHICLE_PROFILE": "flying-car"}, project_root=PROJECT_ROOT)
