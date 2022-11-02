#!/bin/bash

DIR=$(dirname "$0")

rm -f "$2".dot "$2".pdf 
$DIR/sol-visualizer "$1" "$2" > "$2".dot
dot -Tpdf "$2".dot > "$2".pdf
rm -f "$2".dot
open "$2".pdf
