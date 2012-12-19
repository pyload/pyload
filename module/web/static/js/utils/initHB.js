// Loads all helper and set own handlebars rules
define(['handlebars', 'helpers/formatSize'],
    function(Handlebars) {
        // TODO: create better lexer rules, these are just hacked
        Handlebars.Parser.lexer.rules = [/^(?:[^\x00]*?(?=(<%)))/, /^(?:[^\x00]+)/, /^(?:[^\x00]{2,}?(?=(<%|$)))/, /^(?:<%>)/, /^(?:<%#)/, /^(?:<%\/)/, /^(?:<%\^)/, /^(?:<%\s*else\b)/, /^(?:<%=)/, /^(?:<%&)/, /^(?:<%![\s\S]*?\}\})/, /^(?:<%)/, /^(?:=)/, /^(?:\.(?=[%> ]))/, /^(?:\.\.)/, /^(?:[\/.])/, /^(?:\s+)/, /^(?:=%>)/, /^(?:%>)/, /^(?:"(\\["]|[^"])*")/, /^(?:'(\\[']|[^'])*')/, /^(?:@[a-zA-Z]+)/, /^(?:true(?=[%>\s]))/, /^(?:false(?=[%>\s]))/, /^(?:[0-9]+(?=[%>\s]))/, /^(?:[a-zA-Z0-9_$-]+(?=[%>=}\s\/.]))/, /^(?:\[[^\]]*\])/, /^(?:.)/, /^(?:$)/];
        return Handlebars
    });