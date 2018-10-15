/*
---
name: MooDialog.Error
description: Creates an Error dialog
authors: Arian Stolwijk
license:  MIT-style license
requires: MooDialog
provides: MooDialog.Error
...
*/


MooDialog.Error = new Class({

	Extends: MooDialog.Alert,

	options: {
		textPClass: 'MooDialogError'
	}

});
