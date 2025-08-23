import pytest
import tempfile
import os
import logging
import shutil
from unittest.mock import Mock, patch, MagicMock
from ghmcp.main import configure_logging, start_server, stop_server, parse_arguments, main


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_logging_valid_levels(self):
        """Test that configure_logging works with valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            # This should not raise any exception
            configure_logging(level)

            # Verify that the logging level was set correctly
            root_logger = logging.getLogger()
            expected_level = getattr(logging, level.upper())
            assert root_logger.level == expected_level

    def test_configure_logging_invalid_level(self):
        """Test that configure_logging raises error with invalid log level."""
        with pytest.raises(ValueError, match="Invalid log level: INVALID"):
            configure_logging("INVALID")

    def test_configure_logging_case_insensitive(self):
        """Test that configure_logging handles case-insensitive levels."""
        configure_logging("info")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

        configure_logging("Debug")
        assert root_logger.level == logging.DEBUG


class TestStartServer:
    """Tests for start_server function."""

    def test_start_server_with_valid_repos(self):
        """Test that start_server creates and returns a server successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                server = start_server([repo_path], name="test-server")

                assert server is not None
                assert server.name == "test-server"
                assert hasattr(server, 'indexer')
                assert len(server.indexer.repos) == 1

    def test_start_server_with_no_valid_repos(self):
        """Test that start_server raises error when no valid repos found."""
        with patch('ghmcp.server.get_repo') as mock_get_repo:
            mock_get_repo.return_value = None  # No valid repos

            with pytest.raises(ValueError, match="No valid Git repositories found"):
                start_server(["/nonexistent/path"])

    def test_start_server_with_default_parameters(self):
        """Test that start_server uses default parameters correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('ghmcp.server.get_repo') as mock_get_repo:
                mock_repo = Mock()
                mock_repo.working_dir = repo_path
                mock_get_repo.return_value = mock_repo

                server = start_server([repo_path])

                assert server.name == "ghmcp-server"  # Default name


class TestStopServer:
    """Tests for stop_server function."""

    def test_stop_server_with_valid_server(self):
        """Test that stop_server handles valid server gracefully."""
        mock_server = Mock()
        mock_server.name = "test-server"

        # This should not raise any exception
        stop_server(mock_server)

    def test_stop_server_with_none(self):
        """Test that stop_server handles None input gracefully."""
        # This should not raise any exception
        stop_server(None)


class TestParseArguments:
    """Tests for parse_arguments function."""

    def test_parse_arguments_default_values(self):
        """Test that parse_arguments returns correct default values."""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()

            assert args.name == 'ghmcp-server'
            assert args.host == 'localhost'
            assert args.port == 8000
            assert args.repos is None
            assert args.log_level == 'INFO'
            assert args.stdio is False

    def test_parse_arguments_with_custom_values(self):
        """Test that parse_arguments handles custom values correctly."""
        test_args = [
            'main.py',
            '--name', 'custom-server',
            '--host', '0.0.0.0',
            '--port', '9000',
            '--repos', '/repo1', '/repo2',
            '--log-level', 'DEBUG',
            '--stdio'
        ]

        with patch('sys.argv', test_args):
            args = parse_arguments()

            assert args.name == 'custom-server'
            assert args.host == '0.0.0.0'
            assert args.port == 9000
            assert args.repos == ['/repo1', '/repo2']
            assert args.log_level == 'DEBUG'
            assert args.stdio is True

    def test_parse_arguments_short_options(self):
        """Test that parse_arguments handles short options correctly."""
        test_args = [
            'main.py',
            '-n', 'short-server',
            '-H', '127.0.0.1',
            '-p', '8080',
            '-r', '/repo',
            '-l', 'WARNING',
            '-s'
        ]

        with patch('sys.argv', test_args):
            args = parse_arguments()

            assert args.name == 'short-server'
            assert args.host == '127.0.0.1'
            assert args.port == 8080
            assert args.repos == ['/repo']
            assert args.log_level == 'WARNING'
            assert args.stdio is True


class TestMain:
    """Tests for main function."""

    @pytest.mark.asyncio
    async def test_main_stdio_mode(self):
        """Test that main function handles stdio mode correctly."""
        test_args = [
            'main.py',
            '--stdio',
            '--repos', '/test/repo'
        ]

        with patch('sys.argv', test_args):
            with patch('ghmcp.main.run_stdio_server') as mock_run_stdio:
                with patch('ghmcp.main.configure_logging'):
                    mock_run_stdio.return_value = None

                    # Mock asyncio.run to avoid actually running the server
                    with patch('asyncio.run') as mock_asyncio_run:
                        main()
                        mock_asyncio_run.assert_called_once()

    def test_main_standard_mode(self):
        """Test that main function handles standard mode correctly."""
        test_args = [
            'main.py',
            '--repos', '/test/repo'
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "test_repo")
            os.makedirs(repo_path)

            with patch('sys.argv', test_args):
                with patch('ghmcp.server.get_repo') as mock_get_repo:
                    mock_repo = Mock()
                    mock_repo.working_dir = repo_path
                    mock_get_repo.return_value = mock_repo

                    with patch('ghmcp.main.configure_logging'):
                        with patch('asyncio.sleep') as mock_sleep:
                            # Mock sleep to raise KeyboardInterrupt to exit the loop
                            mock_sleep.side_effect = KeyboardInterrupt()

                            # This should handle the KeyboardInterrupt gracefully
                            main()

    def test_main_with_server_failure(self):
        """Test that main function handles server failure correctly."""
        test_args = [
            'main.py',
            '--repos', '/nonexistent'
        ]

        with patch('sys.argv', test_args):
            with patch('ghmcp.main.configure_logging'):
                with patch('ghmcp.main.start_server') as mock_start:
                    mock_start.side_effect = ValueError("Test error")

                    with patch('sys.exit') as mock_exit:
                        main()
                        mock_exit.assert_called_once_with(1)

def test_start_server_with_valid_repos():
    """
    Test that start_server correctly initializes with valid repositories.
    """
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    try:
        server = start_server([temp_dir], name="test-server")
        assert isinstance(server, MCPGitHubServer)
        libs = server.query_libraries()
        assert len(libs) == 1
        assert libs[0]['name'] == temp_dir.split('/')[-1]
        stop_server(server)
    finally:
        shutil.rmtree(temp_dir)

def test_start_server_with_invalid_repos():
    """
    Test that start_server raises RuntimeError when no valid repositories are found.
    """
    with pytest.raises(RuntimeError, match="Server startup failed"):
        start_server(['/non/existent/path'])

def test_stop_server_with_none():
    """
    Test that stop_server handles None input gracefully.
    """
    # Should not raise an exception
    stop_server(None)

def test_start_server_with_multiple_repos():
    """
    Test that start_server works with multiple valid repositories.
    """
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()
    Repo.init(temp_dir1)
    Repo.init(temp_dir2)
    try:
        server = start_server([temp_dir1, temp_dir2], name="multi-test-server")
        libs = server.query_libraries()
        assert len(libs) == 2
        stop_server(server)
    finally:
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)

@patch('ghmcp.main.signal.signal')
def test_start_server_sets_signal_handlers(mock_signal):
    """
    Test that start_server sets up signal handlers.
    """
    temp_dir = tempfile.mkdtemp()
    Repo.init(temp_dir)
    try:
        server = start_server([temp_dir])
        # Verify signal handlers were set
        assert mock_signal.call_count >= 2  # SIGINT and SIGTERM
        stop_server(server)
    finally:
        shutil.rmtree(temp_dir)
