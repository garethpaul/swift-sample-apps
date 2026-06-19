import Foundation

private func emit(_ line: String) {
    let data = Data((line + "\n").utf8)
    FileHandle.standardOutput.write(data)
}

private func observation(for rawTag: String) -> String {
    guard let tag = Int(rawTag) else {
        return "\(rawTag)|malformed"
    }

    guard let selection = BackgroundSelection.selection(forButtonTag: tag) else {
        return "\(tag)|none"
    }

    return "\(tag)|selection|\(selection.buttonTag)|\(selection.key)|\(selection.title)"
}

for rawTag in CommandLine.arguments.dropFirst() {
    emit(observation(for: rawTag))
}
