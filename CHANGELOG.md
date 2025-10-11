# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- core: pull git repos if already cloned
- core: permit to change repos folder path
- export: add suport for remote export of reports with rclone
- docker: add cron support with supercronic
- docker: fix opengrep not found by Python subprocess

## [0.2] - 2025-10-10
- core: only clone selected git branch
- core: update deps
- domains: add checks for new headers
- dependencies: show impacted versions
- dependencies: switch to osv-scanner to scan dependencies
- docker: switch docker image base to Alpine
- docker: adds linux/arm64 platform build

## [0.1] - 2025-08-28

- Initial version