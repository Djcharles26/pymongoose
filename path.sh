#!/bin/bash

#find directory

SITEDIR=$(python -m site --user-site)

mkdir -p "$SITEDIR"

echo "$SITEDIR"

ls -la

#create new .pth file with our path

echo "./" > "$SITEDIR/pymongoose.pth"