
import validate_tree
import itertools
import operator
import collections
from nltk import *
from music21 import *
from xml.etree.ElementTree import *
from os.path import basename
from nltk.parse import ViterbiParser

from nltk.tree import Tree, ProbabilisticTree


harmonyGrammarStringExplicitChordTonesFilename = 'grammarFiles/harmonyGrammarStringExplicitChordTones.txt'
musicGrammarFilename = 'grammarFiles/musicGrammarHandmade.txt'



majorScaleMajorChords = ['I', 'IV', 'V']
majorScaleMinorChords = ['II', 'III', 'VI']

minorScaleMajorChords = ['III', 'VI', 'VII']
minorScaleMinorChords = ['I', 'IV', 'V']

majorScaleChordDegreeToPitchClass = {'I':0, 'II':2, 'III':4, 'IV':5, 'V':7, 'VI':9, 'VII':11}
minorScaleChordDegreeToPitchClass = {'I':0, 'II':2, 'III':3, 'IV':5, 'V':7, 'VI':8, 'VII':10}

majorDegreeToPitchClass = {1:0, 2:2, 3:4, 4:5, 5:7, 6:9, 7:11}
minorDegreeToPitchClass = {1:0, 2:2, 3:3, 4:5, 5:7, 6:8, 7:10}

testString = ['-5', '2', '2', '-3', '1', '2', '1', '-1']
testString1 = ['2', '2', '-3', '1', '2', '1', '-1']
testString2 = ['0', '2', '0', '-7', '10', '-1', '-4','0', '-3']

class ContextFreeGrammar(CFG):
	def __str__(self):
		str = 'Ryan\'s Grammar with %d productions' % len(self._productions)
		str += ' (start state = %r)' % self._start
		for production in self._productions:
			str += '\n    %s' % production
		return str

#class NonterminalConstraint()

def pairwise(iterable):
	"s -> (s0,s1), (s1,s2), (s2, s3), ..."
	a, b = itertools.tee(iterable)
	next(b, None)
	return zip(a, b)

def getPitchListFromFile(filepath, type="MusicXml"):
	pitchList = []
	if type == "MusicXml":
		loadedMusicFile = converter.parse(filepath)
		flatFile = loadedMusicFile.flat
		for n in flatFile.notes:
			if n.tie != None and n.tie.type == 'stop':
				continue
			pitchList.append(n)
	return pitchList

def getIntervalStringsFromPitchList(pitchList, verbose=False):
	intervalList = []
	for p1, p2 in pairwise(pitchList):
		curInterval = p2.ps - p1.ps
		curIntervalString = "{:.0f}".format(curInterval)
		intervalList.append(curIntervalString)
		if verbose:
			print(curInterval)
	return intervalList

def getIntervalStringsFromPitchClassList(pitchList, verbose=False, chordType=None):
	chordTones = []
	if chordType == "MINOR":
		chordTones = [0, 3, 7]
	elif chordType == "MAJOR":
		chordTones = [0, 4, 7]

	intervalList = []
	for p1, p2 in pairwise(pitchList):
		curInterval = p2 - p1
		curIntervalString = "{:.0f}".format(curInterval)

		if (p1 % 12) in chordTones:
			curIntervalString = 'c' + curIntervalString
		if (p2 % 12) in chordTones:
			curIntervalString = curIntervalString + 'c'
		intervalList.append(curIntervalString)
	if verbose:
		print(curInterval)
	return intervalList

def isFirstNoteInScore(noteRefToTest, ref2, ref3):
	ref1List = noteRefToTest.split("-")
	ref2List = ref2.split("-")
	ref3List = ref3.split("-")
	ref1Val = float(ref1List[1]) * 10 + float(ref1List[2]) * .1
	ref2Val = float(ref2List[1]) * 10 + float(ref2List[2]) * .1
	ref3Val = float(ref3List[1]) * 10 + float(ref3List[2]) * .1
	retVal = False
	if ref1Val < ref2Val and ref1Val < ref3Val:
		retVal = True
	return retVal


def isLastNoteInScore(noteRefToTest, ref2, ref3):
	ref1List = noteRefToTest.split("-")
	ref2List = ref2.split("-")
	ref3List = ref3.split("-")
	ref1Val = float(ref1List[1]) * 10 + float(ref1List[2]) * .1
	ref2Val = float(ref2List[1]) * 10 + float(ref2List[2]) * .1
	ref3Val = float(ref3List[1]) * 10 + float(ref3List[2]) * .1
	retVal = False
	if ref1Val > ref2Val and ref1Val > ref3Val:
		retVal = True
	return retVal

def isBefore(noteRefToTest, ref2):
	ref1List = noteRefToTest.split("-")
	ref2List = ref2.split("-")
	ref1Val = float(ref1List[1]) * 10 + float(ref1List[2]) * .1
	ref2Val = float(ref2List[1]) * 10 + float(ref2List[2]) * .1
	retVal = False
	if ref1Val < ref2Val:
		retVal = True
	return retVal

def pitchRefToNum(a):
	ref1List = a.split("-")
	ref1Val = float(ref1List[1]) * 10 + float(ref1List[2]) * .1
	return ref1Val

#these pitch references could be out of order in the score.
#it is this function's job to figure out the order, the intervals, and apply the grammar
def applyGrammarToThreePitchReferences(ref1, ref2, ref3, musicXml, grammar, productionList, verbose=False):
	if ref1 == ref2 or ref1 == ref3 or ref2 == ref3:
		return ""
	ref3isValid = True
	if ref3 == None:
		ref3isValid = False

	ref1List = ref1.split("-")
	ref1Pitch = lookUpPitchReference(ref1, musicXml, verbose)
	ref2List = ref2.split("-")
	ref2Pitch = lookUpPitchReference(ref2, musicXml, verbose)
	if ref3isValid:
		ref3List = ref3.split("-")
		ref3Pitch = lookUpPitchReference(ref3, musicXml, verbose)
	ref1Val = float(ref1List[1]) * 10.0 + float(ref1List[2]) * .1
	ref2Val = float(ref2List[1]) * 10.0 + float(ref2List[2]) * .1
	if ref3isValid:
		ref3Val = float(ref3List[1]) * 10.0 + float(ref3List[2]) * .1
		pitchListInOrder = {ref1Val: ref1Pitch, ref2Val: ref2Pitch, ref3Val: ref3Pitch}
	else:
		pitchListInOrder = {ref1Val: ref1Pitch, ref2Val: ref2Pitch}
	sortedPitches = sorted(pitchListInOrder.items(), key=operator.itemgetter(0))
	if verbose:
		print(sortedPitches)
	intervalList = []
	for p1, p2 in pairwise(sortedPitches):
		interval = p2[1] - p1[1]
		#format the integer interval into a string without any decimal values
		interval = "{:.0f}".format(interval)
		intervalList.append(interval)
	if verbose:
		print ("here is the interval list:")
		print(intervalList)
	traceVal = 0
	if verbose:
		traceVal = 1
	parser = ChartParser(grammar, trace=traceVal)
	grammarTree =""
	grammarNCount = 100000
	for tree in parser.parse(intervalList):
		numberOfNewRules = str(tree).count("N")
		if numberOfNewRules < grammarNCount:
			grammarTree = str(tree)
			grammarNCount = numberOfNewRules
	if verbose:
		print(grammarTree[5:-2])
	productionList.append(grammarTree[3:-1])
	return grammarTree[5:-2]

def find_nth(haystack, needle, n):
	start = haystack.find(needle)
	while start >= 0 and n > 1:
		start = haystack.find(needle, start+len(needle))
		n -= 1
	return start

def findNestedParens(stringParens):
	balance = 0
	gotIntoNest = False
	breakPoints = []
	nestedParens = []
	for index, char in enumerate(stringParens):
		if char == '(':
			balance = balance + 1
			gotIntoNest = True
		if char == ')':
			balance = balance - 1
		if balance == 0 and gotIntoNest:
			breakPoints.append(index)
			gotIntoNest = False
	last = 0
	for splitPoint in breakPoints:
		nestedParens.append(stringParens[last:splitPoint + 1])
		last = splitPoint + 1
	return nestedParens

def insertTree(position, parentTree, treeToInsert, verbose = False):
	if verbose:
		print("inserting '" + treeToInsert + "' into '" + parentTree +"' with position: " + str(position))
	if treeToInsert == '':
		return parentTree
	#find the grammar rules that have no child rules
	#i.e. the inner-most parenthesis pairs
	#parens = re.findall('(\([^()]*\))', parentTree)
	nestedParens = findNestedParens (treeToInsert)
	parentTreeParens = parens = re.findall('(\([^()]*\))', parentTree)
	if len(nestedParens) > 1 and len(parentTreeParens) > 1 and parentTree.count('N') < 2:
		treeToInsert = '(N ' + treeToInsert + ')'



	nestedParentParens = findNestedParens (parentTree)

	if len(nestedParentParens) == 1:
		#do it the old way
		parens = re.findall('(\([^()]*\))', parentTree)
		paren = parens[position]

		#we have to check if there are any duplicate positions, so that
		#we can find the accurate place within the parent string
		numDuplicatesBeforeParen = 0
		if position == -1:
			position = len(parens) - 1
		for idx, otherParen in enumerate(parens):
			if otherParen == paren and idx < position:
				numDuplicatesBeforeParen += 1
		indexOfParen = find_nth(parentTree, paren, numDuplicatesBeforeParen + 1)


		endOfParen = indexOfParen + len(paren)
		newParentTree = parentTree[0:indexOfParen - 1] + treeToInsert + parentTree[endOfParen:]

	else:
		positionTree = ""
		try:
			positionTree = nestedParentParens[position]
		except:
			print(nestedParentParens)
			print(parentTree)
		parens = re.findall('(\([^()]*\))', positionTree)
		if verbose:
			print("matched the paren: " + str(parens))
		#if len(parens) > 1:
		#	print("too many parens!! (" + str(len(parens)) + ")")

		paren = parens[0]


		firstTokenParen = re.search('(\w+)', paren)
		firstTokenTree = re.search('(\w+)', treeToInsert)
		if verbose:
			print('firstTokenParen: ' + firstTokenParen.group() + '\nfirstTokenTree: ' + firstTokenTree.group())

		#double-check that the token you're replacing is the same as the token that you're inserting
		if firstTokenTree.group() != firstTokenParen.group() and verbose:
			print('ERROR, tokens not the same')

		#we have to check if there are any duplicate positions, so that
		#we can find the accurate place within the parent string
		numDuplicatesBeforeParen = 0
		if position == -1:
			position = len(parens) - 1
		for idx, otherParen in enumerate(parens):
			if otherParen == paren and idx < position:
				numDuplicatesBeforeParen += 1

		indexOfParen = find_nth(positionTree, paren, 1)
		if verbose:
			print('indexOfParen: ' + str(indexOfParen))
		endOfParen = indexOfParen + len(paren)
		newPositionTree = positionTree[0:indexOfParen - 1] + treeToInsert + positionTree[endOfParen:]
		newParentTree = newPositionTree
		if position == 0 and len(nestedParentParens) > 1:
			newParentTree = newPositionTree + nestedParentParens[1]
		elif len(nestedParentParens) > 1:
			newParentTree = nestedParentParens[0] + newPositionTree

	if verbose:
		print('inserted tree: ' + newParentTree)
	if newParentTree == '':
		newParentTree = parentTree
	return newParentTree


def collectProductions(treeLists, verbose):
	verbose = False
	productions = []
	for treeAsList in treeLists:
		if verbose:
			print('tree grammar for item ' + treeAsList + ' BEFORE optional tree transformations:')
		tree = Tree.fromstring(treeAsList)

		if verbose:
			print(repr(tree.productions()).replace(',', ',\n' + ' ' * 16))
		# perform optional tree transformations, e.g.:
		tree.collapse_unary(collapsePOS=False)
		tree.chomsky_normal_form(horzMarkov=2)

		if verbose:
			print('tree grammar for item ' + treeAsList + ' AFTER optional tree transformations:')
			print(repr(tree.productions()).replace(',', ',\n' + ' ' * 16))
		productions += tree.productions()

	return productions

#this is a recursive function which will return the tuple of the head node, which contains the child tree representing the entire solution
def parseTag(topXml, musicXml, grammar, productionList, type, verbose=False):
	TreeTuple = collections.namedtuple('ParsedReduction', ['primary', 'primaryTree', 'primaryTreeBranchesLeft', 'secondary', 'secondaryTree', 'secondaryTreeBranchesLeft'])

	tagName = type.lower()
	try:
		headNote = topXml.find('head/chord/note')
	except:
		print("failed!!!")
	headPitchRef = headNote.attrib['id']
	primaryXml = topXml.find('primary')
	primaryTuple = TreeTuple(None, None, None, None, None, None)
	secondaryTuple = TreeTuple(None, None, None, None, None, None)
	if primaryXml != None:
		primaryTuple = parseTag(primaryXml.find(tagName), musicXml, grammar, productionList, type, verbose)
		#if primaryTuple.primary != None and primaryTuple.secondary != None:
		secondaryXml = topXml.find('secondary')
		if secondaryXml == None:
			print('this is bad- no secondary tag when a primary tag exists')
		secondaryTuple = parseTag(secondaryXml.find(tagName), musicXml, grammar, productionList, type, verbose)

	primaryGrammarTree = ''
	secondaryGrammarTree = ''
	secondaryTreeBranchesLeft = None
	primaryTreeBranchesLeft = None
	secondaryIsNestedLeft = False
	if secondaryTuple.primary == 'P1-4-1' and primaryTuple.primary == 'P1-3-4' and primaryTuple.secondary == 'P1-3-1':
		print("found this case")
	if primaryTuple.primary != None and primaryTuple.secondary != None:
		if verbose:
			print('Primary: applying the grammar to the following pitch refs: ' + secondaryTuple.primary + ', ' + primaryTuple.primary + ', ' + primaryTuple.secondary)
		parens = re.findall('(\([^()]*\))', primaryGrammarTree)
		if verbose:
			print("matched the parens: " + str(parens))
		#the primary tuple's primary pitch reference (primaryTuple.primary) must either be
		#the first or the last note in the score, because of the way that the directed
		#trees work for the GTTM data set.
		firstNoteInScore = isFirstNoteInScore(primaryTuple.primary, secondaryTuple.primary, primaryTuple.secondary)
		if primaryTuple.primary == 'P1-2-10' and secondaryTuple.primary == 'P1-2-1' and secondaryTuple.secondary == 'P1-2-4':
			print("found this case")

		firstNoteInScoreSecondary = isFirstNoteInScore(primaryTuple.secondary, secondaryTuple.primary, primaryTuple.primary)
		lastNoteInScoreSecondary = isLastNoteInScore(primaryTuple.secondary, secondaryTuple.primary, primaryTuple.primary)

		if firstNoteInScoreSecondary or lastNoteInScoreSecondary:
			#if the first note or last note temporally is the secondaryTree.secondary, then you don't have anything to sandwich the lowest-prominence note
			#Therefore a 2-note rule would have to apply.

			primarySecondaryGrammarTree = applyGrammarToThreePitchReferences(primaryTuple.primary, primaryTuple.secondary, None, musicXml, grammar, productionList, verbose)
			primaryPrimaryGrammarTree = applyGrammarToThreePitchReferences(primaryTuple.primary, secondaryTuple.primary, None, musicXml, grammar, productionList, verbose)

			treePosition = 0
			primarySecondaryGrammarTree = insertTree(treePosition, primarySecondaryGrammarTree, primaryTuple.secondaryTree, verbose)


			primaryPrimaryGrammarTree = insertTree(treePosition, primaryPrimaryGrammarTree, primaryTuple.primaryTree, verbose)
			#you've already inserted secondaryTuple.primaryTree into secondaryPrimaryGrammarTree, so if secTup.primTree is not blank, you don't need to add the secondarySecondaryGrammarTree


			if firstNoteInScoreSecondary:
				if primaryTuple.primaryTree != '' and primaryTuple.secondaryTree == '':
					primaryGrammarTree = primaryPrimaryGrammarTree
				#elif primaryGrammarTree != '':
				#	secondaryGrammarTree = secondarySecondaryGrammarTree
				else:
					primaryGrammarTree = ' (N ' + primarySecondaryGrammarTree + ') (N ' + primaryPrimaryGrammarTree + ')'
			else:
				primaryGrammarTree = ' (N ' + primaryPrimaryGrammarTree + ') (N ' + primarySecondaryGrammarTree + ')'


			if firstNoteInScoreSecondary:
				primaryIsNestedLeft = True
			else:
				primaryIsNestedLeft = False
		else:

			primaryGrammarTree = applyGrammarToThreePitchReferences(secondaryTuple.primary, primaryTuple.primary, primaryTuple.secondary, musicXml, grammar, productionList, verbose)
			treePosition = 1
			if firstNoteInScore:
				treePosition = 0
			primaryTreeBranchesLeft = firstNoteInScore == False
			primaryGrammarTree = insertTree(treePosition, primaryGrammarTree, primaryTuple.primaryTree, verbose)
			if primaryTuple.secondaryTreeBranchesLeft:
				treePosition = 0
			primaryGrammarTree = insertTree(treePosition, primaryGrammarTree, primaryTuple.secondaryTree, verbose)
		#if primaryTuple.secondaryTree != '':
		#	primaryGrammarTree = '(N ' + primaryGrammarTree + ')'
	if secondaryTuple.primary != None and secondaryTuple.secondary != None:
		if verbose:
			print('Secondary: applying the grammar to the following pitch refs: ' + primaryTuple.primary + ', ' + secondaryTuple.primary + ', ' + secondaryTuple.secondary)
		lastNoteInScore = isLastNoteInScore(primaryTuple.primary, secondaryTuple.primary, secondaryTuple.secondary)

		firstNoteInScoreSecondary = isFirstNoteInScore(secondaryTuple.secondary, secondaryTuple.primary, primaryTuple.primary)
		lastNoteInScoreSecondary = isLastNoteInScore(secondaryTuple.secondary, secondaryTuple.primary, primaryTuple.primary)

		if primaryTuple.primary == 'P1-4-1' and secondaryTuple.primary == 'P1-3-4' and secondaryTuple.secondary == 'P1-3-1':
			print("found this case")
		if firstNoteInScoreSecondary or lastNoteInScoreSecondary:
			#if the first note or last note temporally is the secondaryTree.secondary, then you don't have anything to sandwich the lowest-prominence note
			#Therefore a 2-note rule would have to apply.

			secondarySecondaryGrammarTree = applyGrammarToThreePitchReferences(secondaryTuple.primary, secondaryTuple.secondary, None, musicXml, grammar, productionList, verbose)
			secondaryPrimaryGrammarTree = applyGrammarToThreePitchReferences(primaryTuple.primary, secondaryTuple.primary, None, musicXml, grammar, productionList, verbose)
			#secondaryGrammarTree = applyGrammarToThreePitchReferences(primaryTuple.primary, secondaryTuple.primary, secondaryTuple.secondary, musicXml, grammar, productionList, verbose)
			treePosition = 0
			secondaryPrimaryGrammarTree = insertTree(treePosition, secondaryPrimaryGrammarTree, secondaryTuple.primaryTree, verbose)
			#secondaryPrimaryGrammarTree = insertTree(treePosition, secondaryPrimaryGrammarTree, primaryTuple.secondaryTree, verbose)

			secondarySecondaryGrammarTree = insertTree(treePosition, secondarySecondaryGrammarTree, secondaryTuple.secondaryTree, verbose)
			#you've already inserted secondaryTuple.primaryTree into secondaryPrimaryGrammarTree, so if secTup.primTree is not blank, you don't need to add the secondarySecondaryGrammarTree

			if firstNoteInScoreSecondary:
				if secondaryTuple.primaryTree != '' and secondaryTuple.secondaryTree == '':
					secondaryGrammarTree = secondaryPrimaryGrammarTree
				elif secondaryTuple.secondaryTree != '' and secondaryTuple.primaryTree == '':
					secondaryGrammarTree = secondarySecondaryGrammarTree
				#elif primaryGrammarTree != '':
				#	secondaryGrammarTree = secondarySecondaryGrammarTree
				else:
					secondaryGrammarTree = ' (N ' + secondarySecondaryGrammarTree + ') (N ' + secondaryPrimaryGrammarTree + ')'
			else:
				secondaryGrammarTree = ' (N ' + secondaryPrimaryGrammarTree + ') (N ' + secondarySecondaryGrammarTree + ')'


			if firstNoteInScoreSecondary:
				secondaryIsNestedLeft = True
			else:
				secondaryIsNestedLeft = False
		else:
			secondaryGrammarTree = applyGrammarToThreePitchReferences(primaryTuple.primary, secondaryTuple.primary, secondaryTuple.secondary, musicXml, grammar, productionList, verbose)

			if secondaryTuple.primaryTree != '' and secondaryTuple.secondaryTree != '' and secondaryGrammarTree != '':
				secondarySecondaryGrammarTree = insertTree(1, secondaryTuple.primaryTree, secondaryTuple.secondaryTree, verbose)
				secondaryGrammarTree = secondarySecondaryGrammarTree#insertTree(0, secondaryGrammarTree, secondarySecondaryGrammarTree, verbose)
			else:
				if isBefore(secondaryTuple.secondary, secondaryTuple.primary):
					treePosition = 1
					secondaryTuple.secondaryTree
					secondaryGrammarTree = insertTree(treePosition, secondaryGrammarTree, secondaryTuple.secondaryTree, verbose)
					treePosition = 0
					secondaryGrammarTree = insertTree(treePosition, secondaryGrammarTree, secondaryTuple.primaryTree, verbose)
				else:
					treePosition = 0
					secondaryGrammarTree = insertTree(treePosition, secondaryGrammarTree, secondaryTuple.secondaryTree, verbose)
					#added just now...
					treePosition = 1
					secondaryGrammarTree = insertTree(treePosition, secondaryGrammarTree, secondaryTuple.primaryTree, verbose)

		secondaryTreeBranchesLeft = firstNoteInScoreSecondary

		treePosition = 1
		if lastNoteInScore:
			treePosition = 0
		if firstNoteInScoreSecondary is False and lastNoteInScoreSecondary is False and not (secondaryTuple.primaryTree != '' and secondaryTuple.secondaryTree != '' and secondaryGrammarTree != ''):
			secondaryGrammarTree = insertTree(treePosition, secondaryGrammarTree, secondaryTuple.primaryTree, verbose)
	"""if (secondaryTuple.primaryTree != None and secondaryTuple.primaryTree not in secondaryGrammarTree):
		print("secondaryTuple.primaryTree not in secondaryGrammarTree for (P.P, S.P, S.S) of: (" + primaryTuple.primary + ', ' + secondaryTuple.primary + ', ' + secondaryTuple.secondary)
	if (secondaryTuple.secondaryTree != None and secondaryTuple.secondaryTree not in secondaryGrammarTree):
		print("secondaryTuple.secondaryTree not in secondaryGrammarTree for (P.P, S.P, S.S) of: (" + primaryTuple.primary + ', ' + secondaryTuple.primary + ', ' + secondaryTuple.secondary)
	if (primaryTuple.primaryTree != None and primaryTuple.primaryTree not in primaryGrammarTree):
		print("primaryTuple.primaryTree not in primaryGrammarTree for for (P.P, P.S, S.P) of: (" + primaryTuple.primary + ', ' + primaryTuple.secondary + ', ' + secondaryTuple.primary)
	if (primaryTuple.secondaryTree != None and primaryTuple.secondaryTree not in primaryGrammarTree):
		print("primaryTuple.secondaryTree not in primaryGrammarTree for for (P.P, P.S, S.P) of: (" + primaryTuple.primary + ', ' + primaryTuple.secondary + ', ' + secondaryTuple.primary)
	"""
	#if secondaryGrammarTree != '' and primaryGrammarTree != '':
	#	if secondaryIsNestedLeft:
	#		#here we just insert the subtree in here, because we didn't want to apply the rules to
	#		#a nested left subtree, but we also can't ignore the subtree from the right hand side
	#		secondaryGrammarTree = '(N ' + secondaryGrammarTree + ') (N ' + primaryGrammarTree + ')'
	#	else:
	#		secondaryGrammarTree = insertTree(-1, secondaryGrammarTree, primaryGrammarTree, verbose)
	#	primaryGrammarTree = ''
	curTuple = TreeTuple(headPitchRef, primaryGrammarTree, primaryTreeBranchesLeft, secondaryTuple.primary, secondaryGrammarTree, secondaryTreeBranchesLeft)
	return curTuple

def lookUpPitchReference(scoreReference, musicXml, verbose=False, returnFullNote=False):

	if scoreReference == 'P1-6-4' and verbose:
		print("problem note")
	refList = scoreReference.split("-")
	if verbose:
		print(refList)
		print("looking for partID of " + refList[0])
	retNote = None
	for part in musicXml.parts:
		if verbose:
			print ("part.id is " + part.id)
		#for some reason the id attribute is stored in  part.groups[0]
		if part.groups[0] == None or part.groups[0] != refList[0]:
			continue
		measureNum = int(refList[1])
		for measure in part.measures(measureNum, measureNum, collect=('Measure'), gatherSpanners=False):
			numToAdd = 0
			if len(measure.elements) > 0:
				typeString = type(measure.elements[0]).__name__
				while typeString != 'Note' and typeString != 'Rest':
					numToAdd += 1
					typeString = type(measure.elements[numToAdd]).__name__
			noteNum = int(refList[2]) - 1
			if noteNum + numToAdd >= len(measure.elements):
				print("bad noteNum")
			retNote = measure.elements[noteNum + numToAdd]
			#if retNote contains the tag:<tie type="stop"/>, then use the next one
			typeString = type(measure.elements[noteNum + numToAdd]).__name__

			while typeString != 'Note' or (typeString == 'Note' and retNote.tie != None and retNote.tie.type == 'stop'):
				if typeString == 'Note' and retNote.tie != None and retNote.tie.type == 'stop':
					print('stooooopppies')
				numToAdd += 1
				typeString = type(measure.elements[noteNum + numToAdd]).__name__
				retNote = measure.elements[noteNum + numToAdd]

	if retNote != None and returnFullNote is False:
		retNote = retNote.ps
	return retNote

def getGrammarParseFromSolutionXml(solutionXml, musicXml, grammar, productionList, type, verbose=False):
	root = solutionXml.getroot()
	rootName = type.lower()
	topXml = root.find(rootName)
	headTuple = parseTag(topXml, musicXml, grammar, productionList, type, verbose)
	returnString = ''
	if headTuple.primaryTree != '' and headTuple.secondaryTree != '':
		returnString = '(S (N ' + headTuple.secondaryTree + ') (N ' + headTuple.primaryTree + '))'
	else:
		#one of these is blank, so order doesn't matter
		returnString = '(S ' + headTuple.secondaryTree + headTuple.primaryTree + ')'
	return returnString

def getAllProductions(directory, solutionsDir, fileList, type, verbose=False, harmonicGrammar=False, triadType="MAJOR"):
	pitchLists = []
	intervalLists = []
	solutionTrees = []
	allProductions = []
	allTestSolutionsDict = {}
	for filepath in fileList:
		curPitchList = getPitchListFromFile(filepath)
		pitchLists.append(curPitchList)
		intervalLists.append(getIntervalStringsFromPitchList(curPitchList))
		print(intervalLists[-1])
		if "MSC" in basename(filepath):
			filenumber = int(basename(filepath)[4:7])
			if filenumber >= 268:
				reductionFilename = type + basename(filepath)[3:7] + "_1" + basename(filepath)[7:]
			else:
				reductionFilename = type + basename(filepath)[3:]
		else:
			reductionFilename = type + "-" + basename(filepath)
		reductionFilepath = directory + '/' + solutionsDir + '/' + reductionFilename
		print(reductionFilepath)
		ET = ElementTree()
		ET.parse(reductionFilepath)
		loadedMusicFile = converter.parse(filepath)
		musicGrammar = CFG.fromstring(musicGrammarString)
		#for prTag in ET.iter("note"):
		#	print(prTag.attrib['id'])
		#	lookUpPitchReference(prTag.attrib['id'], loadedMusicFile, False)

		solutionTree = getGrammarParseFromSolutionXml(ET, loadedMusicFile, musicGrammar, allProductions, type, verbose)
		solutionTrees.append(solutionTree)
		allProductions.append('(S (N) (N))')
		#treeObj = Tree.fromstring(solutionTree)
		#treeObj.draw()
		#solutionTree1 = treeObj

		allTestSolutionsDict[filepath] = solutionTree
	return allTestSolutionsDict, allProductions

def parseAllTestXmls(fileList, grammar, allTestSolutionsDict, verbose=False, displayTrees=False):
	testPitchLists = []
	testIntervalLists = []
	totalCorrect = 0
	totalCorrectNonN = 0
	totalProductions = 0
	totalLeaves = 0
	parseTreeStrings = {}
	for filepath in fileList:
		curPitchList = getPitchListFromFile(filepath)
		testPitchLists.append(curPitchList)
		testIntervalLists.append(getIntervalStringsFromPitchList(curPitchList, verbose))
		if verbose:
			print(testIntervalLists[-1])
		listLen = len(testIntervalLists[-1])
		if verbose:
			print(tree)
		parser = ViterbiParser(grammar)
		if verbose:
			parser.trace(0)#3
		else:
			parser.trace(0)
		try:
			parses = parser.parse_all(testIntervalLists[-1])
		except Exception as errorMsg:
			print("error parsing file " + filepath)
			print(errorMsg)
		numTrees = sum(1 for _ in parses)
		if numTrees > 0 and displayTrees == True:
			from nltk.draw.tree import draw_trees
			draw_trees(*parses)
		if numTrees == 0:
			print("Couldn't find a valid parse, this is bad, very very bad")
			return 0,0
		numCorrect = 0
		numCorrectNonN = 0
		bottomCorrect = 0
		bottomCorrectNonN = 0
		solutionTree = None
		try:
			solutionTreeStr = allTestSolutionsDict[filepath]
			solutionTree = Tree.fromstring(solutionTreeStr)
		except Exception as errorMsg:
			print("couldn't find solution for file " + filepath)
			print(errorMsg)
		if solutionTree != None and solutionTree != '':
			parseTreeStrings[filepath] = str(parses[0])
			numCorrect, numCorrectNonN = validate_tree.compareTrees(solutionTree, parses[0])
			numProductions = len(solutionTree.productions())
			totalProductions += numProductions

			#solutionTree.draw()
			#parses[0].draw()
			bottomCorrect, bottomCorrectNonN = validate_tree.compareTreesBottomUp(solutionTree, parses[0])
			parseTreeStrings[filepath+'_afterComparison'] = str(parses[0])
			totalLeaves += len(solutionTree.leaves())
			#parses[0].draw()

		totalCorrect += bottomCorrect
		totalCorrect += numCorrect
		totalCorrectNonN += numCorrectNonN
		totalCorrectNonN += bottomCorrectNonN
	return totalCorrect, totalCorrectNonN, totalProductions, totalLeaves, parseTreeStrings


"""******************Harmony grammar function**********************"""

def getKeyFromMusicXml(musicXml):
	keySigs = musicXml.flat.getKeySignatures()
	if len(keySigs) == 1:
		return keySigs[0]

def getScaleDegreeFromPitchNum(pitchNum, scale):
	curNote = note.Note(pitchNum)
	curPitchObj = curNote.pitches[0]

	print(curNote.name)
	enharms = curPitchObj.getAllCommonEnharmonics()

	pitchDegree = scale.getScaleDegreeFromPitch(curNote.name, direction='descending')
	if pitchDegree is None:
		for enharm in enharms:
			#print(str(enharm))
			pitchDegree = scale.getScaleDegreeFromPitch(str(enharm))
			if pitchDegree is not None:
				break
	return pitchDegree

def getChordRootPitchClassUnchecked(chordDegree, key, stripNumbers=True):
	chordRootPitchClass = -1
	chordDegreeJustLetters = chordDegree

	if stripNumbers:
		m = re.match('([A-z]+)', chordDegree)
		chordDegreeJustLetters = m.group(1)
	if key.mode == 'minor':
		chordRootPitchClass = minorScaleChordDegreeToPitchClass[chordDegreeJustLetters]
	elif key.mode == 'major':
		chordRootPitchClass = majorScaleChordDegreeToPitchClass[chordDegreeJustLetters]
	return chordRootPitchClass

def getTypeFromChordDegree(chordDegree, key):
	topChordDegree = chordDegree
	if '/' in chordDegree:
		topChordDegree = chordDegree[:chordDegree.index('/')]
	type = ''
	if key.mode == 'minor':
		if topChordDegree in minorScaleMajorChords:
			type = "MAJOR"
		elif topChordDegree in minorScaleMinorChords:
			type = "MINOR"
	elif key.mode == 'major':
		if topChordDegree in majorScaleMajorChords:
			type = "MAJOR"
		elif topChordDegree in majorScaleMinorChords:
			type = "MINOR"

	return type

def getRootPitchClassFromChordDegree(chordDegree, key):
	topChordDegree = chordDegree
	baseChordDegree = ''
	baseRootPitchClass = -1
	rootPitchClass = -1
	if '/' in chordDegree:
		topChordDegree = chordDegree[:chordDegree.index('/')]
		baseChordDegree = chordDegree[chordDegree.index('/') + 1:]
		baseRootPitchClass = getChordRootPitchClassUnchecked(baseChordDegree, key)

	chordRootPitchClass = getChordRootPitchClassUnchecked(topChordDegree, key)

	if baseRootPitchClass != -1:
		rootPitchClass = baseRootPitchClass + chordRootPitchClass
		if rootPitchClass > 11:
			rootPitchClass = rootPitchClass - 12
	else:
		rootPitchClass = chordRootPitchClass
	return rootPitchClass


def getSolutionTreeForRangeOfNotes(pitchRefList, musicXml, solutionXml, type, verbose=False):
	root = solutionXml.getroot()
	rootName = type.lower()
	topXml = root.find(rootName)
	print('looking for tree with only pitchrefs:')
	print(pitchRefList)
	headTuple = findTagsWithRefs(topXml, pitchRefList, musicXml, type, verbose)
	containsOnlyPitchRefs = validateThatTreeOnlyIncludesPitchRefs(pitchRefList, headTuple, type, verbose)
	if containsOnlyPitchRefs == False:
		headTuple = None
	return headTuple


def validateThatTreeOnlyIncludesPitchRefs(pitchRefList, head, type, verbose=False):
	tagName = type.lower()
	try:
		headNote = head.find('head/chord/note')
	except:
		print("failed!!!")

	headPitchRef = headNote.attrib['id']
	primaryXml = head.find('primary')
	secondaryXml = head.find('secondary')

	if headPitchRef not in pitchRefList:
		print('found the extra pitchref: ' + str(headPitchRef))
		return False
	elif primaryXml != None:
		hasOnlyTheseRefs = validateThatTreeOnlyIncludesPitchRefs(pitchRefList, primaryXml.find(tagName), type)
		hasOnlyTheseRefs = hasOnlyTheseRefs != False and validateThatTreeOnlyIncludesPitchRefs(pitchRefList, secondaryXml.find(tagName), type) != False
		return hasOnlyTheseRefs
	else:
		return True

def findTagsWithRefs(topXml, pitchRefList, musicXml, type, verbose=False):
	tagName = type.lower()
	try:
		headNote = topXml.find('head/chord/note')
	except:
		print("failed!!!")

	headPitchRef = headNote.attrib['id']
	primaryXml = topXml.find('primary')
	secondaryXml = topXml.find('secondary')
	secondaryHeadNote = ''
	if secondaryXml != None:
		secondRoot = secondaryXml.find(tagName)
		secondaryHeadNote = secondRoot.find('head/chord/note')
		secondaryPitchRef = secondaryHeadNote.attrib['id']
	if headPitchRef in pitchRefList and secondaryPitchRef in pitchRefList:
		print('found the pitchref: ' + str(headPitchRef))
		return topXml
	elif primaryXml != None:
		primaryHead = findTagsWithRefs(primaryXml.find(tagName), pitchRefList, musicXml, type, verbose)
		secondaryHead = findTagsWithRefs(secondaryXml.find(tagName), pitchRefList, musicXml, type, verbose)
		if primaryHead is not None:
			return primaryHead
		elif secondaryHead is not None:
			return secondaryHead

#The triad types are: {"MAJOR", "MINOR"}
def getPitchRefListsOfTriadTypeFromFile(filepath, triadType, musicXml, type="MusicXml"):
	pitchLists = []
	if type == "MusicXml":
		fileBase = basename(filepath)
		basenameIndex = filepath.index(fileBase)

		harmonyFilePath = filepath[:basenameIndex] + "HM-" + basename(filepath)

		ET = ElementTree()
		ET.parse(harmonyFilePath)
		regionXml = ET.getroot()

		key = getKeyFromMusicXml(musicXml)

		while regionXml:
			for chord in regionXml.findall("chord-span"):
				originalChordDegree = chord.attrib['deg']
				print(originalChordDegree)
				chordRootPitchClass = 0
				curChordType = getTypeFromChordDegree(originalChordDegree, key)
				pitchList = []
				if curChordType == triadType:
					for pitchRef in chord.findall("note"):
						pitchRefId = pitchRef.attrib['id']
						pitchList.append(pitchRefId)
					pitchLists.append([originalChordDegree, pitchList])
			regionXml = regionXml.find("region")
	return pitchLists

#the pitchAndChordList is expected to be of the form [chordDegree, [pitchref1, pitchref2, ...]]
def getChordRelativePitchClassesFromPitchRefList(pitchAndChordList, musicXml, includeChordToneNotation=False):
	pitchRefLists = []
	chordRelativeIntervalList = []

	key = getKeyFromMusicXml(musicXml)
	scale = key.getScale()

	chordDegree = pitchAndChordList[0]
	pitchRefList = pitchAndChordList[1]
	#this chordroot pitchclass is relative to the key root still
	chordRootPitchClass = getRootPitchClassFromChordDegree(chordDegree, key)
	print(chordDegree)
	root = scale.pitches[0]
	scaleRootPitchClass = root.ps % 12
	for pitchRefId in pitchRefList:
		curPitch = lookUpPitchReference(pitchRefId, musicXml)
		"""pitchDegree = getScaleDegreeFromPitchNum(curPitch, scale)
		relativePitch = -1
		if key.mode == 'minor':
			print("looking up pitch degree: " +str(pitchDegree))
			relativePitch = minorDegreeToPitchClass[pitchDegree]
		elif key.mode == 'major':
			relativePitch = majorDegreeToPitchClass[pitchDegree]
		"""
		curPitchClass = curPitch % 12
		print ("curPitch is: " + str(curPitch) + ", chordRootPitchClass is: " + str(chordRootPitchClass) + ", and scaleRootPitchClass is: " + str(scaleRootPitchClass))
		chordRootRelativePitchClass = curPitchClass - (chordRootPitchClass + scaleRootPitchClass)
		scaleRelativePitch = curPitch - (chordRootPitchClass + scaleRootPitchClass)
		if chordRootRelativePitchClass < 0:
			chordRootRelativePitchClass += 12
		if chordRootRelativePitchClass > 11:
			chordRootRelativePitchClass = chordRootRelativePitchClass % 12
		print(chordRootRelativePitchClass)
		chordRelativeIntervalList.append(scaleRelativePitch)
	return chordRelativeIntervalList

def getHarmonicGrammarParseFromSolutionXml(headXml, musicXml, grammar, productionList, type, verbose=False):
	headTuple = parseTag(headXml, musicXml, grammar, productionList, type, verbose)
	if headTuple.primaryTree != '' and headTuple.secondaryTree != '':
		returnString = '(S (N ' + headTuple.secondaryTree + ') (N ' + headTuple.primaryTree + '))'
	else:
		#one of these is blank, so order doesn't matter
		returnString = '(S ' + headTuple.secondaryTree + headTuple.primaryTree + ')'
	return returnString

#triadType represents the following two options: {"MAJOR", "MINOR"}
#The grammar will be of that type as well
def getAllProductionsHarmonicGrammar(directory, solutionsDir, fileList, type, triadType="MAJOR", verbose=False):
	pitchLists = []
	intervalLists = []
	solutionTrees = []
	allProductions = []
	allTestSolutionsDict = {}
	for filepath in fileList:
		musicXml = converter.parse(filepath)

		curPitchList = getPitchRefListsOfTriadTypeFromFile(filepath, triadType, musicXml)

		for pList in curPitchList:
			curRelativePitchList = getChordRelativePitchClassesFromPitchRefList(pList, musicXml)
			pitchLists.append(curRelativePitchList)
		for pList in pitchLists:
			curIntervalList = getIntervalStringsFromPitchClassList(pList, chordType="MINOR")
			intervalLists.append(curIntervalList)
		print(intervalLists[-1])
		reductionFilename = type + "-" + basename(filepath)
		reductionFilepath = directory + '/' + solutionsDir + '/' + reductionFilename
		print(reductionFilepath)
		reductionFileXml = ElementTree()
		reductionFileXml.parse(reductionFilepath)
		with open(harmonyGrammarStringExplicitChordTonesFilename, 'r') as f:
			harmonyGrammarStringExplicitChordTones = f.read()
		harmonicGrammar = CFG.fromstring(harmonyGrammarStringExplicitChordTones)
		for iList in intervalLists:
			#solutionXml = getSolutionTreeForRangeOfNotes(pList[1], musicXml, reductionFileXml, type, verbose)
			cp = ChartParser(harmonicGrammar, trace=1)
			chart = cp.chart_parse(iList)
			parses = list(chart.parses(harmonicGrammar.start()))

			print(iList)
			numTrees = len(parses)
			numDrawings = 0
			for tree in parses:
				print(tree)
				tree.draw()
				numDrawings += 1
				if numDrawings > 3:
					break


			#if numTrees > 0:
			#	from nltk.draw.tree import draw_trees
			# 		draw_trees(*parses[0])
			#if solutionXml != None:
			#	solutionTree = getHarmonicGrammarParseFromSolutionXml(solutionXml, musicXml, harmonicGrammar, allProductions, type, verbose)
			#	#solutionTrees.append(solutionTree)
			#	#allProductions.append('(S (N) (N))')
			#	treeObj = Tree.fromstring(solutionTree)
			#	#print(tostring(solutionTree, 'utf-8'))
			#	treeObj.draw()
		#solutionTree1 = treeObj

		#allTestSolutionsDict[filepath] = solutionTree
	return allTestSolutionsDict, allProductions
