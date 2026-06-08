//
//  ViewController.swift
//  background_switcher
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit
import QuartzCore


class ViewController: UIViewController {
    
    var imageView:UIImageView = UIImageView()
    var backgroundDict:Dictionary<String,UIColor> = Dictionary()
    
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        var width:CGFloat = 320
        var height:CGFloat = 568
        backgroundDict = [
            "Background1": UIColor(red: 0.18, green: 0.33, blue: 0.58, alpha: 1.0),
            "Background2": UIColor(red: 0.64, green: 0.20, blue: 0.32, alpha: 1.0)
        ]
        var buttonTitles = ["Background 1", "Background 2"]
        var view:UIView = UIView(frame: CGRectMake(0,0,width,height))
        self.view.addSubview(view)
        imageView = UIImageView(frame: view.frame)
        imageView.backgroundColor = backgroundDict["Background1"]
        
        view.addSubview(imageView)
        
        for i in 0..buttonTitles.count {
            
            var button:UIButton = UIButton.buttonWithType(UIButtonType.System) as UIButton
            button.frame = CGRectMake(0, 0, 200, 20)
            button.center = CGPointMake(view.center.x, CGFloat(100+i*50))
            button.setTitle(buttonTitles[i], forState: UIControlState.Normal)
            button.setTitleColor(UIColor.whiteColor(), forState: UIControlState.Normal)
            button.addTarget(self,action: "buttonClicked:", forControlEvents: UIControlEvents.TouchUpInside)
            button.tag = i + 1
            view.addSubview(button)
            println("\(i)")
            
            
        }
        
    }
    
    func buttonClicked(sender:UIButton) {
        var button:UIButton = sender
        var imageSelector:String = "Background\(button.tag)"
        if let backgroundColor = self.backgroundDict[imageSelector] {
        
            UIView.animateWithDuration(0.4, animations: {self.imageView.alpha=0},
                completion: {
                    _ in self.imageView.backgroundColor = backgroundColor
                    UIView.animateWithDuration(0.4, animations: {self.imageView.alpha=1})
                })
        }
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    
}
