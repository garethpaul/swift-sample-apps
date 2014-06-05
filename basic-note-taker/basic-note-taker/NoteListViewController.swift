//
//  NoteListViewController.swift
//  basic-note-taker
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit

class NoteListViewController: UITableViewController, NoteEditorViewControllerDelegate {
    
    let cellClass = UITableViewCell.self
    
    var cellIdentifier: String {
    return NSStringFromClass(cellClass)
    }
    
    var editor: NoteEditorViewController? {
    didSet {
        if let eeditor: NoteEditorViewController = editor {
            navigationController.pushViewController(eeditor, animated: true)
            eeditor.delegate = self
        }
    }
    }
    
    var notes: String[]
    var selectedNote: Int?
    
    init(notes: String[] = []) {
        self.notes = notes
        super.init(nibName: nil, bundle: nil)
        self.title = NSBundle.mainBundle().infoDictionary["CFBundleName"] as? String
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        tableView.registerClass(cellClass, forCellReuseIdentifier: NSStringFromClass(cellClass))
    }
    
    override func tableView(tableView: UITableView!, didSelectRowAtIndexPath indexPath: NSIndexPath!) {
        editor = NoteEditorViewController(note: note(indexPath))
        selectedNote = indexPath.row
    }
    
    override func tableView(tableView: UITableView!, numberOfRowsInSection section: Int) -> Int {
        return notes.count
    }
    
    override func tableView(tableView: UITableView!, cellForRowAtIndexPath indexPath: NSIndexPath!) -> UITableViewCell! {
        // I think I ought to use an optional here to explicity cope with potential nils
        let cell = tableView.dequeueReusableCellWithIdentifier(cellIdentifier, forIndexPath: indexPath) as UITableViewCell
        cell.textLabel.text = note(indexPath)
        return cell
    }
    
    func note(indexPath: NSIndexPath) -> String {
        return notes[indexPath.row]
    }
    
    func noteEditorDidUpdateNote(editor: NoteEditorViewController) {
        if let sselectedNote: Int = selectedNote {
            notes[sselectedNote] = editor.note
            tableView.reloadData()
        }
    }
}
