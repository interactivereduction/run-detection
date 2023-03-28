"""
Ingest and metadata tests
"""
import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture

from rundetection.ingest import (
    ingest,
    DetectedRun,
    get_sibling_nexus_files,
    get_sibling_runs,
    skip_extract,
    get_extraction_function,
    get_run_title,
)

# Allows test to be run via pycharm play button or from project root
TEST_DATA_PATH = Path("test_data") if Path("test_data").exists() else Path("test", "test_data")


@pytest.mark.parametrize(
    "pair",
    [
        (
            "e2e_data/1510111/ENGINX00241391.nxs",
            DetectedRun(
                run_number=241391,
                instrument="ENGINX",
                experiment_title="CeO2 4 x 4 x 15",
                experiment_number="1510111",
                filepath=Path(TEST_DATA_PATH, "e2e_data/1510111/ENGINX00241391.nxs"),
            ),
        ),
        (
            "e2e_data/1600007/IMAT00004217.nxs",
            DetectedRun(
                run_number=4217,
                instrument="IMAT",
                experiment_title="Check DAE and end of run working after move",
                experiment_number="1600007",
                filepath=Path(TEST_DATA_PATH, "e2e_data/1600007/IMAT00004217.nxs"),
            ),
        ),
        (
            "e2e_data/1920302/ALF82301.nxs",
            DetectedRun(
                run_number=82301,
                instrument="ALF",
                experiment_title="YbCl3 rot=0",
                experiment_number="1920302",
                filepath=Path(TEST_DATA_PATH, "e2e_data/1920302/ALF82301.nxs"),
            ),
        ),
    ],
    ids=["ENGINX00241391.nxs", "IMAT00004217.nxs", "ALF82301.nxs"],
)
def test_ingest(pair) -> None:
    """
    Test the metadata is built from test nexus files
    :return: None
    """
    nexus_file = TEST_DATA_PATH / pair[0]
    assert (ingest(nexus_file)) == pair[1]


def test_ingest_raises_exception_non_nexus_file() -> None:
    """
    Test value error is raised when a non nexus file is given to be ingested
    :return: None
    """
    with pytest.raises(ValueError):
        ingest(Path("foo.log"))


def test_to_json_string() -> None:
    """
    Test valid json string can be built from metadata
    :return: None
    """
    nexus_metadata = DetectedRun(
        run_number=12345,
        instrument="LARMOR",
        experiment_number="54321",
        experiment_title="my experiment",
        filepath=Path("e2e_data/1920302/ALF82301.nxs"),
    )
    assert (
        nexus_metadata.to_json_string() == '{"run_number": 12345, "instrument": "LARMOR", "experiment_title": '
        '"my experiment", "experiment_number": "54321", "filepath": '
        '"e2e_data/1920302/ALF82301.nxs", '
        '"additional_values": {}}'
    )


def test_split_runs():
    detected_run = DetectedRun(
        run_number=1,
        instrument="MARI",
        experiment_title="Run Title A",
        experiment_number="123",
        filepath=Path("MARI0001.nxs"),
        will_reduce=True,
        additional_values={},
    )

    additional_run = DetectedRun(
        run_number=2,
        instrument="MARI",
        experiment_title="Run Title B",
        experiment_number="123",
        filepath=Path("MARI0002.nxs"),
        will_reduce=True,
        additional_values={},
    )

    detected_run.additional_runs.append(additional_run)

    split_detected_runs = detected_run.split_runs()

    # Check if the returned list contains both the detected_run and additional_run
    assert len(split_detected_runs) == 2
    assert detected_run in split_detected_runs
    assert additional_run in split_detected_runs


def test_logging_and_exception_when_nexus_file_does_not_exit(caplog: LogCaptureFixture):
    """
    Test correct logging and exception reraised when nexus file is missing
    :param caplog: LogCaptureFixture
    :return: None
    """
    with pytest.raises(FileNotFoundError):
        ingest(Path("e2e_data/foo/bar.nxs"))

    assert "Nexus file could not be found: e2e_data/foo/bar.nxs" in caplog.text


@patch("rundetection.ingest.ingest")
def test_get_run_title(mock_ingest):
    """
    Test file ingested and title returned
    :param mock_ingest: Mock ingest function
    :return: None
    """
    mock_run = Mock()
    mock_run.experiment_title = "foo"
    mock_ingest.return_value = mock_run
    assert get_run_title(Path("/dir/file.nxs")) == "foo"
    mock_ingest.assert_called_once_with(Path("/dir/file.nxs"))


def test_get_sibling_nexus_files():
    """
    Test that nexus files from within the same directory are returned
    :return: None
    """
    with TemporaryDirectory() as temp_dir:
        Path(temp_dir, "1.nxs").touch()
        Path(temp_dir, "2.nxs").touch()
        Path(temp_dir, "1.log").touch()
        sibling_files = get_sibling_nexus_files(Path(temp_dir, "1.nxs"))
        assert sibling_files == [Path(temp_dir, "2.nxs")]


@patch("rundetection.ingest.ingest")
def test_get_sibling_runs(mock_ingest: Mock):
    """
    Tests that a list of detected runs are returned when ingesting sibling nexus files
    :param mock_ingest: Mock ingest
    :return: None
    """
    run = DetectedRun(1, "inst", "title", "num", Path("path"))
    mock_ingest.return_value = run
    with TemporaryDirectory() as temp_dir:
        Path(temp_dir, "1.nxs").touch()
        Path(temp_dir, "2.nxs").touch()
        assert get_sibling_runs(Path(temp_dir, "1.nxs")) == [run]


if __name__ == "__main__":
    unittest.main()
