#!/usr/bin/env bash
set -o errexit

# Forzar a Render a usar pip en lugar de Poetry
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
