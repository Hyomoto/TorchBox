Prism.languages.tinder = {
	'comment': {
		pattern: /\/\/.*/,
		greedy: true
	},
	// 1. Class/type names (e.g. # TypeName)
	'label': {
		// Matches: # label [else elsewhere]
		pattern: /^(\s*#\s*)\w+(\s+else\s+\w+)?/m,
		inside: {
			'punctuation': /^#/,                // The '#'
			'class-name': {
				pattern: /\w+/,
				alias: 'class-name'
			},
			'keyword': {
				pattern: /\belse\b/,
				alias: 'keyword'
			},
			'target': {
				// This will highlight the jump target after else
				pattern: /(?<=\belse\s+)\w+/,
				alias: 'function'
			}
		},
		alias: 'punctuation'
	},
	// 2. Control keywords at start of line
	'keyword': {
		pattern: /^(\s*)(catch|write|from|import|input|set|const|call|jump|return|stop|yield|inc|dec)\b/m,
		lookbehind: true
	},

	// 3. At-constants and bools
	'constant': [
		{
			pattern: /@\w+/,
			alias: 'variable'
		},
		{
			pattern: /\b(?:True|False)\b/,
			alias: 'boolean'
		}
	],

	// 4. Support functions/logical operators
	'function': {
		pattern: /\b(?:and|or|not|if|in|is|to|from|at|else|import)\b/,
		alias: 'keyword'
	},

	// 5. Invalid identifiers (backtick-prefixed)
	'invalid': {
		pattern: /`[a-zA-Z_][a-zA-Z0-9_]*\b/,
		alias: 'punctuation'
	},

	// 6. Macro-style [[var]] constants
	'macro': {
		pattern: /\[\[(?:var:)?\w+\]\]/,
		alias: 'constant'
	},

	// 7. Strings (double-quoted)
	'string': {
		pattern: /"[^"\r\n]*"/,
		greedy: true
	},

	// 8. Numbers
	'number': /\b\d+\b/,

	// 9. Parameters (ALL_CAPS)
	'parameter': {
		pattern: /\b[A-Z_][A-Z0-9_]*\b/,
		alias: 'variable'
	},

	// 10. Readwrite variables (lowercase)
	'variable': /\b[a-z_][a-z0-9_]*\b/
};
