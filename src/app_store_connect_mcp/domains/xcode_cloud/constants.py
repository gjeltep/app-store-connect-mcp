"""Constants and field definitions for Xcode Cloud domain."""

from typing import List, Dict

# -- FIELD DEFINITIONS --

# Products and Workflows
FIELDS_CI_PRODUCTS: List[str] = [
    "name",
    "createdDate",
    "productType",
]

FIELDS_CI_WORKFLOWS: List[str] = [
    "name",
    "description",
    "isEnabled",
    "isLockedForEditing",
    "containerFilePath",
    "lastModifiedDate",
]

# Build Runs
FIELDS_CI_BUILD_RUNS: List[str] = [
    "number",
    "createdDate",
    "startedDate",
    "finishedDate",
    "sourceCommit",
    "destinationCommit",
    "isPullRequestBuild",
    "issueCounts",
    "executionProgress",
    "completionStatus",
    "startReason",
    "cancelReason",
]

# Build Artifacts and Results
FIELDS_CI_ARTIFACTS: List[str] = [
    "fileType",
    "fileName",
    "fileSize",
    "downloadUrl",
]

FIELDS_CI_ISSUES: List[str] = [
    "issueType",
    "message",
    "fileSource",
    "category",
]

FIELDS_CI_TEST_RESULTS: List[str] = [
    "className",
    "name",
    "status",
    "message",
    "fileSource",
    "destinationTestResults",
]

# SCM Resources
FIELDS_SCM_PROVIDERS: List[str] = [
    "scmProviderType",
    "url",
]

FIELDS_SCM_REPOSITORIES: List[str] = [
    "repositoryName",
    "ownerName",
    "httpCloneUrl",
    "sshCloneUrl",
    "lastAccessedDate",
]

FIELDS_SCM_PULL_REQUESTS: List[str] = [
    "title",
    "number",
    "webUrl",
    "sourceRepositoryOwner",
    "sourceRepositoryName",
    "sourceBranchName",
    "destinationRepositoryOwner",
    "destinationRepositoryName",
    "destinationBranchName",
    "isClosed",
    "isCrossRepository",
]

FIELDS_SCM_GIT_REFERENCES: List[str] = [
    "name",
    "canonicalName",
    "isDeleted",
    "kind",
]

# -- FILTER MAPPINGS --

# Filter mappings for server-side filtering
PRODUCT_FILTER_MAPPING: Dict[str, str] = {
    "product_type": "productType",
}

WORKFLOW_FILTER_MAPPING: Dict[str, str] = {
    "is_enabled": "isEnabled",
}

BUILD_FILTER_MAPPING: Dict[str, str] = {
    "execution_progress": "executionProgress",
    "completion_status": "completionStatus",
    "is_pull_request_build": "isPullRequestBuild",
}
