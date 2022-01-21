
import validate_tree
import constraint_grammar
import itertools
import operator
import collections
from nltk import *
from music21 import *
from xml.etree.ElementTree import *
from os.path import basename
from nltk.parse import ViterbiParser
import score_from_tree
import json
from nltk.tree import Tree, ProbabilisticTree

MAX_NUM_NOTES_PER_SONG = 100000

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


def initLock(l):
	global lock
	lock = l

def getPitchClassIntervalFromTwoNotes(note1, note2, pitchRef1, pitchRef2, key, harmonyXml, additionalDatum=None, isLeftParent=False):
	retVal = 0
	difference = note2.pitch.ps - note1.pitch.ps
	if additionalDatum is not None:
		difference += int(additionalDatum)
	if difference < 0:
		retVal = difference % -12
	else:
		retVal = difference % 12
	return str(int(retVal))

def isChordTone(romanChord, note):
	if romanChord is None:
		return False
	return note.pitchClass in romanChord.orderedPitchClasses

def convertKeyNicknamesToKeySymbols(keyNickname):
	if 's' in keyNickname:
		if 'i' in keyNickname:
			return keyNickname[0] + "#"
		else:
			return keyNickname[0] + "-"
	return keyNickname

#This only works for 4/4 time right now
def getMetricLevel(music21Note):
	rangeList = range(16)
	onset = (music21Note.offset % 4) * 4
	distanceToBeatList = [abs(onset - beat) for beat in rangeList]
	beatIndex = distanceToBeatList.index(min(distanceToBeatList))
	retVal = -1
	if beatIndex == 0: #0
		retVal = 4
	elif beatIndex % 8 == 0:#8
		retVal = 3
	elif beatIndex % 4 == 0:#4, 12
		retVal = 2
	elif beatIndex % 2 == 0:#2, 6, 10 , 14
		retVal = 1
	else:
		retVal = 1
	return retVal



def getKeyRelativePitchClassWithChordInfoAndStartEndSymbols(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, False, True, True, isLeftParent)

def getKeyRelativePitchClassWithChordInfo(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, False, True, False, isLeftParent)

def getKeyRelativePitchClassWithStartEndSymbols(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, False, False, True, isLeftParent)

def getKeyRelativePitchClassWithChordInfoStartEndSymbolsAndMetricIntervals(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, True, True, True, isLeftParent)

def getKeyRelativePitchClassWithChordInfoAndMetricInterval(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, True, True, False, isLeftParent)

def getKeyRelativePitchClassWithMetricInterval(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, True, False, False, isLeftParent)

def getKeyRelativePitchClassOnly(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, isLeftParent=False):
	return getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum, False, False, False, isLeftParent)


def getKeyRelativePitchClass(note1, note2, pitchRef1, pitchRef2, keyScale, harmonyXml, additionalDatum=None, addMetricInfo=False, addChordInfo=False, addStartEndSymbols=False, isLeftParent=False):


	appendBefore = ''
	appendAfter = ''
	if addChordInfo:
		roman1String, keyNickname1 = getRomanAndLocalKeyFromPitchRefAndNotation(pitchRef1, harmonyXml)
		roman2String, keyNickname2 = getRomanAndLocalKeyFromPitchRefAndNotation(pitchRef2, harmonyXml)

		keyString1 = convertKeyNicknamesToKeySymbols(keyNickname1)
		keyString2 = convertKeyNicknamesToKeySymbols(keyNickname2)
		try:
			key1 = key.Key(keyString1)
		except:
			key1 = keyScale
		try:
			key2 = key.Key(keyString2)
		except:
			key2 = keyScale
		#print("romanString1 is: '" + roman1String + "'\nromanString2 is: '" + roman2String +"'")
		chord1 = getChordObjectFromRoman(roman1String, key1)
		chord2 = getChordObjectFromRoman(roman2String, key2)

		if isChordTone(chord1, note1):
			appendBefore = 'c'
		if isChordTone(chord2, note2):
			appendAfter = 'c'
	if addStartEndSymbols:
		pitchRefList = getPitchRefListFromHarmonyFile(harmonyXml)
		if pitchRef1 == pitchRefList[0]:
			appendBefore = 'S' + appendBefore
		if pitchRef2 == pitchRefList[-1]:
			appendAfter = appendAfter + 'E'
	intDatum = 0
	metricDatum = 0
	#we have to check for the 'S' and 'E' start and end tokens
	#'S' will only occur at the beginning, and 'E' only at the end
	if additionalDatum is not None and additionalDatum != '':
		intDatum = additionalDatum

		if addStartEndSymbols:
			if isLeftParent:
				appendBefore = ''
			else:
				appendAfter = ''
			#I'm going to destructively modify additionalDatum, by removing the 'S' or 'E', if they exist

			if additionalDatum[0] == 'S':
				intDatum = intDatum[1:]
				additionalDatum = additionalDatum[1:]
				if isLeftParent:
					appendBefore = 'S'
			if additionalDatum[-1] == 'E':
				intDatum = intDatum[:-1]
				additionalDatum = additionalDatum[:-1]
				if not isLeftParent:
					appendAfter = 'E'
		#appendBefore and appendAfter might already be set
		#if 'S' is set, and a 'c' exists before the interval, we want to prepend 'Sc'
		#if 'E' is set, and a 'c' exists after the interval, we want to append 'cE'
		#therefore, we add to the strings, instead of setting them.
		#Also to consider is that we may have already set them to 'c' based on the original note pair
		#so make sure we don't append a 'c' to a 'c'
		if addChordInfo:
			if additionalDatum[0] == 'c':
				intDatum = intDatum[1:]
				if isLeftParent:
					appendBefore = 'c'
			if additionalDatum[-1] == 'c':
				intDatum = intDatum[:-1]
				if not isLeftParent:
					appendAfter = 'c'
		#at this point, the string is just the interval information
		pitchInterval = intDatum
		if addMetricInfo:
			intervalList = intDatum.split('.')
			pitchInterval = intervalList[0]
			if len(intervalList) > 1:
				metricInterval = intervalList[1]
				metricDatum = int(metricInterval)
		intDatum = int(pitchInterval)
	scale1 = keyScale.getScale()
	scale2 = keyScale.getScale()
	if addChordInfo:
		scale1 = key1.getScale()
		scale2 = key2.getScale()
	keyRelativePitchClass1 = getScaleDegreeFromPitchNum(note1.pitch.ps, scale1)
	keyRelativePitchClass2 = getScaleDegreeFromPitchNum(note2.pitch.ps, scale2)
	if keyRelativePitchClass1 is None:
		#print('Error: keyRelativePitchClass1 for scale of "' + str(scale1) + '" and note of "' + note1.name + '" was None')
		keyRelativePitchClass1 = getClosestScaleDegree(note1, scale1)
		#print('keyRelativePitchClass1 is now "' + str(keyRelativePitchClass1) + '"')
	if keyRelativePitchClass2 is None:
		#print('Error: keyRelativePitchClass2 for scale of "' + str(scale2) + '" and note of "' + note2.name + '" was None')
		#print('note2.pitches is "' + str(note2.pitches) + '" was None')
		keyRelativePitchClass2 = getClosestScaleDegree(note2, scale2)
		#print('keyRelativePitchClass2 is now "' + str(keyRelativePitchClass2) + '"')
	#gotta consider the direction of the actual interval
	isPositiveInterval = False
	if note1.pitch.ps < note2.pitch.ps:
		isPositiveInterval = True

	difference = keyRelativePitchClass2 - keyRelativePitchClass1 + intDatum
	if not isPositiveInterval and keyRelativePitchClass2 > keyRelativePitchClass1:
		difference = keyRelativePitchClass2 - (keyRelativePitchClass1 + 7) + intDatum
	if isPositiveInterval and keyRelativePitchClass2 < keyRelativePitchClass1:
		difference = (keyRelativePitchClass2 + 7) - keyRelativePitchClass1 + intDatum

	if difference < 0:
		retVal = difference % -8
	else:
		retVal = difference % 8
	metricIntervalString = ""
	if addMetricInfo:
		metricLevel1 = getMetricLevel(note1)
		metricLevel2 = getMetricLevel(note2)
		metricIntervalString = '.' + str(int(metricLevel2 - metricLevel1 + metricDatum))

	dataRep = appendBefore + str(int(difference)) + metricIntervalString + appendAfter
	return dataRep

def fixMelodyStreamDurations(melodyStream):
	for note1, note2 in pairwise(melodyStream.flat.notes):
		note1End = note1.offset + note1.duration.quarterLength
		note2Start = note2.offset

		if note1End > note2Start:
			note1.duration.quarterLength = note2Start - note1.offset


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

def getNoteListFromFile(filepath, type="MusicXml"):
	noteList = []
	if type == "MusicXml":
		loadedMusicFile = converter.parse(filepath)
		flatFile = loadedMusicFile.flat
		for n in flatFile.notes:
			if (n.tie != None and n.tie.type != 'start') or n.duration.isGrace:
				continue
			noteList.append(n)
	return noteList


def getKeyFromMusicXmlFilepath(filepath, type="MusicXml"):
	if type == "MusicXml":
		loadedMusicFile = converter.parse(filepath)
		return getKeyFromMusicXml(loadedMusicFile)
	return None

def getPitchRefsFromRegionXml(xml, pitchRefList):
	for child in xml:
		if child.tag == 'region':
			newPitchRefList = getPitchRefsFromRegionXml(child, [])
			for pr in newPitchRefList:
				pitchRefList.append(pr)
		elif child.tag == 'chord-span':
			for note in child:
				if note.tag == 'region':
					newPitchRefList = getPitchRefsFromRegionXml(note, [])
					for pr in newPitchRefList:
						pitchRefList.append(pr)
					continue
				elif note.tag != 'note':
					continue
				pitchRefList.append(note.attrib['id'])
	return pitchRefList


def getRomanNumeralAndKeyUsingPitchRefInAnyRegion(xml, pitchRef):
	for child in xml:
		if child.tag == 'region':
			roman, chordLabel = getRomanNumeralAndKeyUsingPitchRefInAnyRegion(child, pitchRef)
			if roman != None:
				return roman, chordLabel
		elif child.tag == 'chord-span':
			for note in child:
				if note.tag == 'region':
					roman, chordLabel = getRomanNumeralAndKeyUsingPitchRefInAnyRegion(note, pitchRef)
					if roman != None:
						return roman, chordLabel
					continue
				elif note.tag != 'note':
					continue
				if note.attrib['id'] == pitchRef:
					return child.attrib['deg'], xml.attrib['label']
	return None, None

def getPitchRefListFromHarmonyFile(harmonyXml):
	pitchRefList = getPitchRefsFromRegionXml(harmonyXml, [])
	return pitchRefList

def getPitchRefListFromSolutionFile(solutionXml, tagName):
	pitchRefList = score_from_tree.get_pitch_list_from_solution_tree(solutionXml, tagName, [])
	pitchRefList.sort(key=pitchRefToNum)
	return pitchRefList

def getRomanAndLocalKeyFromPitchRefAndNotation(pitchRef, harmonyXml):
	return getRomanNumeralAndKeyUsingPitchRefInAnyRegion(harmonyXml, pitchRef)

def getKeySignature(musicXml):
	for part in musicXml.parts:
		partFlat = part.flat
		keySigs = partFlat.getElementsByClass('KeySignature')
		if len(keySigs) > 1:
			print('there are multiple key sigs, oh no!')
	return keySigs[0]

def getDataRepSequenceFromPitchLists(noteList, pitchRefList, key, harmonyXml, repFunc, verbose=False):
	obsList = []
	if len(noteList) != len(pitchRefList):
		print("error! pitches (len " + str(len(noteList)) + ") and pitchrefs (len " + str(len(pitchRefList)) + ") do not amount to the same number")
		print("pitches: " +str(noteList))
		print("pitchRefs: " +str(pitchRefList))
	first = True
	for index, pitch in enumerate(noteList):

		if first:
			first = False
			continue
		curObservation = repFunc(noteList[index - 1], noteList[index], pitchRefList[index - 1], pitchRefList[index], key, harmonyXml)
		obsList.append(curObservation)
		if verbose:
			print(curObservation)

	#TODO:need to add start and end tags here
	return obsList

#returns the root of the chord as a pitch class
def getChordObjectFromRoman(romanString, key):
	if romanString == '+III':
		#print('romanstring is: "' + romanString + '"')
		#print('key is: "' + str(key) + '"')
		romanString ="III"

	try:
		curRoman = roman.RomanNumeral(romanString, key.getScale())
	except:
		return None
	return curRoman

def getIntervalStringsFromPitchList(pitchList, verbose=False):
	intervalList = []
	for p1, p2 in pairwise(pitchList):
		curInterval = (p2.pitch.ps - p1.pitch.ps) #% 12
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

def loadGrammarFromFile(foldNumber, foldFile, verbose=False):
	allProductions = []
	try:
		f = open(foldFile, 'r')
		solutionTreeDict = json.load(f)
		fileSucceeded = True
		allProductions = [solutionTreeDict[key] for index, key in enumerate(solutionTreeDict)]
	except:
		print('file ' + foldFile + ' did not exist')
	S = Nonterminal('S')
	smallTrees = collectProductions(allProductions, verbose)
	trainedGrammar = induce_pcfg(S, smallTrees)
	return trainedGrammar

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
		"""tree.collapse_unary(collapsePOS=False)
		print("after unary")
		print(tree)
		tree.chomsky_normal_form(horzMarkov=2)
		print("after chomsky")
		print(tree)"""
		if verbose:
			print('tree grammar for item ' + treeAsList + ' AFTER optional tree transformations:')
			print(repr(tree.productions()).replace(',', ',\n' + ' ' * 16))
		#print(tree.productions())
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
			primaryTreeBranchesLeft = firstNoteInScore is False
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
				print(str(musicXml.show()))
				print("bad noteNum: " + scoreReference)
				print("noteNum + numToAdd is: " + str(noteNum + numToAdd))
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
		retNote = retNote.pitch.ps
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

def pruneNotesForTiesAndNonNotes(notes):
	#remove any non-note objects
	newNotes = notes.notes
	#remove any ties
	notesNoTies = [n for n in newNotes if (n.tie is None or (n.tie.type == 'start')) and n.isGrace == False]

	return notesNoTies

class OrderedNode:
	def __init__(self, musicXml, _node, _priority, _treeIndex, _visited, _interval=0):
		self.node = _node
		self.priority = _priority
		self.treeIndex = _treeIndex
		self.visited = _visited
		self.interval = _interval
		self.note = self.getNote(musicXml)

	def getNote(self, musicXml):
		headNote = self.node.find('head/chord/note')
		pitchRef = headNote.attrib['id']
		return lookUpPitchReference(pitchRef, musicXml, False, True)

	def getPitchRef(self):
		headNote = self.node.find('head/chord/note')
		pitchRef = headNote.attrib['id']
		return pitchRef

	def isBeforeOrderedNote(self, otherOrderedNode):
		headNote = self.node.find('head/chord/note')
		pitchRef = headNote.attrib['id']
		otherHeadNote = otherOrderedNode.node.find('head/chord/note')
		otherPitchRef = otherHeadNote.attrib['id']
		return isBefore(pitchRef, otherPitchRef)


#this function will add the child nodes of a node if they exist, and return true
#If the child nodes don't exist, it returns false
def addChildNodesToQueue(musicXml, harmonyXml, orderedNode, queue, treeType, repFunc):
	node = orderedNode.node
	priorityIndex = orderedNode.priority
	key = getKeyFromMusicXml(musicXml)
	primaryXml = node.find('primary')
	retVal = False
	if primaryXml != None:
		secondaryXml = node.find('secondary')

		primOrderedNode = OrderedNode(musicXml, primaryXml.find(treeType), priorityIndex + 1, orderedNode.treeIndex, True)
		secOrderedNode = OrderedNode(musicXml, secondaryXml.find(treeType), priorityIndex + 2, orderedNode.treeIndex, False)

		if primOrderedNode.isBeforeOrderedNote(secOrderedNode):
			queue.append(primOrderedNode)
			queue.append(secOrderedNode)
			difference = repFunc(primOrderedNode.note, secOrderedNode.note, primOrderedNode.getPitchRef(), secOrderedNode.getPitchRef(), key, harmonyXml)
			#primary node just inherits its interval from when it was originally computed.
			primOrderedNode.interval = orderedNode.interval
			secOrderedNode.interval = difference
		else:
			queue.append(secOrderedNode)
			queue.append(primOrderedNode)
			difference = repFunc(secOrderedNode.note, primOrderedNode.note, primOrderedNode.getPitchRef(), secOrderedNode.getPitchRef(), key, harmonyXml)
			#primary node just inherits its interval from when it was originally computed.
			primOrderedNode.interval = orderedNode.interval
			secOrderedNode.interval = difference

		retVal = True
	return retVal

def getPositionOfNode(grammarTree, node, verbose=False):
	positions = grammarTree.treepositions()
	foundPosAlready = False
	retVal = None
	for pos in positions:
		if verbose:
			print('node: ' + str(grammarTree[pos]) + '\npos: ' + str(pos))
		grammarEqualsNode = grammarTree[pos] == node
		if grammarEqualsNode:
			if foundPosAlready and verbose:
				print("two solutions")
			foundPosAlready = True
			retVal = pos
	return retVal

#This function takes two or three orderednodes and builds the rules from them,
# using the info from the orderednodes to help
def buildRulesFromOrderedNodes(musicXml, harmonyXml, nodes, grammarTree, singleLeftParent, singleRightParent, repFunc, verbose=False):
	key = getKeyFromMusicXml(musicXml)
	newString = ''
	# For singleRightParent With '7' as the new interval:
	# (5 (3 3) (2 2))   ->
	# (12 (7 7) (5 (3 3) (2 2)))
	treeIndexChange = None
	# For singleLeftParent With '7' as the new interval:
	# (5 (3 3) (2 2))   ->
	# (12 (5 (3 3) (2 2)) (7 7))
	if len(nodes) == 2 and (singleLeftParent or singleRightParent):
		parentNodeIndex = 1
		childNodeIndex = 0
		if singleLeftParent:
			parentNodeIndex = 0
			childNodeIndex = 1

		#difference = nodes[parentNodeIndex].note.pitch.ps - nodes[childNodeIndex].note.pitch.ps
		difference = repFunc(nodes[childNodeIndex].note, nodes[parentNodeIndex].note, nodes[childNodeIndex].getPitchRef(), nodes[parentNodeIndex].getPitchRef(), key, harmonyXml)
		bothUnvisited = nodes[childNodeIndex].visited is False and nodes[parentNodeIndex].visited is False
		# The case for the very first pair of notes needs to be handled.
		# In that case, both nodes will be unvisited
		if bothUnvisited is False:
			parentsInterval = str(nodes[parentNodeIndex].interval)
			totalInterval = repFunc(nodes[childNodeIndex].note, nodes[parentNodeIndex].note, nodes[childNodeIndex].getPitchRef(), nodes[parentNodeIndex].getPitchRef(), key, harmonyXml, parentsInterval, singleLeftParent)
			indexAfterDifferenceInString = -1
			if singleLeftParent:
				childTree = Tree(difference, [])
				newTree = Tree(totalInterval, [grammarTree, childTree])
				nodes[childNodeIndex].treeIndex = (1,)
				nodes[parentNodeIndex].treeIndex = (0,) + nodes[parentNodeIndex].treeIndex
				# We want the parent node to still point to its correct index within the original treeString
				treeIndexChange = getPositionOfNode(newTree, grammarTree)
				if verbose:
					print('treeIndexChange is ' + str(treeIndexChange))
			else:
				childTree = Tree(difference, [])
				newTree = Tree(totalInterval, [childTree, grammarTree])
				nodes[childNodeIndex].treeIndex = (0,)
				nodes[parentNodeIndex].treeIndex = (0,)
				treeIndexChange = getPositionOfNode(newTree, grammarTree)
				if verbose:
					print('treeIndexChange is ' + str(treeIndexChange))
			nodes[childNodeIndex].visited = True
		else:
			newTree = Tree(difference, [])
			nodes[0].visited = True
			nodes[1].visited = True
			nodes[0].treeIndex = ()
			nodes[1].treeIndex = ()
	else:
		interval1 = repFunc(nodes[0].note, nodes[1].note, nodes[0].getPitchRef(), nodes[1].getPitchRef(), key, harmonyXml)
		interval2 = repFunc(nodes[1].note, nodes[2].note, nodes[1].getPitchRef(), nodes[2].getPitchRef(), key, harmonyXml)

		newChild1 = Tree(interval1, [])
		newChild2 = Tree(interval2, [])

		newParent = Tree(interval1 + interval2, [newChild1, newChild2])
		newTree = grammarTree
		parentIndex = nodes[2].treeIndex
		if len(newTree[parentIndex]) > 0:
			print("ShitShit!!")
		if parentIndex != None:
			if verbose:
				print('parentIndex is ' + str(parentIndex))
				print(newTree.treepositions())
			newTree[parentIndex].append(newChild1)
			newTree[parentIndex].append(newChild2)
		else:
			newTree.append(newChild1)
			newTree.append(newChild2)
		nodes[1].visited = True
		nodes[1].treeIndex = parentIndex + (0, )
		nodes[2].treeIndex = parentIndex + (1, )
	return newTree, treeIndexChange

def convertNoteToStringRep(note):
	return str(note.pitch.ps)

def buildRulesFromOrderedNodesAtDepth(musicXml, harmonyXml, nodes, grammarTree, repFunc, verbose=False):
	productions = []
	numUnvisitedNodes = sum([int(o.visited is False) for o in nodes])

	while numUnvisitedNodes > 0:
		#find the unvisited node of minimum priority
		#build its grammar rules, and remove it.
		indexOfMinPriority = -1
		minPriority = MAX_NUM_NOTES_PER_SONG + 1
		for index, node in enumerate(nodes):
			if node.visited is False and node.priority < minPriority:
				minPriority = node.priority
				indexOfMinPriority = index

		curNoteList = []
		curNodeSubset = []

		#remove all unvisited nodes other than the one we just found
		visitedNodes = [n for n in nodes]
		numRemovedBeforeIndexOfMinPriority = 0

		for index, n in enumerate(reversed(visitedNodes)):
			nonReversedIndex = len(nodes) - index - 1
			if n.visited == True or nonReversedIndex == indexOfMinPriority:
				continue
			visitedNodes.remove(n)
			if nonReversedIndex < indexOfMinPriority:
				numRemovedBeforeIndexOfMinPriority += 1
		#the first case will have 2 unvisited nodes, and you want to keep them both
		nodesToCheck = [n for n in visitedNodes]
		if len(nodesToCheck) == 1:
			nodesToCheck = [n for n in nodes]
			numRemovedBeforeIndexOfMinPriority = 0

		numRemoved = numRemovedBeforeIndexOfMinPriority

		singleRightParent = indexOfMinPriority == 0
		singleLeftParent = indexOfMinPriority == len(nodes) - 1
		# another exception for the first case
		if numUnvisitedNodes == len(nodesToCheck):
			singleLeftParent = False
			singleRightParent = True
		if indexOfMinPriority != 0:
			curNoteList.append(nodesToCheck[indexOfMinPriority - numRemoved - 1].note)
			curNodeSubset.append(nodesToCheck[indexOfMinPriority - numRemoved - 1])
		curNoteList.append(nodesToCheck[indexOfMinPriority - numRemoved].note)
		curNodeSubset.append(nodesToCheck[indexOfMinPriority - numRemoved])
		if indexOfMinPriority != len(nodes) - 1:
			curNoteList.append(nodesToCheck[indexOfMinPriority - numRemoved + 1].note)
			curNodeSubset.append(nodesToCheck[indexOfMinPriority - numRemoved + 1])

		grammarTree, treeIndexChange = buildRulesFromOrderedNodes(musicXml, harmonyXml, curNodeSubset, grammarTree, singleLeftParent, singleRightParent, repFunc)
		if treeIndexChange != None:
			indicesToAvoid = [indexOfMinPriority]
			if indexOfMinPriority == 0:
				indicesToAvoid.append(indexOfMinPriority + 1)
			if indexOfMinPriority == len(nodes) - 1:
				indicesToAvoid.append(indexOfMinPriority - 1)
			for index, n in enumerate(nodes):
				if n.treeIndex != None and index not in indicesToAvoid:
					newTreeIndex = treeIndexChange + n.treeIndex
					#print(grammarTree[newTreeIndex])
					n.treeIndex = treeIndexChange + n.treeIndex
		numUnvisitedNodes = sum([int(o.visited is False) for o in nodes])

	return grammarTree


	"""notesNoTies1 = [n for n in notes.notes if n.tie is None or (n.tie.type == 'start')]
	notesNoTies2 = [n for n in deeperNotes.notes if n.tie is None or (n.tie.type == 'start')]
	for n1, n2 in pairwise(notesNoTies1):
		index1 = notesNoTies2.index(n1)
		index2 = notesNoTies2.index(n2)

		if index2 - index1 > 2:
			print("ruh roh")"""

def addTokensToLeafNodes(grammarTree):
	for leafVar in grammarTree.subtrees(lambda t: t.height() == 1):
		leafVar.append(leafVar._label)

def convertNegativeSignsToMsForNodeLabels(grammarTree):
	for node in grammarTree.subtrees(lambda t: t.height() >= 1):
		if '-' in node._label:
			node._label = node._label.replace('-', 'm')

#traverse breadthwise and add symbols, but only if they're on the very edges
def addStartAndEndSymbols(grammarTree, childQueue, checkStart, checkEnd):
	newChildQueue = []
	if checkStart and not isinstance(childQueue[0], str):
		if  'S' not in childQueue[0]._label:
			childQueue[0]._label = 'S' + childQueue[0]._label
		if len(childQueue[0]) > 0:
			if isinstance(childQueue[0][0], str):
				if 'S' not in childQueue[0][0]:
					childQueue[0][0] = 'S' + childQueue[0][0]
				checkStart = False
			else:
				newChildQueue.append(childQueue[0][0])
	if checkEnd and not isinstance(childQueue[-1], str):
		if 'E' not in childQueue[-1]._label:
			childQueue[-1]._label = childQueue[-1]._label + 'E'
		if len(childQueue[-1]) > 0:
			if isinstance(childQueue[-1][-1], str):
				if 'E' not in childQueue[-1][-1]:
					childQueue[-1][-1] = childQueue[-1][-1] + 'E'
				checkEnd = False
			else:
				newChildQueue.append(childQueue[-1][-1])
	if len(newChildQueue) > 0:
		addStartAndEndSymbols(grammarTree, newChildQueue, checkStart, checkEnd)



def buildGrammarTreeFromSolutionData(solutionXml, musicXml, harmonyXml, treeType, repFunc, verbose):
	root = solutionXml.getroot()
	rootName = treeType.lower()
	topXml = root.find(rootName)
	primaryXml = topXml.find('primary')
	secondaryXml = topXml.find('secondary')
	topON = OrderedNode(musicXml, topXml, -1, (), False, 0)
	topQueue = []
	tree = Tree('', [])
	childrenWereAdded = addChildNodesToQueue(musicXml, harmonyXml, topON, topQueue, treeType, repFunc)
	#hackzor for situations where the top nodes are not the first or last notes of the song
	"""if 'S' not in topQueue[1].interval:
		topQueue[1].interval = 'S' + topQueue[1].interval
	if 'E' not in topQueue[1].interval:
		topQueue[1].interval = topQueue[1].interval + 'E'"""

	for on in topQueue:
		on.visited = False
	if childrenWereAdded is False:
		topQueue.append(topON)
	treeNoTokens = buildTreeTopDownBreadthWise(topQueue, musicXml, harmonyXml, [], tree, treeType, repFunc, verbose)
	addTokensToLeafNodes(treeNoTokens)
	convertNegativeSignsToMsForNodeLabels(treeNoTokens)
	if repFunc == getKeyRelativePitchClassWithChordInfoAndStartEndSymbols or \
			repFunc == getKeyRelativePitchClassWithStartEndSymbols:
		addStartAndEndSymbols(treeNoTokens,[treeNoTokens], True, True)
	if verbose:
		print('final tree:' + str(treeNoTokens))
	#print(treeNoTokens)
	return treeNoTokens


def buildTreeTopDownBreadthWise(orderedNodeQueue, musicXml, harmonyXml, productionList, grammarTree, treeType, repFunc, verbose=False, useHarmony=False):
	curNoteList = []
	priorityList = []
	for o in orderedNodeQueue:
		curNoteList.append(o.note)
		priorityList.append(o.priority)
	curIntervals = []
	curPitchList = [n.pitch.ps for n in curNoteList]
	curVisitedList = [o.visited for o in orderedNodeQueue]
	for n1, n2 in pairwise(curNoteList):
		curIntervals.append(n2.pitch.ps - n1.pitch.ps)


	grammarTree = buildRulesFromOrderedNodesAtDepth(musicXml, harmonyXml, orderedNodeQueue, grammarTree, repFunc, verbose)
	if verbose:
		print('grammarTree is ' + str(grammarTree))

	childrenQueue = []
	childrenWereAddedThisDepth = False
	for orderedNode in orderedNodeQueue:
		curNote = orderedNode.note
		curNoteList.append(curNote)
		childrenWereAdded = addChildNodesToQueue(musicXml, harmonyXml, orderedNode, childrenQueue, treeType, repFunc)

		if childrenWereAdded is False:
			childrenQueue.append(orderedNode)
		childrenWereAddedThisDepth |= childrenWereAdded

	if verbose:
		print('curPriorityList = ' + str(priorityList))
		print('curPitchList = ' + str(curPitchList))
		print('curVisitedList = ' + str(curVisitedList))
		print('curIntervalList = ' + str(curIntervals))


	if childrenWereAddedThisDepth:
		grammarTree = buildTreeTopDownBreadthWise(childrenQueue, musicXml, harmonyXml, productionList, grammarTree, treeType, repFunc, verbose)
	return grammarTree


#def generateIntervalRepFromTreeDepths
def buildTreeFromIntervalsOfSolutionXml(rootXml, musicXml, productionList, treeType, useHarmony=False, verbose=False):
	depth = score_from_tree.get_total_depth_of_tree(rootXml, 0, treeType)
	print('depth is ' + str(depth))
	#musicXml.show()
	melodyOfPrevDepth = None
	melodyOfDepth = None
	for d in reversed(range(0, depth - 1)):
		if melodyOfDepth is not None:
			melodyOfPrevDepth = melodyOfDepth
		pitch_refs = score_from_tree.gather_note_refs_of_depth(rootXml, [], treeType, d, 0)
		pitch_refs.sort(key=pitchRefToNum)
		melodyOfDepth = score_from_tree.pitch_refs_to_notes(pitch_refs, musicXml)
		#if melodyOfPrevDepth is not None:
			#buildRulesFromNotesAtTwoConsecutiveDepths(melodyOfDepth, melodyOfPrevDepth)
		#melodyOfDepth.show()
		print (pitch_refs)


def getAllProductions(directory, solutionsDir, fileList, treeType, repFunc, verbose=False, useDesignedGrammar=False, harmonicGrammar=False, triadType="MAJOR"):
	noteLists = []
	intervalLists = []
	solutionTrees = []
	allProductions = []
	allTestSolutionsDict = {}
	numToSkipForTesting = 0
	for filepath in fileList:
		if numToSkipForTesting > 0:
			numToSkipForTesting -= 1
			continue
		print(filepath)
		if filepath in allTestSolutionsDict:
			continue

		if "MSC" in basename(filepath):
			filenumber = int(basename(filepath)[4:7])
			if filenumber >= 268:
				reductionFilename = treeType + basename(filepath)[3:7] + "_1" + basename(filepath)[7:]
			else:
				reductionFilename = treeType + basename(filepath)[3:]
		else:
			reductionFilename = treeType + "-" + basename(filepath)
		reductionFilepath = directory + '/' + treeType + '/' + reductionFilename
		solutionTree = ElementTree()
		solutionTree.parse(reductionFilepath)
		loadedMusicXml = converter.parse(filepath)

		#get harmony notations
		curPitchRefList = []
		harmonyXml = None
		if repFunc == getKeyRelativePitchClassWithChordInfoAndStartEndSymbols or \
			repFunc == getKeyRelativePitchClassWithChordInfoStartEndSymbolsAndMetricIntervals or \
				repFunc == getKeyRelativePitchClassWithChordInfo or \
				repFunc == getKeyRelativePitchClassWithChordInfoAndMetricInterval:
			harmonyFilename = "HM-" + basename(filepath)
			harmonyFilepath = directory + '/HM/' + harmonyFilename
			harmonyXml = ElementTree()
			harmonyXml.parse(harmonyFilepath)
			harmonyXml = harmonyXml.getroot()
		root = solutionTree.getroot()
		topXml = root.find(treeType.lower())
		curPitchRefList = getPitchRefListFromSolutionFile(topXml, treeType.lower())

		curNoteList = getNoteListFromFile(filepath)
		key = getKeyFromMusicXmlFilepath(filepath)
		noteLists.append(curNoteList)
		if len(curNoteList) != len(curPitchRefList):
			print('failure')
		intervalLists.append(getDataRepSequenceFromPitchLists(curNoteList, curPitchRefList, key, harmonyXml, repFunc))

		print(intervalLists[-1])

		print(reductionFilepath)

		if useDesignedGrammar:
			with open(musicGrammarFilename, 'r') as f:
				musicGrammarString = f.read()
			musicGrammar = CFG.fromstring(musicGrammarString)
			#for prTag in ET.iter("note"):
			#	print(prTag.attrib['id'])
			#	lookUpPitchReference(prTag.attrib['id'], loadedMusicFile, False)

			solutionTree = getGrammarParseFromSolutionXml(solutionTree, loadedMusicXml, musicGrammar, allProductions, treeType, verbose)
			solutionTrees.append(solutionTree)
			allProductions.append('(S (N) (N))')
		else:
			solutionTree = buildGrammarTreeFromSolutionData(solutionTree, loadedMusicXml, harmonyXml, treeType.lower(), repFunc, verbose)

			#TODO:need to add start and end tags here
			solutionTree = '(S ' + str(solutionTree) + ')'
			solutionTreeObj = Tree.fromstring(solutionTree)
			#print(solutionTree)
			#solutionTreeObj.draw()
			testForBug(solutionTreeObj, filepath)
			allProductions.append(solutionTree)

		#treeObj = Tree.fromstring(solutionTree)
		#treeObj.draw()
		#solutionTree1 = treeObj

		allTestSolutionsDict[filepath] = solutionTree
	return allTestSolutionsDict, allProductions

def testForBug(grammarTree, filename):
	stillHasBug = False
	for prod in grammarTree.productions():
		if len(prod.rhs()) > 2:
			#print(filename)
			print('production is ' + str(prod))#grammarTree.draw()
			stillHasBug = True
	if stillHasBug:
		print('this file still has the bug: ' + filename)
		print(grammarTree.productions())

def parseAllTestXmlsAndYield(fileList, grammar, allTestSolutionsDict, repFunc, existingParses, verbose=False, writeFilePath=None, displayTrees=False):
	testIntervalLists = []
	totalCorrect = 0
	totalCorrectNonN = 0
	totalProductions = 0
	totalLeaves = 0
	parseTreeStrings = {}
	for filepath in fileList:
		if filepath in existingParses:
			continue
		filenameLength = len(basename(filepath))
		harmonyFilename = "HM-" + basename(filepath)
		harmonyFilepath = filepath[:len(filepath) - filenameLength - 1] + '/HM/' + harmonyFilename
		harmonyXml = ElementTree()
		harmonyXml.parse(harmonyFilepath)
		harmonyXml = harmonyXml.getroot()

		curNoteList = getNoteListFromFile(filepath)
		curPitchRefList = getPitchRefListFromHarmonyFile(harmonyXml)

		#Get the solution tree
		try:
			solutionTreeStr = allTestSolutionsDict[filepath]
			solutionTree = Tree.fromstring(solutionTreeStr)
		except Exception as errorMsg:
			print("couldn't find solution for file " + filepath)
			print(errorMsg)
		#get the root node from the solution tree
		print(solutionTree.label())
		print(solutionTree[0].label())
		prodList = grammar.productions()
		startProdsToRemove = []
		for prod in prodList:
			#print(prod)
			#print(prod.lhs())
			if str(prod.lhs()) == 'S':
				if str(prod.rhs()) != solutionTree[0].label():
					startProdsToRemove.append(prod)

		"""
		#this was a test for specifying the correct start rule
		for prod in startProdsToRemove:
			prodList.remove(prod)
		newStartProd = ProbabilisticProduction(solutionTree.label(), [solutionTree[0].label()])
		prodList.append(newStartProd)
		S = Nonterminal('S')
		reducedGrammar = induce_pcfg(S, prodList)"""

		key = getKeyFromMusicXmlFilepath(filepath)
		testIntervalLists.append(getDataRepSequenceFromPitchLists(curNoteList, curPitchRefList, key, harmonyXml, repFunc))
		if verbose:
			print(testIntervalLists[-1])
		listLen = len(testIntervalLists[-1])
		if verbose:
			print(tree)
		parser = ViterbiParser(grammar)
		parses = None
		print('parsing this interval list: ' + str(testIntervalLists[-1]))
		if verbose:
			parser.trace(0)#3
		else:
			parser.trace(0)
		#parser.trace(3)
		try:
			parses = parser.parse_all(testIntervalLists[-1])
			#parses = parser.parse(testIntervalLists[-1])
		except Exception as errorMsg:
			print("error parsing file " + filepath)
			print(errorMsg)
		print('finished parsing')
		numTrees = 0
		if parses is not None:
			numTrees = sum(1 for _ in parses)
		if numTrees > 0 and displayTrees == True:
			from nltk.draw.tree import draw_trees
			draw_trees(*parses)
		if numTrees == 0:
			print("Couldn't find a valid parse, this is bad, very very bad")
			continue
		numCorrect = 0
		numCorrectNonN = 0
		bottomCorrect = 0
		bottomCorrectNonN = 0
		solutionTree = None

		if solutionTree != None and solutionTree != '':
			parseTreeStrings[filepath] = str(parses[0])
			curParseTreeString = str(parses[0])
			numCorrect, numCorrectNonN = validate_tree.compareTrees(solutionTree, parses[0])
			numProductions = len(solutionTree.productions())
			bottomCorrect, bottomCorrectNonN = validate_tree.compareTreesBottomUp(solutionTree, parses[0])
			yield numCorrect + bottomCorrect, numCorrectNonN, numProductions, len(solutionTree.leaves()), {filepath: curParseTreeString}

def parseAllTestXmlsMulticore(filepath, treeType, directory, grammar, repFunc, writeFilePath, parseTreeSharedDict, verbose=False, displayTrees=False):
	harmonyXml = ''
	if repFunc == getKeyRelativePitchClassWithChordInfoAndStartEndSymbols or \
		repFunc == getKeyRelativePitchClassWithChordInfoStartEndSymbolsAndMetricIntervals or \
			repFunc == getKeyRelativePitchClassWithChordInfo or \
			repFunc == getKeyRelativePitchClassWithChordInfoAndMetricInterval:
		#get the harmony notation info:
		harmonyFilename = "HM-" + basename(filepath)
		harmonyFilepath = directory + '/HM/' + harmonyFilename
		harmonyXml = ElementTree()
		harmonyXml.parse(harmonyFilepath)
		harmonyXml = harmonyXml.getroot()

	if "MSC" in basename(filepath):
		filenumber = int(basename(filepath)[4:7])
		if filenumber >= 268:
			reductionFilename = treeType + basename(filepath)[3:7] + "_1" + basename(filepath)[7:]
		else:
			reductionFilename = treeType + basename(filepath)[3:]
	else:
		reductionFilename = treeType + "-" + basename(filepath)
	reductionFilepath = directory + '/' + treeType + '/' + reductionFilename
	solutionTree = ElementTree()
	solutionTree.parse(reductionFilepath)
	root = solutionTree.getroot()
	topXml = root.find(treeType.lower())
	curPitchRefList = getPitchRefListFromSolutionFile(topXml, treeType.lower())

	if verbose:
		lock.acquire()
		print('running the multicore parse function')
		lock.release()

	testIntervalLists = []
	parseTreeStrings = {}

	#Gotta safely do the file loading by using a lock
	lock.acquire()
	print('getting pitchList from file: ' + filepath)
	curNoteList = getNoteListFromFile(filepath)
	lock.release()

	key = getKeyFromMusicXmlFilepath(filepath)
	testIntervalLists.append(getDataRepSequenceFromPitchLists(curNoteList, curPitchRefList, key, harmonyXml, repFunc))

	if len(testIntervalLists[-1]) > 75:
		return
	if verbose:
		print(testIntervalLists[-1])
	listLen = len(testIntervalLists[-1])
	if verbose:
		print(tree)
	parser = ViterbiParser(grammar)
	parses = None
	print('parsing this interval list: ' + str(testIntervalLists[-1]))
	if verbose:
		parser.trace(0)#3
	else:
		parser.trace(0)
	#parser.trace(3)
	try:
		parses = parser.parse_all(testIntervalLists[-1])
		#parses = parser.parse(testIntervalLists[-1])
	except Exception as errorMsg:
		print("error parsing file " + filepath)
		print(errorMsg)
	print('finished parsing')
	numTrees = 0
	if parses is not None:
		numTrees = sum(1 for _ in parses)
	if numTrees > 0 and displayTrees == True:
		from nltk.draw.tree import draw_trees
		draw_trees(*parses)
	if numTrees == 0:
		print("Couldn't find a valid parse, this is bad, very very bad")
		return

	lock.acquire()
	parseTreeSharedDict[filepath] = str(parses[0])
	parsesFile = open(writeFilePath, 'w')
	json.dump(parseTreeSharedDict.copy(), parsesFile)
	parsesFile.close()
	lock.release()




def parseAllTestXmlsMulticoreTestXmls(fileList, grammar, harmonyXml, allTestSolutionsDict, repFunc, verbose=False, writeFilePath=None, displayTrees=False):
	testNoteLists = []
	testIntervalLists = []
	totalCorrect = 0
	totalCorrectNonN = 0
	totalProductions = 0
	totalLeaves = 0
	existingParses = {}
	parseTreeStrings = {}
	for filepath in fileList:
		curNoteList = getNoteListFromFile(filepath)
		testNoteLists.append(curNoteList)
		curPitchRefList = getPitchRefListFromHarmonyFile(harmonyXml)
		testNoteLists.append(curNoteList)

		key = getKeyFromMusicXmlFilepath(filepath)
		testIntervalLists.append(getDataRepSequenceFromPitchLists(curNoteList, curPitchRefList, key, harmonyXml, repFunc))
		if verbose:
			print(testIntervalLists[-1])
		listLen = len(testIntervalLists[-1])
		if verbose:
			print(tree)
		parser = ViterbiParser(grammar)
		parses = None
		print('parsing this interval list: ' + str(testIntervalLists[-1]))
		if verbose:
			parser.trace(0)#3
		else:
			parser.trace(0)
		#parser.trace(3)
		try:
			parses = parser.parse_all(testIntervalLists[-1])
			#parses = parser.parse(testIntervalLists[-1])
		except Exception as errorMsg:
			print("error parsing file " + filepath)
			print(errorMsg)
		print('finished parsing')
		numTrees = 0
		if parses is not None:
			numTrees = sum(1 for _ in parses)
		if numTrees > 0 and displayTrees == True:
			from nltk.draw.tree import draw_trees
			draw_trees(*parses)
		if numTrees == 0:
			print("Couldn't find a valid parse, this is bad, very very bad")
			continue
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

#For the case where your note is out of key
def getClosestScaleDegree(outOfKeyNote, scale):
	if len(outOfKeyNote.name) > 1:
		truncatedNoteName = outOfKeyNote.name[:-1]
		noteWithoutAccidentals = note.Note(truncatedNoteName)
	else:
		for name in [str(p) for p in scale.getPitches('c3', 'c4')]:
			if name[:1] == outOfKeyNote.name[:1]:
				return getScaleDegreeFromPitchName(name, scale)
	return getScaleDegreeFromMusic21Note(noteWithoutAccidentals, scale)

def getScaleDegreeFromMusic21Note(m21Note, scale):
	curPitchObj = m21Note.pitches[0]
	enharms = curPitchObj.getAllCommonEnharmonics()

	pitchDegree = scale.getScaleDegreeFromPitch(m21Note.name, direction='descending')
	if pitchDegree is None:
		for enharm in enharms:
			#print(str(enharm))
			pitchDegree = scale.getScaleDegreeFromPitch(str(enharm))
			if pitchDegree is not None:
				break
	return pitchDegree

def getScaleDegreeFromPitchNum(pitchNum, scale):
	curNote = note.Note(pitchNum)
	return getScaleDegreeFromMusic21Note(curNote, scale)

def getScaleDegreeFromPitchName(pitchName, scale):
	curNote = note.Note(pitchName)
	return getScaleDegreeFromMusic21Note(curNote, scale)

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
	scaleRootPitchClass = root.pitch.ps % 12
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
