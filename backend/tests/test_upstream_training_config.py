from types import SimpleNamespace

import pytest

from app.api import training
from app.entity.db_models import DetectionScene, User
from app.entity.schemas import TrainingTaskCreate


@pytest.mark.asyncio
@pytest.mark.parametrize("options", [None, {"cos_lr": True, "mosaic": 0.3, "freeze": 2}])
async def test_start_endpoint_forwards_advanced_options(db_session, monkeypatch, tmp_path, options):
    """Catch options silently lost between API validation and the training worker."""
    user = User(username="config-owner", email="config@example.com", hashed_password="x")
    scene = DetectionScene(name="config-scene", display_name="Config", class_names=["scratch"])
    db_session.add_all([user, scene])
    db_session.commit()
    (tmp_path / "data.yaml").write_text("names: [scratch]\n", encoding="utf-8")
    monkeypatch.setattr(training.settings, "DATASET_BASE_DIR", str(tmp_path))
    captured = {}

    def start(**kwargs):
        captured.update(kwargs["config"])
        return SimpleNamespace(id=1, public_task_id="TR-1", task_uuid="config-task",
                               status="pending", model_name="yolo11n", epochs=10)

    monkeypatch.setattr(training.training_service, "start_training", start)
    monkeypatch.setattr(training.operation_log_service, "record", lambda *args, **kwargs: None)
    result = await training.start_training(
        TrainingTaskCreate(scene_id=scene.id, epochs=10, train_config=options),
        SimpleNamespace(state=SimpleNamespace()), idempotency_key="config-request",
        db=db_session, current_user=user,
    )
    assert result["status"] == "pending"
    assert captured["idempotency_key"] == "config-request"
    if options is None:
        assert captured["train_config"] == {}
    else:
        assert all(captured["train_config"][key] == value for key, value in options.items())
        assert all(value is not None for value in captured["train_config"].values())
