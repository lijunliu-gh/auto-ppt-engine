# Security Policy

## Supported Scope

This repository is an experimental open-source prototype. Security fixes may be accepted on a best-effort basis.

## Reporting A Vulnerability

Please do not file public GitHub issues for suspected vulnerabilities.

Instead, report them privately to the maintainers through your preferred private channel before public disclosure.

When reporting, include:

- affected file or feature
- reproduction steps
- potential impact
- suggested mitigation if known

## What Counts As Security-Relevant

Examples include:

- unsafe handling of uploaded or local files
- SSRF-like issues through URL source loading
- path traversal through request inputs
- accidental credential exposure
- unsafe HTTP service behavior

## Implemented Mitigations

As of v0.7.7, the following security controls are in place:

- **Path traversal prevention**: file paths are resolved and validated to stay within the project directory
- **SSRF blocking**: URL targets are validated to reject private/internal network addresses
- **File size limits**: source files are capped at 50 MB before processing
- **Subprocess timeout**: the Node.js renderer subprocess has a configurable timeout to prevent hangs
- **LLM credential isolation**: API keys are read from environment variables and never logged
- **Image security**: image files are limited to 10 MB, only common formats accepted (PNG, JPG, GIF, BMP, TIFF, SVG, WebP), local image paths must stay within the project directory, URL images undergo SSRF validation
- **Template file validation**: brand template uploads are limited to 100 MB, must be valid `.pptx` files, and paths are resolved to prevent traversal

## Prototype Warning

Do not deploy this repository as a public internet-facing service without additional hardening such as:

- authentication and authorization
- rate limiting
- stricter input validation
- sandboxing for file handling
- deployment-specific secrets management