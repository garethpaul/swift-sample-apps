//
//  NoteEditorViewController.swift
//  basic-note-taker
//
//  Created by Gareth Paul Jones on 6/4/14.
//  Copyright (c) 2014 Gareth Paul Jones. All rights reserved.
//

import UIKit

protocol NoteEditorViewControllerDelegate {
    func noteEditorDidUpdateNote(editor: NoteEditorViewController)
}

class NoteEditorViewController: UIViewController, UITextViewDelegate {
    
    var note: String {
    didSet {
        if isViewLoaded() == false {
            return
        }
        
        textView.text = note
        
        if let ddelegate: NoteEditorViewControllerDelegate = delegate {
            ddelegate.noteEditorDidUpdateNote(self)
        }
    }
    }
    
    // This should be weak, but it doesn’t like it if I make it weak.
    var delegate: NoteEditorViewControllerDelegate?
    
    init(note: String = "") {
        self.note = note
        super.init(nibName: nil, bundle: nil)
    }
    
    var textView: UITextView {
    return view as UITextView
    }
    
    override func loadView() {
        self.view = UITextView()
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        textView.delegate = self
    }
    
    override func viewWillAppear(animated: Bool) {
        super.viewWillAppear(animated)
        textView.text = note
    }
    
    func textViewDidChange(textView: UITextView!) {
        note = textView.text
    }
    
}