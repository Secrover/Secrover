# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8] - 2026-02-17
- chore: update deps
- core: force git pull by resetting changes before
- templates: add links on vulnerabilities badges
- templates: better margin for packages list
- templates: add links to repos with a git icon

## [0.7] - 2026-01-30
- core: update deps
- dependencies: fix scanning by not ignore ignored files

## [0.6] - 2026-01-15
- core: fix for possible not existing audit_results var
- core: update deps
- chore: update deps

## [0.5] - 2025-10-18
- core: update deps
- templates: show technologies used in the report
- templates: handle pluralization of 'vulnerabilities' word
- domains: add global summary

## [0.4] - 2025-10-15
- templates: improve main report
- domains: add country of domain (based on IP)
- security: escape html templates

## [0.3] - 2025-10-11
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

- initial version
