from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from japanese_tutor.logic import app

runner = CliRunner()

@patch("uvicorn.run")
@patch("japanese_tutor.api.mount_static")
@patch("japanese_tutor.logic.resolve_provider")
@patch("japanese_tutor.logic.Database")
def test_run_command(mock_db, mock_resolve, mock_mount, mock_uvicorn, tmp_path):
    # Setup mock DB
    mock_db_instance = MagicMock()
    mock_db.return_value = mock_db_instance
    
    # Run with dry-run and no-llm to minimize side effects
    # Since it's a single command app, we don't need "run"
    result = runner.invoke(app, ["--dry-run", "--no-llm", "--db-path", str(tmp_path / "test.db")])
    
    assert result.exit_code == 0
    assert "Starting server at http://localhost:8421" in result.stdout
    mock_uvicorn.assert_called_once()
    mock_db.assert_called_once()
    mock_mount.assert_called_once()
