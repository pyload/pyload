// Loads all helper and set own handlebars rules
define(['underscore', 'handlebars', 'helpers/formatSize'],
    function(_, Handlebars) {
        // Replace with own lexer rules compiled from handlebars.l
        Handlebars.Parser.lexer.rules = [/^(?:[^\x00]*?(?=(<%)))/, /^(?:[^\x00]+)/, /^(?:[^\x00]{2,}?(?=(\{\{|$)))/, /^(?:\{\{>)/, /^(?:<%=)/, /^(?:<%\/)/, /^(?:\{\{\^)/, /^(?:<%\s*else\b)/, /^(?:\{<%%)/, /^(?:\{\{&)/, /^(?:<%![\s\S]*?%>)/, /^(?:<%)/, /^(?:=)/, /^(?:\.(?=[%} ]))/, /^(?:\.\.)/, /^(?:[\/.])/, /^(?:\s+)/, /^(?:%%>)/, /^(?:%>)/, /^(?:"(\\["]|[^"])*")/, /^(?:'(\\[']|[^'])*')/, /^(?:@[a-zA-Z]+)/, /^(?:true(?=[%}\s]))/, /^(?:false(?=[%}\s]))/, /^(?:[0-9]+(?=[%}\s]))/, /^(?:[a-zA-Z0-9_$-]+(?=[=%}\s\/.]))/, /^(?:\[[^\]]*\])/, /^(?:.)/, /^(?:$)/];
        _.compile = Handlebars.compile;

        return Handlebars
    });