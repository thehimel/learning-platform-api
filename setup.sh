#!/usr/bin/env bash
set -e

uv sync
pre-commit install
