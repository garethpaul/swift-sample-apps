private func expectKey(_ expected: String?, tag: Int, caseName: String) {
    let actual = BackgroundSelection.key(forButtonTag: tag)
    if actual != expected {
        fatalError("\(caseName): expected \(String(describing: expected)), got \(String(describing: actual))")
    }
}

expectKey("Background1", tag: 1, caseName: "first background")
expectKey("Background2", tag: 2, caseName: "second background")
expectKey(nil, tag: 0, caseName: "zero tag")
expectKey(nil, tag: -1, caseName: "negative tag")
expectKey(nil, tag: Int.min, caseName: "minimum integer tag")
expectKey(nil, tag: 3, caseName: "out-of-range tag")
