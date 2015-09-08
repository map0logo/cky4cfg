# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, division
import nltk
from nltk.grammar import is_nonterminal


def init_production_table(cnf_grammar):
    """
    Create a table a dictionary such that keys are productions right-hand-sides
    of the given grammar, and values the corresponding production.
    Useful to get the productions of a given rhs.
    :param cnf_grammar: A grammar in CNF format,
    :type cnf_grammar: nltk.grammar.CFG
    :return: The production table (dict of lists)
    """
    production_table = {}

    # Loops over all the productions in the grammar
    for production in cnf_grammar.productions():
        rhs = production.rhs()
        rhs_len = len(rhs)
        # If has two non-terminal rhs append to production_table
        if rhs_len == 2 and is_nonterminal(rhs[0]) and is_nonterminal(rhs[1]):
            key = (rhs[0].symbol(), rhs[1].symbol())
            if not production_table.has_key(key):
                production_table[key] = []
            production_table[key].append(production)
        elif rhs_len > 2:
            raise ValueError('{}: {}'.format(str(production), "non-CNF grammar"))
    return production_table


def cky_recognizer(tokens, cnf_grammar, production_table):
    """
    Generate a table where each element [i, j] contains a set of non-terminals
    that represent all the constituents that span positions i through j of the
    input
    :param tokens: Words of a sentence
    :type tokens: list of str
    :param cnf_grammar: A grammar in CNF format
    :type cnf_grammar: nltk.grammar.CFG
    :param production_table:
    :type dict of lists of nltk.Production
    :return: table, a list of lists of nltk.grammar.Nonterminal
    """
    # check if tokens are in the grammar
    try:
        cnf_grammar.check_coverage(tokens)
    except ValueError:
        return []

    n_tokens = len(tokens)
    table = [[None for j in range(n_tokens + 1)] for i in range(n_tokens)]
    # Fill the upper-triangular table a column at a time working from
    # left to right
    for j in range(1, n_tokens + 1):
        productions = cnf_grammar.productions(rhs=tokens[j-1])
        lhs_list = []
        for production in productions:
            lhs_list.append(production.lhs())
        table[j - 1][j] = lhs_list
        # Each column is then filled from bottom to top
        for i in range(j - 2, -1, -1):
            lhs_list = []
            # Range over the places the string can be split
            for k in range(i + 1, j):
                right = table[i][k] # Right along row i
                down = table[k][j] # Down along column j
                for r_lhs in right:
                    for d_lhs in down:
                        key = (str(r_lhs), str(d_lhs))
                        if production_table.has_key(key):
                            for production in production_table[key]:
                                lhs_list.append(production.lhs())
            table[i][j] = lhs_list
    return table


def is_in_CFG_language(table, cnf_grammar):
    """
    Verifies that at least one nonterminal in the upper right corner of the
    table corresponds to the grammar start
    :param table: result of cky_recognizer for an specific sentece.
    :type table: list of lists of nltk.grammar.Nonterminal
    :param cnf_grammar: A grammar in CNF format
    :type cnf_grammar: nltk.grammar.CFG
    :return: True if the table corresponds to a sentence in CFG language
    """
    found = []
    n_tokens = len(table[0]) - 1
    for lhs in table[0][n_tokens]: # Nonterminals in upper right corner
        if lhs == cnf_grammar.start(): # Is grammar start?
            found.append(lhs)
    return len(found) > 0 # At least one?


def cky_parser(tokens, cnf_grammar, production_table):
    """
    Generate a table where each element [i, j] contains a set of trees
    that represent all the constituents that span positions i through j of the
    input
    :param tokens: Words of a sentence
    :type tokens: list of str
    :param cnf_grammar: A grammar in CNF format
    :type cnf_grammar: nltk.grammar.CFG
    :param production_table:
    :type dict of lists of nltk.Production
    :return: table, a list of lists of nltk.Tree
    """
    # check if tokens are in the grammar
    try:
        cnf_grammar.check_coverage(tokens)
    except ValueError:
        return []

    n_tokens = len(tokens)
    table = [[0 for j in range(n_tokens + 1)] for i in range(n_tokens)]
    # Fill the upper-triangular table a column at a time working from
    # left to right
    for j in range(1, n_tokens + 1):
        productions = cnf_grammar.productions(rhs=tokens[j-1])
        trees = []
        for production in productions:
            trees.append(nltk.Tree(production.lhs(), [production.rhs()]))
        table[j-1][j] = trees
        # Each column is then filled from bottom to top
        for i in range(j - 2, -1, -1):
            trees = []
            # Range over the places the string can be split
            for k in range(i + 1, j):
                right = table[i][k] # Right along row i
                down = table[k][j] # Down along column j
                for r_tree in right:
                    for d_tree in down:
                        key = (str(r_tree.label()), str(d_tree.label()))
                        if production_table.has_key(key):
                            for production in production_table[key]:
                                trees.append(nltk.Tree(production.lhs(),
                                                       [r_tree, d_tree]))
            table[i][j] = trees
    trees_found = []
    for tree in table[0][n_tokens]:
        if str(tree.label()) == str(cnf_grammar.start()):
            trees_found.append(tree)

    return trees_found

if __name__ == "__main__":
    g = nltk.data.load("atis-grammar-cnf.cfg")
    pt = init_production_table(g)
    # load the raw sentences
    s = nltk.data.load("atis_test_sentences_a3.txt", "raw")
    # extract the test sentences
    t = nltk.parse.util.extract_test_sentences(s)
    for sentence in t:
        table = cky_recognizer(sentence[0], g, pt)
        print table
    tf = cky_parser(t[45][0], g, pt)
    for tree in tf:
        tree.draw()