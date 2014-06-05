//
//  TaskManager.swift
//  todo-list
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit

var taskMngr: TaskManager = TaskManager()

struct task{
    var name = "un-named"
    var desc = "un-Described"
}

class TaskManager: NSObject {
    var tasks = task[]()
    
    func addTask(name: String , desc:String){
        //tasks.append(task(name: name , desc: desc))
        tasks.append(task(name: name, desc: desc))
    }
}

