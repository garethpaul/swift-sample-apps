//
//  ViewController.swift
//  background_switcher
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit
class ViewController: UIViewController {
    
    var imageView:UIImageView = UIImageView()
    var backgroundDict:Dictionary<String,UIColor> = Dictionary()
    private var backgroundButtons: [UIButton] = []
    private var selectedBackground: BackgroundSelection = .first
    private var reduceMotionObserver: NSObjectProtocol?
    var reduceMotionEnabledProvider: () -> Bool = { UIAccessibility.isReduceMotionEnabled }
    
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        backgroundDict = Dictionary(uniqueKeysWithValues: BackgroundSelection.allCases.map {
            ($0.key, backgroundColor(for: $0))
        })
        let contentView = UIView(frame: view.bounds)
        contentView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        self.view.addSubview(contentView)
        imageView = UIImageView(frame: contentView.bounds)
        imageView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        imageView.backgroundColor = backgroundDict["Background1"]
        
        contentView.addSubview(imageView)
        let buttonStack = UIStackView()
        buttonStack.axis = .vertical
        buttonStack.alignment = .fill
        buttonStack.spacing = 8
        buttonStack.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(buttonStack)
        
        for selection in BackgroundSelection.allCases {
            
            let button = UIButton(type: .system)
            button.setTitle(selection.title, for: .normal)
            button.accessibilityLabel = selection.title
            button.accessibilityTraits.insert(.button)
            button.setTitleColor(.white, for: .normal)
            button.titleLabel?.font = UIFont.preferredFont(forTextStyle: .body)
            button.titleLabel?.adjustsFontForContentSizeCategory = true
            button.titleLabel?.numberOfLines = 0
            button.titleLabel?.textAlignment = .center
            button.contentEdgeInsets = UIEdgeInsets(top: 12, left: 16, bottom: 12, right: 16)
            button.heightAnchor.constraint(greaterThanOrEqualToConstant: 44).isActive = true
            button.addTarget(self, action: #selector(buttonClicked(_:)), for: .touchUpInside)
            button.tag = selection.rawValue
            backgroundButtons.append(button)
            buttonStack.addArrangedSubview(button)
            
            
        }

        let safeArea = contentView.safeAreaLayoutGuide
        NSLayoutConstraint.activate([
            buttonStack.centerXAnchor.constraint(equalTo: safeArea.centerXAnchor),
            buttonStack.centerYAnchor.constraint(equalTo: safeArea.centerYAnchor),
            buttonStack.leadingAnchor.constraint(greaterThanOrEqualTo: safeArea.leadingAnchor, constant: 20),
            buttonStack.trailingAnchor.constraint(lessThanOrEqualTo: safeArea.trailingAnchor, constant: -20),
            buttonStack.topAnchor.constraint(greaterThanOrEqualTo: safeArea.topAnchor, constant: 20),
            buttonStack.bottomAnchor.constraint(lessThanOrEqualTo: safeArea.bottomAnchor, constant: -20)
        ])
        if let initialButton = backgroundButtons.first {
            updateSelectedButton(initialButton)
        }
        buttonStack.accessibilityElements = backgroundButtons
        reduceMotionObserver = NotificationCenter.default.addObserver(
            forName: UIAccessibility.reduceMotionStatusDidChangeNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.reduceMotionStatusDidChange()
        }
        
    }
    
    @objc private func buttonClicked(_ sender: UIButton) {
        guard let selection = BackgroundSelection.selection(forButtonTag: sender.tag) else {
            return
        }
        if let backgroundColor = self.backgroundDict[selection.key] {
            selectedBackground = selection
            updateSelectedButton(sender)
            if reduceMotionEnabledProvider() {
                imageView.layer.removeAllAnimations()
                imageView.backgroundColor = backgroundColor
            } else {
                UIView.transition(
                    with: imageView,
                    duration: 0.4,
                    options: [.transitionCrossDissolve, .beginFromCurrentState, .allowUserInteraction],
                    animations: {
                        self.imageView.backgroundColor = backgroundColor
                    },
                    completion: nil
                )
            }
        }
    }

    func backgroundColor(for selection: BackgroundSelection) -> UIColor {
        switch selection {
        case .first:
            return UIColor(red: 0.18, green: 0.33, blue: 0.58, alpha: 1.0)
        case .second:
            return UIColor(red: 0.64, green: 0.20, blue: 0.32, alpha: 1.0)
        }
    }

    private func reduceMotionStatusDidChange() {
        guard reduceMotionEnabledProvider() else {
            return
        }
        imageView.layer.removeAllAnimations()
        imageView.backgroundColor = backgroundColor(for: selectedBackground)
    }

    private func updateSelectedButton(_ selectedButton: UIButton) {
        for button in backgroundButtons {
            button.isSelected = button === selectedButton
            if button.isSelected {
                button.accessibilityTraits.insert(.selected)
            } else {
                button.accessibilityTraits.remove(.selected)
            }
        }
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }

    deinit {
        if let reduceMotionObserver = reduceMotionObserver {
            NotificationCenter.default.removeObserver(reduceMotionObserver)
        }
    }
    
    
}
