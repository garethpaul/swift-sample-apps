enum BackgroundSelection {
    private static let keys = ["Background1", "Background2"]

    static func key(forButtonTag tag: Int) -> String? {
        guard tag > 0 else {
            return nil
        }
        let index = tag - 1
        guard keys.indices.contains(index) else {
            return nil
        }
        return keys[index]
    }
}
