# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Fixed
- Revert Azure deployment back to main branch until release deployment supported is added to Azure

## [0.1.1]

### Added

- Added CHANGELOG.md
- Added Website footer with Copyright  and link to Github pr reporting issues
- Added /healthz health check endpoint

### Fixed

- Fixed "Go back to analysis" button so it preserves the previously entered values

### Changed

- Azure Deployment to be on Release instead of push to main branch
- Renamed Github workflow from main_payvest.yml to release_payvest.yml
