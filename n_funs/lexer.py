import ply.lex as lex


tokens = [
    'INTEGER',
    'FLOAT',
    'PLUS',
    'MINUS',
    'TIMES',
    'LPAREN',
    'RPAREN',

    'LBRACKET',
    'RBRACKET',
    'FRAC',
    'SQRT',
    'FACT',
    'HAT',
    'SYMBOL',
    'VEE',
    'EQUALS',  
    'COLON',   
]

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_SYMBOL  = r"[a-zA-Z]|\\pi"
t_FACT    = r'\!'
t_HAT     = r'\^'
t_EQUALS  = r'\='

# Latex symbols
t_LBRACKET = r"{"
t_RBRACKET = r"}"
t_COLON = r":"

# Matches decimal point numbers
def t_FLOAT(t):
    r'\d+[\,\.]\d+'
    t.value = t.value.replace(',', '.')
    t.value = float(t.value)
    return t

# Matches integers
def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Match the \frac symbol
def t_FRAC(t):
    r'\\frac'
    return t

# Match the \sqrt symbol
def t_SQRT(t):
    r'\\sqrt'
    return t

# Match the \vee symbol
def t_VEE(t):
    r'\\vee'
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()
