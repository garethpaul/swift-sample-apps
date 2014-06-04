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
    var backgroundDict:Dictionary<String,String> = Dictionary()
    
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        var width:CGFloat = 320
        var height:CGFloat = 568
        backgroundDict = ["Background1":"http://scontent-b.cdninstagram.com/hphotos-xfp1/t51.2885-15/10362298_1412014695748047_1496400892_n.jpg","Background2":"http://scontent-b.cdninstagram.com/hphotos-xpa1/t51.2885-15/10296956_280293632148907_639323969_n.jpg"]
        var buttonTitles = ["Background 1", "Background 2"]
        var view:UIView = UIView(frame: CGRectMake(0,0,width,height))
        self.view.addSubview(view)
        var backgroundImage:UIImage = UIImage(named:backgroundDict["Background1"])
        var urlString = "https://trusteads.appspot.com//img?token=9af1a259-2b33-4ca7-b605-28a2cc112608"
        var imgURL: NSURL = NSURL(string: urlString)
        var imgData: NSData = NSData(contentsOfURL: imgURL)
        imageView = UIImageView(frame: view.frame)
        imageView.image = UIImage(data: imgData)
        
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
        var imgURL: NSURL = NSURL(string: self.backgroundDict[imageSelector])
        var imgData: NSData = NSData(contentsOfURL: imgURL)
        
        UIView.animateWithDuration(0.4, animations: {self.imageView.alpha=0},
            completion: {
                
                _ in self.imageView.image = UIImage(data: imgData)
                UIView.animateWithDuration(0.4, animations: {self.imageView.alpha=1})
            })
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    
}


