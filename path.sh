#!/bin/bash

#find directory

SITEDIR=$(python -m site --user-site)

mkdir -p "$SITEDIR"

#create new .pth file with our path

echo "./" > "$SITEDIR/pymongoose.pth"