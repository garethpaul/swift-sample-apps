//
//  ViewController.swift
//  swift-objects-example
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

//
//  RootViewController.swift
//  TSwift
//
//  Created by Hunk on 14-6-4.
//  Copyright (c) 2014年 Hunk. All rights reserved.
//

import UIKit

class ViewController : UIViewController, UITableViewDelegate, UITableViewDataSource
{
    var tableView   : UITableView?
    var items       : NSArray?
    
    override func viewDidLoad()
    {
        self.title = "Swift"
        self.items = ["UILabel", "UIButton", "UIImageView", "UISlider", "UIWebView", "UISegmentedControl", "UISwitch", "UITextField", "UIScrollView", "UISearchBar", "UIPageControl", "UIDatePicker", "UIPickerView", "UIProgressView", "UITextView", "UIToolbar", "UIActionSheet", "UIActivityIndicatorView"]
        
        self.tableView = UITableView(frame:self.view.frame, style:UITableViewStyle.Plain)
        self.tableView!.delegate = self
        self.tableView!.dataSource = self
        self.tableView!.registerClass(UITableViewCell.self, forCellReuseIdentifier: "Cell")
        self.view?.addSubview(self.tableView)
    }
    
    // UITableViewDataSource Methods
    func numberOfSectionsInTableView(tableView: UITableView!) -> Int
    {
        return 1
    }
    
    func tableView(tableView: UITableView!, numberOfRowsInSection section: Int) -> Int
    {
        if let currentItems = self.items {
            return currentItems.count
        }
        return 0
    }
    
    func tableView(tableView: UITableView!, cellForRowAtIndexPath indexPath: NSIndexPath!) -> UITableViewCell!
    {
        let cell = tableView.dequeueReusableCellWithIdentifier("Cell", forIndexPath: indexPath) as UITableViewCell!
        cell.accessoryType = UITableViewCellAccessoryType.DisclosureIndicator
        if let itemTitle = item(indexPath) {
            cell.textLabel.text = itemTitle
        } else {
            cell.textLabel.text = ""
        }
        
        return cell
    }
    
    // UITableViewDelegate Methods
    func tableView(tableView: UITableView!, didSelectRowAtIndexPath indexPath: NSIndexPath!)
    {
        self.tableView!.deselectRowAtIndexPath(indexPath, animated: true)
        
        if let selectedItemTitle = item(indexPath) {
            var detailViewController = DetailViewController()
            detailViewController.title = selectedItemTitle
            self.navigationController.pushViewController(detailViewController, animated:true)
        }
    }

    func item(indexPath: NSIndexPath) -> String? {
        if let currentItems = self.items {
            if indexPath.row < 0 || indexPath.row >= currentItems.count {
                return nil
            }
            return currentItems.objectAtIndex(indexPath.row) as? String
        }
        return nil
    }
    
    //
    override func didReceiveMemoryWarning()
    {}
}

