import Foundation

let arguments = Array(CommandLine.arguments.dropFirst())
guard !arguments.isEmpty else {
    FileHandle.standardError.write(Data("missing integer tags\n".utf8))
    exit(64)
}

for argument in arguments {
    guard let tag = Int(argument) else {
        FileHandle.standardError.write(Data("invalid integer tag\n".utf8))
        exit(64)
    }

    if let selection = BackgroundSelection.selection(forButtonTag: tag) {
        print("selection:\(selection.rawValue):\(selection.key):\(selection.title)")
    } else {
        print("none")
    }
}
