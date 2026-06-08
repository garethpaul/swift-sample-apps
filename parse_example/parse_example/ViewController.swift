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
        var width:CGFloat = 320
        var height:CGFloat = 568
        var view:UIView = UIView(frame: CGRectMake(0,0,width,height))
        self.view.addSubview(view)
        imageView = UIImageView(frame: view.frame)
        imageView.backgroundColor = UIColor.lightGrayColor()
        view.addSubview(imageView)
        
        
        

        // Do any additional setup after loading the view, typically from a nib.
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }


}
