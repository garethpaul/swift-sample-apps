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
        if let selectedNoteText = note(indexPath) {
            selectedNote = indexPath.row
            let editor = NoteEditorViewController(note: selectedNoteText)
            editor.delegate = self
            navigationController.pushViewController(editor, animated: true)
        }
    }
    
    override func tableView(tableView: UITableView!, numberOfRowsInSection section: Int) -> Int {
        return notes.count
    }
    
    override func tableView(tableView: UITableView!, cellForRowAtIndexPath indexPath: NSIndexPath!) -> UITableViewCell! {
        // I think I ought to use an optional here to explicity cope with potential nils
        let cell = tableView.dequeueReusableCellWithIdentifier(cellIdentifier, forIndexPath: indexPath) as UITableViewCell
        if let noteText = note(indexPath) {
            cell.textLabel.text = noteText
        } else {
            cell.textLabel.text = ""
        }
        return cell
    }
    
    func note(indexPath: NSIndexPath) -> String? {
        if indexPath.row < 0 || indexPath.row >= notes.count {
            return nil
        }
        return notes[indexPath.row]
    }
    
    func noteEditorDidUpdateNote(editor: NoteEditorViewController) {
        if let sselectedNote: Int = selectedNote {
            if sselectedNote >= 0 && sselectedNote < notes.count {
                notes[sselectedNote] = editor.note
                tableView.reloadData()
            }
        }
    }
}
