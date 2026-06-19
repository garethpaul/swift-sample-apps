enum BackgroundSelection: Int, CaseIterable {
    case first = 1
    case second = 2

    var key: String {
        return "Background\(rawValue)"
    }

    var title: String {
        return "Background \(rawValue)"
    }

    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
        return BackgroundSelection(rawValue: tag)
    }

    static func key(forButtonTag tag: Int) -> String? {
        return selection(forButtonTag: tag)?.key
    }
}
