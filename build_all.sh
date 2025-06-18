#!/bin/bash

# EZpanso Universal Build Wrapper
# Quick script to build both Apple Silicon and Intel versions

exec "$(dirname "$0")/build.sh" all
