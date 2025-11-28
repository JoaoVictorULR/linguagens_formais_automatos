#!/usr/bin/env python3
# meu_compilador.py
"""
Mini-projeto de Compiladores (versão alternativa)
Funcionalidades:
 - Tokenizador (análise léxica)
 - Simulador de AFD (validação de identificadores)
 - Parser recursivo-descendente para expressões aritméticas
 - Menu interativo para testar tudo
Autor: Versão adaptada para seu trabalho
Requisitos: Python 3.8+
Opcional: colorama (pip install colorama) para cores no terminal
"""

import re
import sys

# --------- cores (opcional) ----------
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except Exception:
    class _D:
        RESET = RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = ""
    Fore = Style = _D()

# ========= TOKENIZADOR =========
# especificação de tokens (nome, regex)
TOKEN_SPEC = [
    ("FLOAT",   r"\d+\.\d+"),
    ("INT",     r"\d+"),
    ("ID",      r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP",      r"==|!=|<=|>=|\+|\-|\*|/|="),
    ("LPAREN",  r"\("),
    ("RPAREN",  r"\)"),
    ("SEMI",    r";"),
    ("COMMA",   r","),
    ("SKIP",    r"[ \t\r\n]+"),
    ("UNKNOWN", r"."),
]

MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

KEYWORDS = {"if", "else", "while", "return", "int", "float", "for", "break", "continue"}


def tokenize(src: str):
    """Retorna lista de tokens (tipo, valor, posição)."""
    tokens = []
    for m in MASTER.finditer(src):
        kind = m.lastgroup
        val = m.group()
        pos = m.start()
        if kind == "SKIP":
            continue
        if kind == "ID" and val in KEYWORDS:
            kind = "KEYWORD"
        if kind == "UNKNOWN":
            tokens.append(("ERROR", val, pos))
        else:
            tokens.append((kind, val, pos))
    return tokens


# ========= AFD (simulador para identificadores) =========
def afd_identificador(s: str) -> bool:
    """
    Aceita strings que seguem [A-Za-z_][A-Za-z0-9_]*
    Implementado manualmente (sem regex) para fins didáticos.
    """
    if len(s) == 0:
        return False
    first = s[0]
    if not (first.isalpha() or first == "_"):
        return False
    for ch in s[1:]:
        if not (ch.isalnum() or ch == "_"):
            return False
    return True


# ========= PARSER: AST classes e parser recursivo-descendente =========
class AST:
    pass

class Number(AST):
    def __init__(self, value: str):
        self.value = value
    def __repr__(self):
        return f"Number({self.value})"

class Identifier(AST):
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"Identifier({self.name})"

class BinOp(AST):
    def __init__(self, op: str, left: AST, right: AST):
        self.op = op
        self.left = left
        self.right = right
    def __repr__(self):
        return f"BinOp({self.op}, {self.left}, {self.right})"


class ExprLexer:
    """Um lexer simples só para o parser de expressões (diferente do tokenizer principal)."""
    TOKEN_RE = re.compile(r"\s*(?:(\d+\.\d+|\d+)|([A-Za-z_][A-Za-z0-9_]*)|(.))")

    def __init__(self, text: str):
        self.tokens = []
        for m in ExprLexer.TOKEN_RE.finditer(text):
            num, ident, other = m.groups()
            if num:
                # manter distinção int/float opcionalmente
                if "." in num:
                    self.tokens.append(("NUMBER", num))
                else:
                    self.tokens.append(("NUMBER", num))
            elif ident:
                self.tokens.append(("ID", ident))
            elif other in "+-*/()":
                self.tokens.append((other, other))
            elif other == "":
                continue
            else:
                self.tokens.append(("ERROR", other))
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def next(self):
        t = self.peek()
        self.pos += 1
        return t

# Gramática:
# E -> T { (+|-) T }
# T -> F { (*|/) F }
# F -> NUMBER | ID | "(" E ")"

def parse_expression(text: str) -> AST:
    lex = ExprLexer(text)

    def F():
        tok = lex.peek()
        if tok[0] == "NUMBER":
            lex.next()
            return Number(tok[1])
        if tok[0] == "ID":
            lex.next()
            return Identifier(tok[1])
        if tok[0] == "(":
            lex.next()
            node = E()
            if lex.peek()[0] != ")":
                raise SyntaxError("Parêntese de fechamento esperado")
            lex.next()
            return node
        raise SyntaxError(f"Token inesperado em F: {tok}")

    def T():
        node = F()
        while lex.peek()[0] in ("*", "/"):
            op = lex.next()[0]
            right = F()
            node = BinOp(op, node, right)
        return node

    def E():
        node = T()
        while lex.peek()[0] in ("+", "-"):
            op = lex.next()[0]
            right = T()
            node = BinOp(op, node, right)
        return node

    ast = E()
    if lex.peek()[0] != "EOF":
        raise SyntaxError("Entrada extra após expressão")
    return ast


def pretty_print_ast(node: AST, indent: int = 0):
    pad = "  " * indent
    if isinstance(node, BinOp):
        print(pad + f"BINOP {node.op}")
        pretty_print_ast(node.left, indent + 1)
        pretty_print_ast(node.right, indent + 1)
    elif isinstance(node, Number):
        print(pad + f"NUMBER: {node.value}")
    elif isinstance(node, Identifier):
        print(pad + f"ID: {node.name}")
    else:
        print(pad + f"UNKNOWN_NODE: {node}")


# ========= Funções de interface (menu) =========
def run_tokenizer_interactive():
    print(Fore.CYAN + "=== Tokenizador Interativo ===" + Style.RESET_ALL)
    src = input("Cole um trecho de código: ")
    toks = tokenize(src)
    if not toks:
        print(Fore.YELLOW + "Nenhum token encontrado.")
        return
    for t in toks:
        typ, val, pos = t
        if typ == "ERROR":
            print(Fore.RED + f"{pos:04d}: ERRO -> {val}")
        else:
            print(Fore.GREEN + f"{pos:04d}: {typ:8s} -> {val}")


def run_afd_interactive():
    print(Fore.CYAN + "=== Simulador AFD (identificador) ===" + Style.RESET_ALL)
    s = input("Digite uma string para validar como identificador: ").strip()
    ok = afd_identificador(s)
    if ok:
        print(Fore.GREEN + "ACEITO: é um identificador válido.")
    else:
        print(Fore.RED + "REJEITADO: não é um identificador válido.")


def run_parser_interactive():
    print(Fore.CYAN + "=== Parser de Expressões (recursivo-descendente) ===" + Style.RESET_ALL)
    expr = input("Digite uma expressão (ex: a + 3*(b-2)): ")
    try:
        ast = parse_expression(expr)
        print(Fore.GREEN + "Árvore sintática:")
        pretty_print_ast(ast)
    except Exception as e:
        print(Fore.RED + "Erro de sintaxe:", e)


def show_help():
    print(Fore.CYAN + "=== Ajuda Rápida ===" + Style.RESET_ALL)
    print("Comandos básicos: digite o número da opção e Enter.")
    print("1 - Tokenizador\n2 - Simulador AFD\n3 - Parser\n4 - Sair")


def main():
    actions = {
        "1": run_tokenizer_interactive,
        "2": run_afd_interactive,
        "3": run_parser_interactive,
        "4": lambda: sys.exit(0),
    }
    while True:
        print(Fore.YELLOW + "\n--- MENU PRINCIPAL ---" + Style.RESET_ALL)
        print("1) Tokenizador")
        print("2) Simulador AFD")
        print("3) Parser")
        print("4) Sair")
        choice = input("> ").strip()
        action = actions.get(choice)
        if action:
            action()
        else:
            print(Fore.RED + "Opção inválida. Tente novamente.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
