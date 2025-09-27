"""Analytics data downloader for fetching report segments from S3 and saving to TSV files."""

import gzip
import io
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

from app_store_connect_mcp.core.errors import (
    AppStoreConnectError,
    NetworkError,
)

# Constants
HTTP_TIMEOUT_SECONDS = 60.0
URL_TRUNCATE_LENGTH = 100
TEMP_FILE_PREFIX = "analytics_"
TEMP_FILE_SUFFIX = ".tsv"
FILE_ENCODING = "utf-8"
BYTES_PER_MEGABYTE = 1024 * 1024


class DownloadStatus(str, Enum):
    """Status values for download operations."""

    SUCCESS = "success"
    NO_DATA = "no_data"
    ERROR = "error"


class AnalyticsDataDownloader:
    """Downloads analytics report data from pre-signed S3 URLs and saves to TSV files."""

    def __init__(self):
        """Initialize the downloader with a simple HTTP client."""
        # No auth needed - S3 URLs are pre-signed
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)

    def _create_result_dict(
        self,
        status: DownloadStatus,
        file_path: Optional[str] = None,
        file_size_mb: float = 0,
        segment_count: int = 0,
        row_count: int = 0,
        message: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a standardized result dictionary for download operations.

        Args:
            status: Operation status from DownloadStatus enum
            file_path: Path to the downloaded file (if successful)
            file_size_mb: File size in megabytes
            segment_count: Number of segments processed
            row_count: Number of data rows (excluding header)
            message: Optional status message
            errors: Optional list of non-fatal errors

        Returns:
            Standardized result dictionary
        """
        result = {
            "status": status.value,
            "file_path": file_path,
            "file_size_mb": file_size_mb,
            "segment_count": segment_count,
            "row_count": row_count,
            "errors": errors,
        }

        if message:
            result["message"] = message

        return result

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def download_segment(self, url: str) -> bytes:
        """Download raw data from a pre-signed S3 segment URL.

        Args:
            url: The pre-signed S3 URL from the segment

        Returns:
            Raw bytes of the downloaded segment

        Important:
            Do NOT add Authorization headers - S3 URLs are pre-signed
        """
        try:
            # Download without any auth headers - URL is pre-signed
            response = await self._client.get(url)
            response.raise_for_status()
            return response.content
        except httpx.NetworkError as e:
            raise NetworkError(
                f"Failed to download analytics segment: {str(e)}",
                details={
                    "url": url[:URL_TRUNCATE_LENGTH] + "..."
                },  # Truncate URL for security
            )
        except httpx.HTTPStatusError as e:
            raise AppStoreConnectError(
                f"HTTP error downloading segment: {e.response.status_code}",
                details={"status": e.response.status_code},
            )
        except Exception as e:
            raise AppStoreConnectError(
                f"Unexpected error downloading segment: {str(e)}"
            )

    async def download_and_decompress_segment(self, url: str) -> str:
        """Download and decompress a gzipped segment.

        Analytics segments are gzipped TSV files.

        Args:
            url: The pre-signed S3 segment URL

        Returns:
            Decompressed text content
        """
        raw_data = await self.download_segment(url)

        try:
            # Decompress gzipped content
            with gzip.GzipFile(fileobj=io.BytesIO(raw_data)) as gz:
                return gz.read().decode(FILE_ENCODING)
        except gzip.BadGzipFile:
            # If not gzipped (unlikely), return as text
            try:
                return raw_data.decode(FILE_ENCODING)
            except UnicodeDecodeError:
                raise AppStoreConnectError(
                    "Segment data is not valid text or gzipped text"
                )

    async def download_segments_to_file(
        self, segments: List[Dict[str, Any]], output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Download all analytics report segments and save to a TSV file.

        This is the main method for downloading analytics data. It fetches all segments
        from pre-signed S3 URLs, decompresses them, and combines them into a single TSV file.

        Args:
            segments: List of segment objects from the API with 'url' attributes
            output_path: Optional path for output file. If None, uses temp directory

        Returns:
            Dict with file path and metadata:
            - status: "success", "no_data", or "error"
            - file_path: Path to the downloaded TSV file
            - file_size_mb: File size in megabytes
            - segment_count: Number of segments downloaded
            - row_count: Number of data rows (excluding header)
            - errors: List of any non-fatal errors encountered
        """
        if not segments:
            return self._create_result_dict(
                status=DownloadStatus.NO_DATA,
                message="No segments available for this report instance",
            )

        # Extract URLs from segment objects
        segment_urls = []
        for segment in segments:
            attrs = segment.get("attributes", {})
            if "url" in attrs:
                segment_urls.append(attrs["url"])

        if not segment_urls:
            return self._create_result_dict(
                status=DownloadStatus.ERROR,
                message="No download URLs found in segments",
            )

        # Determine output file path
        if output_path:
            file_path = Path(output_path)
        else:
            # Create temp file
            fd, temp_path = tempfile.mkstemp(
                suffix=TEMP_FILE_SUFFIX, prefix=TEMP_FILE_PREFIX
            )
            os.close(fd)  # Close the file descriptor
            file_path = Path(temp_path)

        try:
            # Download and combine all segments
            row_count = 0
            headers_written = False
            errors = []

            with open(file_path, "w", encoding=FILE_ENCODING) as outfile:
                for i, url in enumerate(segment_urls):
                    try:
                        # Download and decompress segment
                        content = await self.download_and_decompress_segment(url)

                        if content:
                            lines = content.strip().split("\n")

                            # Write headers from first segment only
                            if not headers_written and lines:
                                outfile.write(lines[0] + "\n")
                                headers_written = True
                                start_line = 1
                            else:
                                # Skip header line for subsequent segments
                                start_line = 1 if len(lines) > 1 else 0

                            # Write data lines
                            for line in lines[start_line:]:
                                if line.strip():  # Skip empty lines
                                    outfile.write(line + "\n")
                                    row_count += 1

                    except Exception as e:
                        errors.append(f"Segment {i + 1}: {str(e)}")

            # Check if we got any data
            if not headers_written:
                # No successful downloads
                if file_path.exists():
                    file_path.unlink()
                return self._create_result_dict(
                    status=DownloadStatus.ERROR,
                    message=f"Failed to download any segments: {'; '.join(errors)}",
                )

            # Get file size
            file_size_bytes = file_path.stat().st_size
            file_size_mb = round(file_size_bytes / BYTES_PER_MEGABYTE, 2)

            return self._create_result_dict(
                status=DownloadStatus.SUCCESS,
                file_path=str(file_path),
                file_size_mb=file_size_mb,
                segment_count=len(segment_urls),
                row_count=row_count,
                errors=errors or None,
            )

        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()

            raise AppStoreConnectError(
                f"Failed to save analytics data to file: {str(e)}"
            )
