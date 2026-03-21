#!/usr/bin/env bash
npm ci
npm run build
pip install --only-binary=all -r requirements.txt
