#!/bin/bash
set -e
S=/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/fonts-src
O=/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/fonts-out
U="U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+2010-2027,U+2030-203A,U+2190-2193,U+2212,U+20AC,U+2122"
run() { uv run -q --with fonttools --with brotli "$@"; }
# instance variable fonts to the ranges we use
run fonttools varLib.instancer "$S/ibmplexsans/IBMPlexSans[wdth,wght].ttf" wght=400:700 wdth=85:100 -o "$O/plexsans-var.ttf" -q
run fonttools varLib.instancer "$S/ibmplexsans/IBMPlexSans-Italic[wdth,wght].ttf" wght=400 wdth=100 -o "$O/plexsans-italic.ttf" -q
run fonttools varLib.instancer "$S/jetbrainsmono/JetBrainsMono[wght].ttf" wght=400:600 -o "$O/jbmono-var.ttf" -q
sub() { run pyftsubset "$1" --unicodes="$U" --layout-features='kern,liga,tnum,lnum,case,calt' --flavor=woff2 --output-file="$2"; }
sub "$O/plexsans-var.ttf" "$O/a1-sans.woff2"
sub "$O/plexsans-italic.ttf" "$O/a1-sans-italic.woff2"
sub "$S/ibmplexmono/IBMPlexMono-Regular.ttf" "$O/a1-mono-400.woff2"
sub "$S/ibmplexmono/IBMPlexMono-Medium.ttf" "$O/a1-mono-500.woff2"
sub "$S/barlow/Barlow-Regular.ttf" "$O/a2-sans-400.woff2"
sub "$S/barlow/Barlow-Medium.ttf" "$O/a2-sans-500.woff2"
sub "$S/barlow/Barlow-SemiBold.ttf" "$O/a2-sans-600.woff2"
sub "$S/barlowsemicondensed/BarlowSemiCondensed-SemiBold.ttf" "$O/a2-cond-600.woff2"
sub "$S/barlowsemicondensed/BarlowSemiCondensed-Bold.ttf" "$O/a2-cond-700.woff2"
sub "$O/jbmono-var.ttf" "$O/a2-mono.woff2"
ls -la "$O"/*.woff2
