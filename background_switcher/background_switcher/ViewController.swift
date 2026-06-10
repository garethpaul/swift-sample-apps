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
    
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        let width: CGFloat = 320
        let height: CGFloat = 568
        backgroundDict = [
            "Background1": UIColor(red: 0.18, green: 0.33, blue: 0.58, alpha: 1.0),
            "Background2": UIColor(red: 0.64, green: 0.20, blue: 0.32, alpha: 1.0)
        ]
        let buttonTitles = ["Background 1", "Background 2"]
        let contentView = UIView(frame: CGRect(x: 0, y: 0, width: width, height: height))
        self.view.addSubview(contentView)
        imageView = UIImageView(frame: contentView.frame)
        imageView.backgroundColor = backgroundDict["Background1"]
        
        contentView.addSubview(imageView)
        
        for i in buttonTitles.indices {
            
            let button = UIButton(type: .system)
            button.frame = CGRect(x: 0, y: 0, width: 200, height: 20)
            button.center = CGPoint(x: contentView.center.x, y: CGFloat(100 + i * 50))
            button.setTitle(buttonTitles[i], for: .normal)
            button.setTitleColor(.white, for: .normal)
            button.addTarget(self, action: #selector(buttonClicked(_:)), for: .touchUpInside)
            button.tag = i + 1
            contentView.addSubview(button)
            
            
        }
        
    }
    
    @objc private func buttonClicked(_ sender: UIButton) {
        let imageSelector = "Background\(sender.tag)"
        if let backgroundColor = self.backgroundDict[imageSelector] {
        
            UIView.animate(withDuration: 0.4, animations: {
                self.imageView.alpha = 0
            }, completion: { _ in
                self.imageView.backgroundColor = backgroundColor
                UIView.animate(withDuration: 0.4) {
                    self.imageView.alpha = 1
                }
            })
        }
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    
}
