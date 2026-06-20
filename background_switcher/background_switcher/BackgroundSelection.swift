enum BackgroundSelection {
    case first
    case second

    static let supportedCases: [BackgroundSelection] = [.first, .second]

    var buttonTag: Int {
        switch self {
        case .first:
            return 1
        case .second:
            return 2
        }
    }

    var key: String {
        switch self {
        case .first:
            return "Background1"
        case .second:
            return "Background2"
        }
    }

    var title: String {
        switch self {
        case .first:
            return "Background 1"
        case .second:
            return "Background 2"
        }
    }

    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
        switch tag {
        case 1:
            return .first
        case 2:
            return .second
        default:
            return nil
        }
    }

    static func key(forButtonTag tag: Int) -> String? {
        return selection(forButtonTag: tag)?.key
    }
}
