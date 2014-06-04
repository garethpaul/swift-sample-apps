//
//  ViewController.swift
//  facebook-login
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit


class ViewController: UIViewController, FBLoginViewDelegate {
    
    var profilePictureView: FBProfilePictureView?
    
    //var parse: Parse?
    var nameLabel: UILabel?
    var statusLabel: UILabel?
    //var p = Parse()
    
    
    
    override func viewDidLoad() {
        profilePictureView = FBProfilePictureView();
        profilePictureView!.frame = CGRectMake(86, 158, 50, 50)
        
        var font: UIFont = UIFont(name: "HelveticaNeue-Light", size: 15.0)
        
        nameLabel = UILabel();
        nameLabel!.frame = CGRectMake(144, 158, 156, 21)
        nameLabel!.font = font
        statusLabel = UILabel();
        statusLabel!.frame = CGRectMake(86, 129, 145, 21)
        statusLabel!.font = font
        
        self.view.addSubview(profilePictureView)
        self.view.addSubview(nameLabel)
        self.view.addSubview(statusLabel)
        
        
        var applicationId = String("8eQR5sFwbogIl6Ehs1AUvJKXc8hrnyFePaNYeSek")
        var clientKey = String("NCS4G5MSMNpbdiUWM67v2d7EmFJeKFl5TRbyZ8VD")
        
        
        //var login : Void = Parse.setApplicationId(applicationId, clientKey: clientKey)
        
        var permissions: AnyObject[] = ["public_profile", "email", "user_friends"];
        
        var loginView:FBLoginView = FBLoginView(readPermissions: permissions)
        loginView.delegate = self;
        
        loginView.frame = CGRectOffset(loginView.frame, (self.view.center.x - (loginView.frame.size.width / 2)), 5)
        loginView.center = self.view.center
        
        self.view.addSubview(loginView)
    }
    
    
    
    func loginViewFetchedUserInfo(loginView: FBLoginView?, user: AnyObject){
        var userObj: NSDictionary = user as NSDictionary
        profilePictureView!.profileID = userObj["id"] as String
        nameLabel!.text = userObj["name"] as String
    }
    
    func loginViewShowingLoggedInUser(loginView: FBLoginView?) {
        //statusLabel!.text = "You're logged in as"
    }
    
    func loginViewShowingLoggedOutUser(loginView: FBLoginView?) {
        profilePictureView!.profileID = nil
        nameLabel!.text = ""
        statusLabel!.text = "You're not logged in!"
    }
    
    func handleError(loginView: FBLoginView?, error: NSError) {
        var alertTitle: NSString = ""
        var alertMessage: NSString = ""
        
        // You need to override loginView:handleError in order to handle possible errors that can occur during login
        var error: NSError?
        if (FBErrorUtility.shouldNotifyUserForError(error)) {
            alertTitle = "Facebook error"
            alertMessage = FBErrorUtility.userMessageForError(error)
            
        } else if (FBErrorUtility.errorCategoryForError(error) == FBErrorCategory.AuthenticationReopenSession) {
            
            alertTitle = "Session Error"
            alertMessage = "Your current session is no longer valid. Please log in again."
            
            // If the user has cancelled a login, we will do nothing.
            // You can also choose to show the user a message if cancelling login will result in
            // the user not being able to complete a task they had initiated in your app
            // (like accessing FB-stored information or posting to Facebook)
        } else if (FBErrorUtility.errorCategoryForError(error) == FBErrorCategory.UserCancelled) {
            NSLog("user cancelled login")
            
            // For simplicity, this sample handles other errors with a generic message
            // You can checkout our error handling guide for more detailed information
            // https://developers.facebook.com/docs/ios/errors
        } else {
            alertTitle  = "Something went wrong"
            alertMessage = "Please try again later."
            NSLog("Unexpected error:%@", error!)
        }
        
        var alertView: UIAlertView = UIAlertView(title: alertTitle, message: alertMessage, delegate: nil, cancelButtonTitle: "OK")
        
        alertView.show()
        
    }
    
}
