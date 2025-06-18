#!/bin/bash

# EZpanso Intel Build Wrapper
# Quick script to build only Intel version

exec "$(dirname "$0")/build.sh" intel
