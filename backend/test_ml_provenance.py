import asyncio
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi import HTTPException

from backend import ml_model
from backend.routes.ml import (
    TrainModelRequest,
    _training_data_source,
    delete_model,
    train_model,
)


class MlProvenanceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
