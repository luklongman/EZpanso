#!/bin/bash

# EZpanso Apple Silicon Build Wrapper
# Quick script to build only Apple Silicon version

exec "$(dirname "$0")/build.sh" arm64
