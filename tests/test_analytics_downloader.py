"""Tests for analytics data downloader."""

import gzip
import io
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from app_store_connect_mcp.core.errors import AppStoreConnectError, NetworkError
from app_store_connect_mcp.domains.analytics.data_downloader import (
    AnalyticsDataDownloader,
)


class TestAnalyticsDataDownloader:
    """Test the analytics data downloader."""

    @pytest.fixture
    def downloader(self):
        """Create a downloader instance."""
        return AnalyticsDataDownloader()

    @pytest.fixture
    def sample_tsv_data(self):
        """Create sample TSV data."""
        return "Date\tApp Name\tDownloads\tTerritory\n2025-01-01\tMyApp\t100\tUSA\n2025-01-02\tMyApp\t150\tCAN"

    @pytest.fixture
    def gzipped_tsv_data(self, sample_tsv_data):
        """Create gzipped TSV data."""
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb") as gz:
            gz.write(sample_tsv_data.encode("utf-8"))
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_download_segment_success(self, downloader, gzipped_tsv_data):
        """Test successful segment download."""
        with patch.object(downloader._client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = gzipped_tsv_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = await downloader.download_segment("https://s3.example.com/segment.gz")

            assert result == gzipped_tsv_data
            mock_get.assert_called_once_with("https://s3.example.com/segment.gz")

    @pytest.mark.asyncio
    async def test_download_segment_network_error(self, downloader):
        """Test network error during download."""
        with patch.object(downloader._client, "get") as mock_get:
            mock_get.side_effect = httpx.NetworkError("Connection failed")

            with pytest.raises(NetworkError) as exc_info:
                await downloader.download_segment("https://s3.example.com/segment.gz")

            assert "Failed to download analytics segment" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_segment_http_error(self, downloader):
        """Test HTTP error during download."""
        with patch.object(downloader._client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Forbidden", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response

            with pytest.raises(AppStoreConnectError) as exc_info:
                await downloader.download_segment("https://s3.example.com/segment.gz")

            assert "HTTP error downloading segment: 403" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_and_decompress_gzipped(
        self, downloader, sample_tsv_data, gzipped_tsv_data
    ):
        """Test downloading and decompressing gzipped content."""
        with patch.object(downloader, "download_segment") as mock_download:
            mock_download.return_value = gzipped_tsv_data

            result = await downloader.download_and_decompress_segment(
                "https://s3.example.com/segment.gz"
            )

            assert result == sample_tsv_data

    @pytest.mark.asyncio
    async def test_download_and_decompress_not_gzipped(self, downloader, sample_tsv_data):
        """Test handling non-gzipped content."""
        with patch.object(downloader, "download_segment") as mock_download:
            mock_download.return_value = sample_tsv_data.encode("utf-8")

            result = await downloader.download_and_decompress_segment(
                "https://s3.example.com/segment.tsv"
            )

            assert result == sample_tsv_data

    @pytest.mark.asyncio
    async def test_download_and_decompress_invalid_data(self, downloader):
        """Test handling invalid binary data that's not text."""
        with patch.object(downloader, "download_segment") as mock_download:
            # Invalid binary data that's not gzipped and not valid UTF-8
            mock_download.return_value = b"\x80\x81\x82\x83"

            with pytest.raises(AppStoreConnectError) as exc_info:
                await downloader.download_and_decompress_segment(
                    "https://s3.example.com/segment.bin"
                )

            assert "Segment data is not valid text or gzipped text" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_segments_to_file_no_segments(self, downloader):
        """Test downloading with no segments."""
        result = await downloader.download_segments_to_file([])

        assert result["status"] == "no_data"
        assert result["message"] == "No segments available for this report instance"
        assert result["file_path"] is None
        assert result["row_count"] == 0

    @pytest.mark.asyncio
    async def test_download_segments_to_file_no_urls(self, downloader):
        """Test downloading with segments but no URLs."""
        segments = [
            {"attributes": {"sizeInBytes": 100}},  # No URL
            {"attributes": {"checksum": "abc123"}},  # No URL
        ]

        result = await downloader.download_segments_to_file(segments)

        assert result["status"] == "error"
        assert result["message"] == "No download URLs found in segments"
        assert result["file_path"] is None

    @pytest.mark.asyncio
    async def test_download_segments_to_file_success(self, downloader, sample_tsv_data):
        """Test successful file download."""
        segments = [
            {"attributes": {"url": "https://s3.example.com/segment1.gz"}},
            {"attributes": {"url": "https://s3.example.com/segment2.gz"}},
        ]

        # Second segment data (without header)
        segment2_data = "2025-01-03\tMyApp\t200\tGBR"

        with patch.object(downloader, "download_and_decompress_segment") as mock_download:
            # Return different data for each segment
            mock_download.side_effect = [
                sample_tsv_data,
                f"Date\tApp Name\tDownloads\tTerritory\n{segment2_data}",
            ]

            result = await downloader.download_segments_to_file(segments)

            assert result["status"] == "success"
            assert result["file_path"] is not None
            assert Path(result["file_path"]).exists()
            assert result["segment_count"] == 2
            assert result["row_count"] == 3  # 2 from first segment, 1 from second
            assert result["errors"] is None

            # Read the file and verify content
            with open(result["file_path"]) as f:
                lines = f.readlines()
                assert len(lines) == 4  # 1 header + 3 data rows
                assert lines[0].strip() == "Date\tApp Name\tDownloads\tTerritory"

            # Cleanup
            Path(result["file_path"]).unlink()

    @pytest.mark.asyncio
    async def test_download_segments_to_file_custom_path(self, downloader, sample_tsv_data):
        """Test downloading to a custom file path."""
        segments = [{"attributes": {"url": "https://s3.example.com/segment1.gz"}}]

        with tempfile.NamedTemporaryFile(suffix=".tsv", delete=False) as tf:
            output_path = tf.name

        try:
            with patch.object(downloader, "download_and_decompress_segment") as mock_download:
                mock_download.return_value = sample_tsv_data

                result = await downloader.download_segments_to_file(
                    segments, output_path=output_path
                )

                assert result["status"] == "success"
                assert result["file_path"] == output_path
                assert Path(output_path).exists()
        finally:
            # Cleanup
            if Path(output_path).exists():
                Path(output_path).unlink()

    @pytest.mark.asyncio
    async def test_download_segments_to_file_partial_failure(self, downloader, sample_tsv_data):
        """Test file download with some segments failing."""
        segments = [
            {"attributes": {"url": "https://s3.example.com/segment1.gz"}},
            {"attributes": {"url": "https://s3.example.com/segment2.gz"}},
            {"attributes": {"url": "https://s3.example.com/segment3.gz"}},
        ]

        with patch.object(downloader, "download_and_decompress_segment") as mock_download:
            # First succeeds, second fails, third succeeds
            mock_download.side_effect = [
                sample_tsv_data,
                NetworkError("Connection failed"),
                "Date\tApp Name\tDownloads\tTerritory\n2025-01-03\tMyApp\t200\tGBR",
            ]

            result = await downloader.download_segments_to_file(segments)

            # Should still create file with data from successful segments
            assert result["status"] == "success"
            assert result["file_path"] is not None
            assert result["row_count"] == 3  # 2 from first, 1 from third
            assert result["errors"] == ["Segment 2: Connection failed"]

            # Cleanup
            Path(result["file_path"]).unlink()

    @pytest.mark.asyncio
    async def test_download_segments_to_file_all_fail(self, downloader):
        """Test file download with all segments failing."""
        segments = [
            {"attributes": {"url": "https://s3.example.com/segment1.gz"}},
            {"attributes": {"url": "https://s3.example.com/segment2.gz"}},
        ]

        with patch.object(downloader, "download_and_decompress_segment") as mock_download:
            mock_download.side_effect = NetworkError("Connection failed")

            result = await downloader.download_segments_to_file(segments)

            assert result["status"] == "error"
            assert "Failed to download any segments" in result["message"]
            assert result["file_path"] is None
            assert result["row_count"] == 0

    @pytest.mark.asyncio
    async def test_cleanup(self, downloader):
        """Test cleanup closes the HTTP client."""
        with patch.object(downloader._client, "aclose") as mock_close:
            await downloader.aclose()
            mock_close.assert_called_once()
