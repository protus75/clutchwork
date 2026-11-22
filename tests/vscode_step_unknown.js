'use strict';

const path = require('path');
const Module = require('module');
const root = path.resolve(__dirname, '..');
const disposable = { dispose() {} };
let steps;
const vscode = {
	Uri: { file: fsPath => ({ fsPath }) },
	workspace: {
		workspaceFolders: [{ uri: { fsPath: root } }],
		getConfiguration: () => ({ get: key => key === 'command' ? ['true'] : 0 }),
		onDidChangeConfiguration: () => disposable,
	},
	window: {
		createTreeView: (id, options) => {
			if (id === 'clutch.steps') steps = options.treeDataProvider;
			return { ...disposable, onDidChangeVisibility() {} };
		},
		registerWebviewViewProvider: () => disposable,
	},
	commands: { registerCommand: () => disposable },
	EventEmitter: class { constructor() { this.event = () => {}; } },
	TreeItem: class {},
	MarkdownString: class { appendText() { return this; } appendMarkdown() { return this; } },
	ThemeIcon: class { constructor(id) { this.id = id; } },
	ThemeColor: class {},
};
const load = Module._load;
Module._load = function (request, parent, isMain) {
	if (request === 'vscode') return vscode;
	if (request === 'child_process') return { execFile() {} };
	return load.call(this, request, parent, isMain);
};
require('../vscode-clutchwork/extension.js').activate({ extensionUri: {}, subscriptions: [] });
const item = steps.getTreeItem({ kind: process.argv[2], text: 'A check completed' });
console.log(JSON.stringify({ icon: item.iconPath.id, description: item.description }));
