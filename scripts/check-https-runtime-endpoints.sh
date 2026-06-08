#!/usr/bin/env bash
set -euo pipefail

grep -q "https://scontent-b.cdninstagram.com/hphotos-xfp1" background_switcher/background_switcher/ViewController.swift
grep -q "https://scontent-b.cdninstagram.com/hphotos-xpa1" background_switcher/background_switcher/ViewController.swift
grep -q 'NSURL(string: "https://caipiao.taobao.com")' swift-objects-example/swift-objects-example/DetailController.swift
grep -q 'NSURL(string: "https://garethpaul.com")' swift-objects-example/swift-objects-example/DetailViewController.swift

if grep -RIn --include='*.swift' 'http://' .; then
  echo "Swift runtime endpoints must not use cleartext HTTP" >&2
  exit 1
fi
