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
    
    func addTask(name: String , desc:String) -> Bool {
        if name.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet()).isEmpty {
            return false
        }
        tasks.append(task(name: name, desc: desc))
        return true
    }

    func taskAtIndex(index: Int) -> task? {
        if index < 0 || index >= tasks.count {
            return nil
        }
        return tasks[index]
    }

    func removeTaskAtIndex(index: Int) -> Bool {
        if index < 0 || index >= tasks.count {
            return false
        }
        tasks.removeAtIndex(index)
        return true
    }
}
