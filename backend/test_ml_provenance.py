import asyncio
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import UUID

import numpy as np
import pandas as pd
from fastapi import HTTPException

from backend import ml_model
from backend.routes.ml import (
    TrainModelRequest,
    _apply_training_profile,
    _training_lock,
    _training_data_source,
    delete_model,
    train_model,
)


class MlProvenanceTests(unittest.TestCase):
    def test_render_demo_profile_clamps_training_to_free_instance_limits(self):
        request = TrainModelRequest(
            days=365,
            sequence_length=30,
            epochs=80,
            batch_size=32,
            validation_splits=5,
            stability_runs=5,
            model_types=["lstm", "mlp"],
            max_trials=8,
        )

        effective, profile = _apply_training_profile(request, "render_demo")

        self.assertEqual(profile, "render_demo")
        self.assertEqual(effective.days, 120)
        self.assertEqual(effective.sequence_length, 14)
        self.assertEqual(effective.epochs, 5)
        self.assertEqual(effective.batch_size, 8)
        self.assertEqual(effective.validation_splits, 2)
        self.assertEqual(effective.stability_runs, 1)
        self.assertEqual(effective.model_types, ["gru"])
        self.assertEqual(effective.max_trials, 1)

    def test_local_profile_preserves_requested_training_configuration(self):
        request = TrainModelRequest(days=240, epochs=12, model_types=["gru", "lstm"], max_trials=2)

        effective, profile = _apply_training_profile(request, None)

        self.assertIsNone(profile)
        self.assertEqual(effective, request)

    def test_unknown_training_profile_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Unsupported ML training profile"):
            _apply_training_profile(TrainModelRequest(), "unbounded")

    def test_training_source_classification_is_explicit(self):
        self.assertEqual(_training_data_source(TrainModelRequest(dataset_records=[{"price": 10}])), "uploaded_dataset")
        self.assertEqual(_training_data_source(TrainModelRequest(product_id="product-1")), "database_price_history")
        self.assertEqual(_training_data_source(TrainModelRequest()), "synthetic_generator")

    def test_report_discloses_training_data_source(self):
        payload = {
            "created_at": "2026-07-15T00:00:00",
            "data_source": "synthetic_generator",
            "best_model": {"model_type": "gru"},
            "metrics": {"mae": 1.0, "rmse": 2.0},
            "stability": {"consistency_score": 0.9},
            "eda": {},
            "cross_validation": [],
            "statistical_tests": {},
        }

        with TemporaryDirectory() as artifact_dir, patch.object(ml_model, "REPORT_DIR", artifact_dir):
            report_md, _ = ml_model._write_report("provenance_test", payload)

            with open(report_md, encoding="utf-8") as handle:
                report = handle.read()

        self.assertIn("Data source: synthetic_generator", report)

    def test_real_training_sources_reject_invalid_data_instead_of_generating_synthetic_data(self):
        invalid_frame = pd.DataFrame([{"date": "not-a-date", "price": "invalid"}])

        with self.assertRaisesRegex(RuntimeError, "uploaded_dataset.*valid daily price records"):
            ml_model.normalize_price_dataframe(invalid_frame, data_source="uploaded_dataset")

        with self.assertRaisesRegex(RuntimeError, "database_price_history.*valid daily price records"):
            ml_model.normalize_price_dataframe(pd.DataFrame(), data_source="database_price_history")

    def test_fold_scalers_are_fit_only_on_training_samples(self):
        X = np.asarray([
            [[1.0], [2.0]],
            [[2.0], [3.0]],
            [[3.0], [4.0]],
            [[400.0], [500.0]],
        ])
        y = np.asarray([10.0, 20.0, 30.0, 900.0])

        scaled = ml_model._scale_fold_data(
            X,
            y,
            train_idx=np.asarray([0, 1, 2]),
            validation_idx=np.asarray([3]),
        )

        self.assertAlmostEqual(scaled["feature_scaler"].mean_[0], 2.5)
        self.assertAlmostEqual(scaled["target_scaler"].mean_[0], 20.0)
        self.assertGreater(scaled["X_validation"][0, -1, 0], 100)

    def test_public_artifact_references_are_relative_to_artifact_directory(self):
        with TemporaryDirectory() as artifact_dir, patch.object(ml_model, "ARTIFACT_DIR", artifact_dir):
            reference = ml_model._artifact_reference(os.path.join(artifact_dir, "reports", "model_report.md"))

        self.assertEqual(reference, "reports/model_report.md")
        self.assertNotIn("C:\\Users", reference)

    def test_public_metadata_sanitizes_windows_paths_on_any_runtime(self):
        metadata = {"artifact_paths": {"model_path": r"C:\\Users\\Harry\\model.h5"}}

        public = ml_model._public_metadata(metadata)

        self.assertEqual(public["artifact_paths"]["model_path"], "model.h5")

    def test_holdout_metrics_are_evaluated_with_a_model_fit_only_on_earlier_samples(self):
        class RecordingModel:
            def __init__(self):
                self.fit_samples = None

            def fit(self, X, y, **kwargs):
                self.fit_samples = len(X)

            def predict(self, X, **kwargs):
                return np.zeros((len(X), 1))

        X = np.arange(20, dtype=float).reshape(10, 2, 1)
        y = np.arange(10, dtype=float)
        model = RecordingModel()

        with patch.object(ml_model, "_build_neural_model", return_value=model):
            metrics, actual, predicted = ml_model._evaluate_holdout_candidate(
                {"model_type": "gru"}, X, y, epochs=1, batch_size=2
            )

        self.assertEqual(model.fit_samples, 8)
        self.assertEqual(len(actual), 2)
        self.assertEqual(len(predicted), 2)
        self.assertIn("rmse", metrics)

    def test_disabled_training_and_delete_reject_before_artifact_or_tensorflow_work(self):
        with patch.dict(os.environ, {"ML_TRAINING_ENABLED": "false"}, clear=False), patch.object(
            ml_model, "train_model_suite"
        ) as train_suite:
            with self.assertRaises(HTTPException) as train_error:
                asyncio.run(train_model(TrainModelRequest()))

        self.assertEqual(train_error.exception.status_code, 403)
        train_suite.assert_not_called()

        with patch.dict(os.environ, {"ML_MODEL_DELETE_ENABLED": "false"}, clear=False), patch.object(
            ml_model, "delete_model_artifacts"
        ) as delete_artifacts:
            with self.assertRaises(HTTPException) as delete_error:
                asyncio.run(delete_model("bootstrap_price_forecaster"))

        self.assertEqual(delete_error.exception.status_code, 403)
        delete_artifacts.assert_not_called()

    def test_training_response_includes_effective_profile_and_configuration(self):
        suite_result = {
            "model_name": "demo",
            "best_model": {},
            "metrics": {},
            "baseline": {},
            "cross_validation": [],
            "stability": {},
            "statistical_tests": {},
            "eda": {},
            "data_source": "synthetic_generator",
            "artifact_paths": {},
        }
        with patch.dict(os.environ, {"ML_TRAINING_ENABLED": "true", "ML_TRAINING_PROFILE": "render_demo", "ML_TRAINING_KEY": "demo-key"}, clear=False), patch.object(
            ml_model, "train_model_suite", return_value=suite_result
        ):
            response = asyncio.run(train_model(TrainModelRequest(epochs=80, model_types=["lstm"]), training_key="demo-key"))

        self.assertEqual(response["training_profile"], "render_demo")
        self.assertEqual(response["training_config"]["epochs"], 5)
        self.assertEqual(response["training_config"]["model_types"], ["gru"])

    def test_training_key_rejects_missing_or_wrong_value_before_tensorflow_work(self):
        with patch.dict(os.environ, {"ML_TRAINING_ENABLED": "true", "ML_TRAINING_KEY": "correct-key"}, clear=False), patch.object(
            ml_model, "train_model_suite"
        ) as train_suite:
            for training_key in (None, "wrong-key"):
                with self.subTest(training_key=training_key), self.assertRaises(HTTPException) as auth_error:
                    asyncio.run(train_model(TrainModelRequest(), training_key=training_key))

                self.assertEqual(auth_error.exception.status_code, 401)

        train_suite.assert_not_called()

    def test_render_demo_without_configured_training_key_fails_closed(self):
        with patch.dict(
            os.environ,
            {"ML_TRAINING_ENABLED": "true", "ML_TRAINING_PROFILE": "render_demo"},
            clear=True,
        ), patch.object(ml_model, "train_model_suite") as train_suite:
            with self.assertRaises(HTTPException) as config_error:
                asyncio.run(train_model(TrainModelRequest()))

        self.assertEqual(config_error.exception.status_code, 503)
        train_suite.assert_not_called()

    def test_correct_training_key_allows_training(self):
        suite_result = {
            "model_name": "local_model",
            "best_model": {},
            "metrics": {},
            "baseline": {},
            "cross_validation": [],
            "stability": {},
            "statistical_tests": {},
            "eda": {},
            "data_source": "synthetic_generator",
            "artifact_paths": {},
        }
        with patch.dict(os.environ, {"ML_TRAINING_ENABLED": "true", "ML_TRAINING_KEY": "correct-key"}, clear=False), patch.object(
            ml_model, "train_model_suite", return_value=suite_result
        ) as train_suite:
            asyncio.run(train_model(TrainModelRequest(), training_key="correct-key"))

        train_suite.assert_called_once()

    def test_render_demo_uses_a_unique_server_generated_model_name(self):
        suite_result = {
            "model_name": "placeholder",
            "best_model": {},
            "metrics": {},
            "baseline": {},
            "cross_validation": [],
            "stability": {},
            "statistical_tests": {},
            "eda": {},
            "data_source": "synthetic_generator",
            "artifact_paths": {},
        }
        with patch.dict(os.environ, {"ML_TRAINING_ENABLED": "true", "ML_TRAINING_PROFILE": "render_demo", "ML_TRAINING_KEY": "demo-key"}, clear=False), patch.object(
            ml_model, "train_model_suite", return_value=suite_result
        ) as train_suite, patch(
            "backend.routes.ml.uuid.uuid4", side_effect=[UUID(int=1), UUID(int=2)]
        ):
            asyncio.run(train_model(TrainModelRequest(model_name="bootstrap_price_forecaster"), training_key="demo-key"))
            asyncio.run(train_model(TrainModelRequest(model_name="bootstrap_price_forecaster"), training_key="demo-key"))

        published_names = [call.kwargs["model_name"] for call in train_suite.call_args_list]
        self.assertEqual(published_names, [f"render_demo_{UUID(int=1).hex}", f"render_demo_{UUID(int=2).hex}"])
        self.assertNotIn("bootstrap_price_forecaster", published_names)

    def test_concurrent_training_is_rejected_before_tensorflow_work(self):
        _training_lock.acquire()
        try:
            with patch.dict(os.environ, {"ML_TRAINING_ENABLED": "true"}, clear=False), patch.object(
                ml_model, "train_model_suite"
            ) as train_suite:
                with self.assertRaises(HTTPException) as training_error:
                    asyncio.run(train_model(TrainModelRequest()))
        finally:
            _training_lock.release()

        self.assertEqual(training_error.exception.status_code, 409)
        train_suite.assert_not_called()


if __name__ == "__main__":
    unittest.main()
