from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from japanese_tutor import api
from japanese_tutor.api import TutorDBError
from japanese_tutor.logic import JapaneseTutorError, ProviderSetupError, app
from japanese_tutor.ocr import OCRError


class TestTypedErrors:
    def test_tutor_error_hierarchy(self):
        err = JapaneseTutorError("base")
        assert isinstance(err, Exception)

    def test_provider_setup_error_is_tutor_error(self):
        err = ProviderSetupError("no provider")
        assert isinstance(err, JapaneseTutorError)
        assert "no provider" in str(err)

    def test_ocr_error_is_exception(self):
        err = OCRError("whisper failed")
        assert isinstance(err, Exception)
        assert "whisper failed" in str(err)

    def test_tutor_db_error_is_exception(self):
        err = TutorDBError("db error")
        assert isinstance(err, Exception)
        assert "db error" in str(err)


runner = CliRunner()


@patch("uvicorn.run")
@patch("japanese_tutor.api.mount_static")
@patch("japanese_tutor.cli.resolve_provider")
@patch("japanese_tutor.cli.Database")
def test_run_command(mock_db, mock_resolve, mock_mount, mock_uvicorn, tmp_path):
    # Setup mock DB
    mock_db_instance = MagicMock()
    mock_db.return_value = mock_db_instance

    # Run with dry-run and no-llm to minimize side effects
    # Since it's a single command app, we don't need "run"
    result = runner.invoke(
        app, ["--dry-run", "--no-llm", "--db-path", str(tmp_path / "test.db")]
    )

    assert result.exit_code == 0
    assert "Starting Japanese Tutor at http://localhost:8421" in result.stdout
    mock_uvicorn.assert_called_once()
    mock_db.assert_called_once()
    mock_mount.assert_called_once()
    assert mock_mount.call_args.args[0].name == "japanese_tutor"


@patch("uvicorn.run")
@patch("japanese_tutor.api.mount_static")
@patch("japanese_tutor.cli.LLMHelper")
@patch("japanese_tutor.cli.resolve_provider")
@patch("japanese_tutor.cli.Database")
def test_run_command_initializes_llm_helper_with_provider(
    mock_db,
    mock_resolve,
    mock_llm_helper,
    mock_mount,
    mock_uvicorn,
    tmp_path,
):
    mock_db.return_value = MagicMock()
    provider = MagicMock(name="provider")
    helper = MagicMock(name="llm_helper")
    mock_resolve.return_value = provider
    mock_llm_helper.return_value = helper

    prior_helper = api.llm_helper
    assigned_helper = None
    try:
        result = runner.invoke(
            app, ["--no-llm", "--db-path", str(tmp_path / "test.db")]
        )
        assigned_helper = api.llm_helper
    finally:
        api.llm_helper = prior_helper

    assert result.exit_code == 0
    mock_llm_helper.assert_called_once_with(provider)
    assert assigned_helper is helper
