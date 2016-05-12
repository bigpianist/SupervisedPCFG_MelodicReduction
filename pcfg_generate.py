from nltk import *
import copy

def generate(probGrammar):
	tree = generate_random_tree_recursive(probGrammar, 'S')
	return '(' + tree + ')'


def getTerminal(probGrammar, nonterminalString):
	curProductions = probGrammar.productions(Nonterminal(nonterminalString))
	dict = {}
	terminal = ''
	for pr in curProductions:
		if len(pr.rhs()) > 0:
			if not isinstance(pr.rhs()[0], Nonterminal):
				terminal = pr.rhs()
				break
	return terminal[0]


def expandAllLeaves(probGrammar, tree):
	leaves = tree.leaves()
	copyTree = copy.deepcopy(tree)
	for leafIndex, leaf in enumerate(leaves):
		print ('working with leaf: ' + str(leaf))


		leafPosition = tree.leaf_treeposition(leafIndex)
		parentPosition = leafPosition[:-1]
		print('leafPos is: ' + str(leafPosition) + ' and parentPos is: ' + str(parentPosition))
		parentTree = tree[parentPosition]

		parentOfLeaf = parentTree._label
		curProductions = probGrammar.productions(Nonterminal(parentOfLeaf))
		hasEmbellishments = False
		for prod in curProductions:
			print('checking production: ' + str(prod) + ' of len: ' + str(len(prod)))
			if len(prod) > 1:
				hasEmbellishments = True
				break
		if not hasEmbellishments:
			print('could not find a production rule with more than one non-terminal')
		dict = {}
		for pr in curProductions: dict[pr.rhs()] = pr.prob()

		probDist = DictionaryProbDist(dict)
		if hasEmbellishments:
			nextRule = probDist.generate()
			while len(nextRule) < 2:
				nextRule = probDist.generate()
		else:
			continue
		print(tree.leaf_treeposition(leafIndex))
		#replace the leaf tree with the new rule
		newTree = ''#' ('
		for r in nextRule:
			terminal = getTerminal(probGrammar, r._symbol)
			newTree += ' (' + r._symbol + ' ' + terminal + ')'
		#newTree += ')'
		#treeToInsert = Tree.fromstring(newTree)
		print('inserting: ' + str(newTree))
		copyTree[tree.leaf_treeposition(leafIndex)] = newTree
	return copyTree


def generate_random_tree_recursive(probGrammar, curNonterminalString):
	curProductions = probGrammar.productions(Nonterminal(curNonterminalString))
	print('checking nonterminal')
	print(curNonterminalString)
	dict = {}
	for pr in curProductions: dict[pr.rhs()] = pr.prob()


	probDist = DictionaryProbDist(dict)
	nextRule = probDist.generate()
	print('foundNextRule: ')
	print(nextRule)
	nonterminalsExist = False
	if len(nextRule) == 0:
		print('this should never happen, len(nextRule) is 0')
		nextRule = probDist.generate()
	for r in nextRule:
		if isinstance(r, Nonterminal):
			nonterminalsExist = True
	if not nonterminalsExist:
		curTree = curNonterminalString + ' ' + nextRule[0]
		print('found a terminal')
		return curTree
	else:
		curTree = curNonterminalString
		for r in nextRule:
			#print(type(nextRule))
			curTree += ' ('
			curTree += generate_random_tree_recursive(probGrammar, r._symbol)
			curTree += ')'
		return curTree
