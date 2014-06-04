//
//  ViewController.swift
//  parse_example
//
//  Created by Gareth Paul Jones on 6/3/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit
import QuartzCore

class ViewController: UIViewController {
    
    var imageView:UIImageView = UIImageView()

    override func viewDidLoad() {
        super.viewDidLoad()
        var urlString = "https://trusteads.appspot.com//img?token=9af1a259-2b33-4ca7-b605-28a2cc112608"
        var imgURL: NSURL = NSURL(string: urlString)
        // Download an NSData representation of the image at the URL
        var imgData: NSData = NSData(contentsOfURL: imgURL)
        var width:CGFloat = 320
        var height:CGFloat = 568
        var view:UIView = UIView(frame: CGRectMake(0,0,width,height))
        self.view.addSubview(view)
        imageView = UIImageView(frame: view.frame)
        imageView.image = UIImage(data: imgData)
        view.addSubview(imageView)
        
        
        

        // Do any additional setup after loading the view, typically from a nib.
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }


}

