"""Constants and field definitions for Xcode Cloud domain."""


# -- FIELD DEFINITIONS --

# Products and Workflows
FIELDS_CI_PRODUCTS: list[str] = [
    "name",
    "createdDate",
    "productType",
]

FIELDS_CI_WORKFLOWS: list[str] = [
    "name",
    "description",
    "isEnabled",
    "isLockedForEditing",
    "containerFilePath",
    "lastModifiedDate",
]

# Build Runs
FIELDS_CI_BUILD_RUNS: list[str] = [
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
FIELDS_CI_ARTIFACTS: list[str] = [
    "fileType",
    "fileName",
    "fileSize",
    "downloadUrl",
]

FIELDS_CI_ISSUES: list[str] = [
    "issueType",
    "message",
    "fileSource",
    "category",
]

FIELDS_CI_TEST_RESULTS: list[str] = [
    "className",
    "name",
    "status",
    "message",
    "fileSource",
    "destinationTestResults",
]

# SCM Resources
FIELDS_SCM_PROVIDERS: list[str] = [
    "scmProviderType",
    "url",
]

FIELDS_SCM_REPOSITORIES: list[str] = [
    "repositoryName",
    "ownerName",
    "httpCloneUrl",
    "sshCloneUrl",
    "lastAccessedDate",
]

FIELDS_SCM_PULL_REQUESTS: list[str] = [
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

FIELDS_SCM_GIT_REFERENCES: list[str] = [
    "name",
    "canonicalName",
    "isDeleted",
    "kind",
]

# -- FILTER MAPPINGS --

# Filter mappings for server-side filtering
PRODUCT_FILTER_MAPPING: dict[str, str] = {
    "product_type": "productType",
}

WORKFLOW_FILTER_MAPPING: dict[str, str] = {
    "is_enabled": "isEnabled",
}

BUILD_FILTER_MAPPING: dict[str, str] = {
    "execution_progress": "executionProgress",
    "completion_status": "completionStatus",
    "is_pull_request_build": "isPullRequestBuild",
}
