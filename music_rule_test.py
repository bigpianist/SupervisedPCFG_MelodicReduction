import multiprocessing
import operator
import validate_tree
import music_grammar
import glob
import itertools
from nltk import *
from music21 import *
import copy
import argparse
from xml.etree.ElementTree import *
from os.path import basename
from nltk.tree import *
import os.path
from nltk.parse import ViterbiParser
import json
from functools import partial
from nltk.parse import BottomUpProbabilisticChartParser
from nltk.draw.tree import draw_trees
from nltk.parse import pchart
import sys, time
from nltk import tokenize

from functools import reduce
from nltk.tree import Tree, ProbabilisticTree
from nltk.grammar import Nonterminal, PCFG
import random
import score_from_tree
from nltk.parse.api import ParserI
from nltk.parse.chart import Chart, LeafEdge, TreeEdge, AbstractChartRule
#from nltk.compat import python_2_unicode_compatible


from nltk.draw import tree

dataRepresentationFunction = music_grammar.getKeyRelativePitchClassWithMetricInterval


def generateFoldIndices(numFolds, numFiles):
	random.seed(3)
	foldSize = int(numFiles / numFolds)
	foldIndices = []
	allIndices = []
	for f in range(numFolds):
		curFoldIndices = []
		for i in range(foldSize):
			newInt = random.randint(0, numFiles - 1)
			while newInt in allIndices and newInt < numFiles:
				newInt += 1
			if newInt == numFiles:
				while newInt in allIndices and newInt >= 0:
					newInt -= 1
			curFoldIndices.append(newInt)
			allIndices.append(newInt)
		foldIndices.append(curFoldIndices)
	return foldIndices

def crossVal(args, useFile=True):
	fileList = [file for file in glob.glob(os.path.join(args.directory, '*.xml'))]
	if args.folds != None:
		numFolds = int(args.folds)
		numFiles = len(fileList)
		foldIndices = generateFoldIndices(numFolds,numFiles - 1)

		for i in foldIndices[0]:
			for f in foldIndices[1:-1]:
				for j in f:
					if i == j:
						return

		resultsFile = 'Results_' +args.type + '.txt'

		results = open(resultsFile, 'w')

		for testFold in range(numFolds):
			print('training fold ' + str(testFold))
			trainingSet = []
			for index, fold in enumerate(foldIndices):
				if index != testFold:
					for i in fold:
						trainingSet.append(fileList[i])

			testSet = [fileList[j] for j in foldIndices[testFold]]

			foldFile = 'fold' + str(testFold) + '_' + args.type + '_trainingTrees.txt'
			solutionTreeDict = {}
			allProductions = []
			fileSucceeded = False
			if useFile:
				try:
					f = open(foldFile, 'r')
					solutionTreeDict = json.load(f)
					fileSucceeded = True
					allProductions = [solutionTreeDict[key] for index, key in enumerate(solutionTreeDict)]
				except:
					print('file ' + foldFile + ' did not exist')
			if not fileSucceeded:
				solutionTreeDict, allProductions = music_grammar.getAllProductions(args.directory, args.type, trainingSet, args.type, dataRepresentationFunction, args.verbose)
				f = open(foldFile, 'w')
				json.dump(solutionTreeDict, f)
				f.close()
			foldTestFile = 'fold' + str(testFold) + '_' + args.type + '_testSetFilenames.txt'
			f2 = open(foldTestFile, 'w')
			for filename in testSet:
				f2.write(filename + '\n')
			f2.close()
			S = Nonterminal('S')
			smallTrees = music_grammar.collectProductions(allProductions, args.verbose)
			trainedGrammar = induce_pcfg(S, smallTrees)

			print('trainedGrammar is ' + str(trainedGrammar))


			print('length of the trainingset is: ' + str(len(trainingSet)))
			print('length of the testset is: ' + str(len(testSet)))

			print("starting to get solutions for the test set ")
			testProductions = []

			foldTestSolutionsFile = 'fold' + str(testFold) + '_' + args.type + '_testSolutions.txt'
			fileSucceeded = False
			solutionTreeDictForTestSet = {}
			if useFile:
				try:
					fTest = open(foldTestSolutionsFile, 'r')
					solutionTreeDictForTestSet = json.load(fTest)
					fileSucceeded = True
				except:
					print('file ' + foldTestSolutionsFile + ' did not exist')
			if not fileSucceeded:
				solutionTreeDictForTestSet, testProductions = music_grammar.getAllProductions(args.directory, args.type, testSet, args.type, dataRepresentationFunction, args.verbose)
				foldTestSolutionsFile = 'fold' + str(testFold) + '_' + args.type + '_testSolutions.txt'
				f3 = open(foldTestSolutionsFile, 'w')
				json.dump(solutionTreeDictForTestSet,f3)

			#save the parses to disk
			foldParsesFilePath = 'fold' + str(testFold) + '_' + args.type + '_parsedTestSet.txt'
			parsesDict = {}
			if os.path.exists(foldParsesFilePath):
				foldParsesFile = open(foldParsesFilePath, 'r')
				parsesDict = json.load(foldParsesFile)

			"""
			#single-core, generator version
			parsesDict = {}
			parseGenerator = music_grammar.parseAllTestXmlsAndYield(testSet, trainedGrammar, solutionTreeDictForTestSet, music_grammar.getKeyRelativePitchClassAndAppendChordInfo, parsesDict, args.verbose, False)#"./MusicXml/Test"
			print("parsing the test set")
			try:
				totalCorrect = 0
				totalCorrectNonN = 0
				totalProductions = 0
				totalLeaves = 0
				while True:
					numCorrect, numCorrectNonN, numProductions, numLeaves, parseTreeStringDict = next(parseGenerator)
					totalCorrect += numCorrect
					totalCorrectNonN += numCorrectNonN
					totalProductions += numProductions
					totalLeaves += numLeaves
					foldParsesFile = open(foldParsesFilePath, 'w')
					parsesDict.update(parseTreeStringDict)
					json.dump(parsesDict, foldParsesFile)
					foldParsesFile.close()
			except Exception as errorMsg:
				print('reached end of generator')
				print(errorMsg)

			"""

			multiManager = multiprocessing.Manager()
			l = multiprocessing.Lock()
			parsedTrees = multiManager.dict(parsesDict)

			#totalCorrect, totalCorrectNonN, totalProductions, totalLeaves, parseTreeStrings = music_grammar.parseAllTestXmls(testSet, trainedGrammar, solutionTreeDictForTestSet, music_grammar.getPitchClassIntervalFromTwoNotes, parsedTrees, args.verbose, False)#"./MusicXml/Test"

			newTestSet = [filename for filename in testSet if filename not in parsesDict.keys()]
			print(newTestSet)
			parsePool = multiprocessing.Pool(initializer=music_grammar.initLock, initargs=(l,), processes=6)
			#paramList = zip(testSet, itertools.repeat(trainedGrammar), itertools.repeat(music_grammar.getPitchClassIntervalFromTwoNotes), itertools.repeat(foldParsesFilePath), itertools.repeat(lock), itertools.repeat(parsedTrees))

			parsePool.map(partial(music_grammar.parseAllTestXmlsMulticore, treeType=args.type, directory=args.directory, grammar=trainedGrammar, repFunc=dataRepresentationFunction, writeFilePath=foldParsesFilePath, parseTreeSharedDict=parsedTrees), newTestSet)


def removeProbability(treeString):
	probabilisticPart = re.findall('(\(p=[^()]*\))', treeString)
	indexOfProbPart = treeString.index(probabilisticPart[0])
	return treeString[:indexOfProbPart]

def printReductionComparisonResults(reductionsByFile):
	for filename, reductionsByDepth in reductionsByFile.items():
		for depthIndex, [numAccurate, numSpurious, numMissing] in reductionsByDepth.items():
			print(numAccurate)
			print(numSpurious)
			print(numMissing)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("directory", help="Directory that contains melody files")
	parser.add_argument("-g", "--grammar", help="The file that specifies a saved grammar, this grammar will be used instead of training a new one")
	parser.add_argument("-gd", "--grammar-directory", help="The directory containing the grammar files")
	parser.add_argument("-f", "--folds", help="number of folds desired")
	parser.add_argument("-o", "--outfile", help="The file that the grammar will be saved in")
	parser.add_argument("-t", "--type", help="The type of solutions file we're using, either 'PR' or 'TS' for Prolongational Reduction or Time-span Tree, respectively")
	parser.add_argument("-v", "--verbose", help="increase output verbosity")
	parser.add_argument("-s", "--stats", help="Just run the statistics on existing files")
	args = parser.parse_args()
	print(args)

	gramTree = Tree('3', [])
	childTree = Tree('5', [])
	gramTree.append(childTree)
	#print(gramTree)
	#print(gramTree.treepositions())
	childTree.append('6')
	#print(gramTree)
	#print(gramTree.treepositions())



	if args.verbose == None or args.verbose == 'False':
		args.verbose = False
	elif args.verbose == 'True':
		args.verbose = True


	if args.stats == None or args.stats == 'False':
		args.stats = False
	elif args.stats == 'True':
		args.stats = True

	#If the grammar is specified, then the "directory" folder will be used as a test set
	#If the grammar is not specified, it will use 20% of the files in "directory" as a test set, and the rest as a training set to create the grammar
	#If folds are specified, then it will split the files in "directory" into numFolds groups, applying training and testing, and then adding up the percentages overall
	allProductions = []
	stats = True
	if args.grammar != None and args.grammar != '':
		#Load the grammar's training trees, and induce it from the productions of each tree
		if not os.path.isfile(args.grammar):
			return
		f = open(args.grammar, 'r')
		trainingTrees = json.load(f)

		"""displays the grammar productions
		for filename, trainingTree in trainingTrees.items():
			allProductions.append(trainingTree)
		S = Nonterminal('S')
		smallTrees = music_grammar.collectProductions(allProductions, args.verbose)
		trainedGrammar = induce_pcfg(S, smallTrees)
		print(trainedGrammar)
		"""

		"""#Used this code for generating specific figures:
		exampleTree = Tree.fromstring('(S (N (N (5 5)) (N (m4 -4))) (N (6 6)))')
		#exampleTree.draw()
		exampleTreeToCompare = Tree.fromstring('(S (N (5 5)) (N (N (m4 -4)) (N (6 6))))')
		#exampleTreeToCompare.draw()
		validate_tree.compareTreesBottomUp(exampleTree, exampleTreeToCompare)
		#exampleTreeToCompare.draw()"""

		"""This code will generate right-hand side values for the production rule specified, and then embellish it
		np_productions = trainedGrammar.productions(Nonterminal('4'))
		dict = {}
		for pr in np_productions: dict[pr.rhs()] = pr.prob()
		np_probDist = DictionaryProbDist(dict)

		for i in range(100):
			rightHand = np_probDist.generate()
			print(rightHand)
			print(len(rightHand))

		generatedTree = pcfg_generate.generate(trainedGrammar)
		print('resulting tree: ')
		generatedTreeObj = Tree.fromstring(generatedTree)
		print(generatedTreeObj)
		print(str(generatedTreeObj.leaves()))
		print('\n\n')
		embellishedTree = pcfg_generate.expandAllLeaves(trainedGrammar, generatedTreeObj)
		print(embellishedTree)

		print(str(Tree.fromstring(str(embellishedTree)).leaves()))
		"""

		"""This code will open the hand-made grammar and parse the example in fileToTest
		fileToTest = "./MusicXml/72_Preludes 1 La fille aux cheveux de lin.xml"
		musicXmlTest = converter.parse(fileToTest)

		curPitchList = music_grammar.getNoteListFromFile(fileToTest)

		intervalList = music_grammar.getIntervalStringsFromPitchList(curPitchList)

		print('num intervals is: ' + str(len(intervalList)))



		with open(music_grammar.musicGrammarFilename, 'r') as f:
			musicGrammarString = f.read()
		musicGrammar = CFG.fromstring(musicGrammarString)
		parser = ChartParser(musicGrammar, trace=2)
		#parses = parser.parse(intervalList)

		#numTrees = sum(1 for _ in parses)
		#print('numTrees is: ' + str(numTrees))
		#return
		"""
		#this is for the musical examples

		fileToTest = "./MusicXml/50_Amazing Grace.xml"

		harmonyFilename = "HM-" + basename(fileToTest)
		harmonyFilepath = args.directory + '/HM/' + harmonyFilename
		harmonyXml = ElementTree()
		harmonyXml.parse(harmonyFilepath)
		harmonyXml = harmonyXml.getroot()
		musicXmlTest = converter.parse(fileToTest)
		curNoteList = music_grammar.getNoteListFromFile(fileToTest)
		curPitchRefList = music_grammar.getPitchRefListFromHarmonyFile(harmonyXml)

		"""key = music_grammar.getKeyFromMusicXmlFilepath(fileToTest)
		intervalList = music_grammar.getDataRepSequenceFromPitchLists(curNoteList, curPitchRefList, key, harmonyXml, dataRepresentationFunction)
		print(intervalList)"""
		bestParseString = '(S\
  (c3c\
    (c4c\
      (c0c\
        (c0c\
          (c4c (c2c c2c) (c2c (c1 c1) (1c 1c)))\
          (cm4c c-4c))\
        (c0c\
          (c5c (c3c c3c) (c2c (c1 c1) (1c 1c)))\
          (cm5c c-5c)))\
      (c4c c4c))\
    (cm1c\
      (c3 (c3c (c1 c1) (2c (1c 1c) (c1c c1c))) (c0 c0))\
      (m4c\
        (m2\
          (0 (0 0) (0 (0 0) (0 (1c 1c) (cm1 c-1))))\
          (m2\
            (m1c (m1 -1) (0c 0c))\
            (cm1\
              (c0c\
                (c0c (c1c c1c) (cm1c c-1c))\
                (c0c (cm1 (cm1 c-1) (0 0)) (1c 1c)))\
              (cm1 c-1))))\
        (m2c (m1c -1c) (cm1c c-1c))))))'
		#trainedParser = ViterbiParser(trainedGrammar)
		#parses = trainedParser.parse_all(intervalList)
		#bestParse = parses[0]
		bestParseString = removeProbability(trainingTrees[fileToTest])
		bestParse = Tree.fromstring(bestParseString)
		print(bestParse)
		#bestParse.draw()
		treeType = bestParse.convert(ParentedTree)
		parse_depth = 0
		depth = score_from_tree.get_total_depth_of_tree_obj(bestParse, parse_depth)
		print('depth is : ' + str(depth))
		print('builtin height is : ' + str(bestParse.height()))
		print(bestParse)
		#bestParse.draw()
		#score_from_tree.get_tree_obj_to_negative_depth(bestParse, 2, parse_depth)
		score_from_tree.print_reductions_for_parse_tree(bestParse, musicXmlTest,['S'])
		#prunedBestParse, removedLeaves, leafIndex= score_from_tree.remove_embellishment_rules_from_tree_below_depth(bestParse, {}, depth - 2, 0, 0)
		prunedBestParse, removedLeaves, leafIndex, maxSubtreeDepth = score_from_tree.remove_embellishment_rules_from_tree_negative_depth(bestParse, {}, 3, 0, 0)

		print(prunedBestParse)
		#for s in parentedBestParse.subtrees(lambda t: t.height() > parse_depth - 3):
			#treepos = parentedBestParse.treeposition(s)
			#parentedBestParse.remove(treepos)
		prunedBestParse.draw()
		score_from_tree.get_melody_from_parse_tree(bestParse, removedLeaves, musicXmlTest)

		PR_fileToTest = "./MusicXml/PR/PR-39_Andante C dur.xml"
		ET = ElementTree()
		ET.parse(PR_fileToTest)
		root = ET.getroot()
		rootName = args.type.lower()
		topXml = root.find(rootName)
		depth = 0
		depth = score_from_tree.get_total_depth_of_tree(topXml, depth, rootName)
		print('depth is ' + str(depth))
		musicXmlTest.show()
		for d in reversed(range(0, depth - 1)):
			pitch_refs = score_from_tree.gather_note_refs_of_depth(topXml, [], rootName, d, 0)
			pitch_refs.sort(key=music_grammar.pitchRefToNum)
			melody_of_depth = score_from_tree.pitch_refs_to_notes(pitch_refs, musicXmlTest)
			melody_of_depth.show()
			print (pitch_refs)


		#examples with 3-child nodes
		#, './MusicXml/MSC-166.xml', './MusicXml/MSC-103.xml', './MusicXml/37_Sonate fur Klavier Nr.48 C dur Op.30-1 Mov.1.xml', './MusicXml/MSC-211.xml'
		#wrong buti like it , './MusicXml/MSC-238.xml'
		#like: ./MusicXml/MSC-141.xml fold 2,
		#filesToTest = ['./MusicXml/MSC-238.xml', './MusicXml/39_Andante C dur.xml']#fold 1
		#filesToTest = ['./MusicXml/MSC-224.xml', './MusicXml/MSC-141.xml']# fold 2
		#filesToTest = ["./MusicXml/03_Bagatelle 'Fur Elise' WoO.59.xml"]#fold 3
		#filesToTest = ['./MusicXml/MSC-111.xml'] #['./MusicXml/MSC-108.xml', './MusicXml/01_Waltz in E flat Grande Valse Brillante Op.18.xml', './MusicXml/MSC-231.xml', './MusicXml/37_Sonate fur Klavier Nr.48 C dur Op.30-1 Mov.1.xml', './MusicXml/59_Schwanengesang No.1 Op.72-4 D.957-4 Standchen.xml']#fold4
		#filesToTest = ['./MusicXml/MSC-111.xml', './MusicXml/MSC-108.xml', './MusicXml/01_Waltz in E flat Grande Valse Brillante Op.18.xml', './MusicXml/MSC-231.xml', './MusicXml/59_Schwanengesang No.1 Op.72-4 D.957-4 Standchen.xml']

		#PR
		#filesToTest = ['./MusicXml/80_Symphonie Nr.40 g moll KV.550 1.Satz.xml', './MusicXml/31_Sinfonie Nr.9 d moll Op.125 4.Satz An die Freude.xml']# fold 0 PR
		#filesToTest = ['./MusicXml/34_Water Music in D major HWV 349 No.11 Alla Hornpipe.xml', './MusicXml/02_Moments Musicaux.xml']#fold 0 20%
		#filesToTest = ['./MusicXml/84_Toccata und Fuge d moll BWV565.xml'] #fold 1
		#filesToTest = ['./MusicXml/33_Swan Lake Op.20 No.9 Finale.xml', './MusicXml/40_Alpengluhen Op.193.xml']# fold 3 Pr
		#filesToTest =  ['./MusicXml/57_Waves of the Danube.xml']#, './MusicXml/60_Ma Vlast Moldau.xml']# fold 3 PR < 20%

		filesToTest = ['./MusicXml/02_Moments Musicaux.xml']#fold 4 ts
		totalCorrect, totalCorrectNonN, totalProductions, totalLeaves, parseTreeStrings = music_grammar.parseAllTestXmls(filesToTest, trainedGrammar, solutionTreeDictForTestSet, args.verbose, False)
		solutionTreeDictForTestSet, testProductions = music_grammar.getAllProductions(args.directory, args.type, filesToTest, args.type, args.verbose)

		parseFilename = "fold4_" + args.type + "_parsedTestSet.txt"
		parseFile = open(parseFilename, 'r')
		parses = json.load(parseFile)

		for filename, solutionTree in parseTreeStrings.items():
			if "_afterComparison" in filename:
				continue
			treeSolution = solutionTreeDictForTestSet[filename]
			percentageCorrect = -1
			print(filename)
			treeSolutionObj = Tree.fromstring(treeSolution)
			treeSolutionObj.draw()
			parseTreeNoProbabilities = removeProbability(str(parseTreeStrings[filename]))
			parseTreeObj = Tree.fromstring(parseTreeNoProbabilities)
			parseTreeObj.draw()
			parseAfterCompNoProbabilities = removeProbability(str(parseTreeStrings[filename+'_afterComparison']))
			parseAfterCompObj = Tree.fromstring(parseAfterCompNoProbabilities)
			parseAfterCompObj.draw()
		percentageCorrectNonN = -1
		percentageLeaves = -1
		if totalProductions > 0:
			percentageCorrect = totalCorrect / totalProductions
			percentageCorrectNonN = totalCorrectNonN / totalProductions
			percentageLeaves = totalLeaves / totalProductions
		print("results:\ntotalCorrect: " + str(totalCorrect) + "\npercentageCorrect: " + str(percentageCorrect) + "\ntotalCorrectNonN: " + str(totalCorrectNonN) + "\npercentageCorrectNonN: " + str(percentageCorrectNonN) + "\ntotalProductions: " + str(totalProductions) + "\ntotalLeaves: " + str(totalLeaves) + "\npercentageLeavess: " + str(percentageLeaves) + "\n")
		#finish this case
		return
	if True:
		"""solutionsFilename = "fold0_" + args.type + "_testSolutions.txt"
		solutionsFile = open(solutionsFilename, 'r')
		solutions = json.load(solutionsFile)
		for filename, sol in solutions.items():
			solTree = Tree.fromstring(sol)

			for prod in solTree.productions():
				if len(prod.rhs()) > 2:
					print(filename)
					print(prod)
		"""
		amazingGraceFilename = './MusicXml/50_Amazing Grace.xml'
		for i in range(5):

			with open('./Feb19SavePR/fold' + str(i) + '_PR_parsedTestSet.txt', 'r') as inFile:
				treeDict = json.load(inFile)
				if amazingGraceFilename not in treeDict.keys():
					continue
				amazingString = removeProbability(treeDict[amazingGraceFilename])
				amazingString = re.sub('[c]', '', amazingString)
				tree = Tree.fromstring(amazingString)
				tree.draw()
		problemFiles = ['./MusicXml/50_Amazing Grace.xml','./MusicXml/33_Swan Lake Op.20 No.9 Finale.xml','./MusicXml/08_Spinnerlied Op.14 No.4.xml', './MusicXml/66_The Nutcracker Suite Op.71a No.2 March.xml','./MusicXml/81_Symphony No.9 in E minor Op.95 B.178 From the New World Mov.2 Goin\' Home.xml', './MusicXml/18_Thais Meditation.xml', './MusicXml/01_Waltz in E flat Grande Valse Brillante Op.18.xml']

		for filename in problemFiles:
			print(filename)
			harmonyFilename = "HM-" + basename(filename)
			harmonyFilepath = args.directory + '/HM/' + harmonyFilename
			harmonyXml = ElementTree()
			harmonyXml.parse(harmonyFilepath)
			#pitchRefs = ["P1-1-1", "P1-2-2", "P1-3-3", "P1-4-2"]
			#for pitchRef in pitchRefs:
			#	print('chord for pitch "' + pitchRef + '" is: ' + music_grammar.getChordStringFromPitchRefAndNotation(pitchRef, harmonyXml.getroot()))

			solutionFilename = args.type + "-" + basename(filename)
			solutionFilepath = args.directory + '/' + args.type + '/' + solutionFilename

			#	solutionFilename = args.type + "-" + basename(filename)[4:]
			#	solutionFilepath = args.directory + '/' + args.type + '/' + solutionFilename[:-4] + '_1' + solutionFilename[-4:]

			ET = ElementTree()
			ET.parse(solutionFilepath)
			root = ET.getroot()
			rootName = args.type.lower()
			topXml = root.find(rootName)
			curMusicXml  = converter.parse(filename)
			#topXml.show()
			#parseTreeObj.draw()
			#score_from_tree.print_reductions_for_parse_tree(parseTreeObj, curMusicXml)
			depth = 0
			prodList = []

			grammarTree = music_grammar.buildGrammarTreeFromSolutionData(ET, curMusicXml, harmonyXml.getroot(), rootName, music_grammar.getPitchClassIntervalFromTwoNotes, True)
			#print(solutionFilepath)
			grammarTree.draw()
			stillHasBug = False
			for prod in grammarTree.productions():
				if len(prod.rhs()) > 2:
					print(filename)
					print(prod)#grammarTree.draw()
					stillHasBug = True
			if stillHasBug:
				print('this file still has the bug: ' + filename)
			else:
				print('this file no longer has the bug: ' + filename)

			continue
			depth = score_from_tree.get_total_depth_of_tree(ET, depth, rootName)
			print('depth is ' + str(depth))
			curMusicXml.show()
			for d in reversed(range(0, depth - 1)):
				pitch_refs = score_from_tree.gather_note_refs_of_depth(topXml, [], rootName, d, 0)
				pitch_refs.sort(key=music_grammar.pitchRefToNum)
				melody_of_depth = score_from_tree.pitch_refs_to_notes(pitch_refs, curMusicXml)
				melody_of_depth.show()
				print (pitch_refs)
			break
		return

	if args.stats == True:
		totalCorrect = 0
		totalCorrectNonN = 0
		totalProductions = 0
		totalLeaves = 0
		#./MusicXml/MSC-103.xml, ./MusicXml/24_Orphee aux Enfers Overture.xml, ./MusicXml/MSC-211.xml, ./MusicXml/39_Andante C dur.xml,./MusicXml/01_Waltz in E flat Grande Valse Brillante Op.18.xml
		#small ones
		#./MusicXml/MSC-224.xml
		#pretty good one:  ['./MusicXml/57_Waves of the Danube.xml', './MusicXml/MSC-107.xml','./MusicXml/59_Schwanengesang No.1 Op.72-4 D.957-4 Standchen.xml', './MusicXml/MSC-231.xml']
		goodOnesTS = ['./MusicXml/57_Waves of the Danube.xml', './MusicXml/MSC-107.xml','./MusicXml/59_Schwanengesang No.1 Op.72-4 D.957-4 Standchen.xml', './MusicXml/MSC-231.xml']
		goodOnesPR = ['./MusicXml/02_Moments Musicaux.xml',"./MusicXml/95_12 Variationen uber ein franzosisches Lied 'Ah,vous dirai-je, maman' C dur K.265 K6.300e.xml"]

		#music_grammar.getAllProductionsHarmonicGrammar(args.directory, args.type, [goodOnesPR[0]], args.type, "MINOR", args.verbose)
		#if stats == True:
		#	return
		num_skip = 0
		for fold in range(int(args.folds)):
			bestSolutionFiles = []
			worstSolutionFile = ""
			bestPercentage = .6
			worstPercentage = .3
			#get parses from file
			grammarDir = ""
			if args.grammar_directory is not None:
				grammarDir = args.grammar_directory + '/'
			parseFilename = grammarDir + "fold" + str(fold) + "_" + args.type + "_parsedTestSet.txt"
			parseFile = open(parseFilename, 'r')
			parses = json.load(parseFile)
			#get solutions from file
			solutionsFilename = grammarDir + "fold" + str(fold) + "_" + args.type + "_testSolutions.txt"
			solutionsFile = open(solutionsFilename, 'r')
			solutions = json.load(solutionsFile)

			foldLeaves = 0
			foldProductions = 0
			foldCorrect = 0
			foldCorrectNonN = 0
			foldFilesSkipped = 0
			numToSkipForTesting = 2
			foldReductionsAnalysis = {}
			for filename, solutionTree in sorted(solutions.items()):
				if numToSkipForTesting > 0:
					numToSkipForTesting -= 1
					continue
				#print(filename)
				solutionTreeObj = Tree.fromstring(solutionTree)
				if filename not in parses:
					foldFilesSkipped += 1
					continue
				parseStr = parses[filename]
				probabilisticPart = re.findall('(\(p=[^()]*\))', parseStr)
				indexOfProbPart = parseStr.index(probabilisticPart[0])
				parseTreeObj = Tree.fromstring(parseStr[:indexOfProbPart])

				#here's where we look at example reductions in musical scores
				curMusicXml = converter.parse(filename)

				#solutionTreeObj.draw()
				#parseTreeObj.draw()
				parseTreeObjAfterComparison = copy.deepcopy(parseTreeObj)
				numProductions = len(solutionTreeObj.productions())
				foldProductions += numProductions
				bottomCorrect, bottomCorrectNonN = validate_tree.compareTreesBottomUp(solutionTreeObj, parseTreeObjAfterComparison)
				topCorrect, topCorrectNonN = validate_tree.compareTrees(solutionTreeObj, parseTreeObjAfterComparison)
				#parseTreeObjAfterComparison.draw()
				#adding this for testing
				bottomCorrect += topCorrect
				bottomCorrectNonN += topCorrectNonN
				print(bottomCorrect / numProductions)
				if bottomCorrect / numProductions > .46 and bottomCorrect / numProductions < .49:
					print("this file is more than 46% correct")
					print(filename)

				if "MSC" in basename(filename):
					filenumber = int(basename(filename)[4:7])
					if filenumber >= 268:
						reductionFilename = args.type + basename(filename)[3:7] + "_1" + basename(filename)[7:]
					else:
						reductionFilename = args.type + basename(filename)[3:]
				else:
					reductionFilename = args.type + "-" + basename(filename)
				solutionFilepath = args.directory + '/' + args.type + '/' + reductionFilename

				ET = ElementTree()
				ET.parse(solutionFilepath)
				root = ET.getroot()
				rootName = args.type.lower()
				solutionXml = root.find(rootName)
				#reductionsByDepth = validate_tree.compareTreesByReductions(parseTreeObjAfterComparison, curMusicXml, solutionXml, args.type.lower(), ['S'])

				#foldReductionsAnalysis[filename] = reductionsByDepth
				if bottomCorrect / numProductions > bestPercentage:# and bottomCorrect / numProductions < bestPercentage:
					bestSolutionFiles.append(filename)
					if filename in goodOnesPR and False:
						print(filename)
						print(parseTreeObj.leaves())
						#solutionTreeObj.draw()
						#parseTreeObj.draw()
						#parseTreeObjAfterComparison.draw()
					#bestPercentage = bottomCorrect / numProductions

				#if bottomCorrect / numProductions < worstPercentage:
				#	worstSolutionFile = filename
				#	worstPercentage = bottomCorrect / numProductions
				foldLeaves = len(solutionTreeObj.leaves())

				foldCorrect += bottomCorrect
				foldCorrectNonN += bottomCorrectNonN
			printReductionComparisonResults(foldReductionsAnalysis)
			totalProductions += foldProductions
			totalLeaves += foldLeaves
			totalCorrect += foldCorrect
			totalCorrectNonN += foldCorrectNonN
			foldPercentageCorrect = -1
			foldPercentageCorrectNonN = -1
			foldPercentageLeaves = -1
			if foldProductions > 0:
				foldPercentageCorrect = foldCorrect / foldProductions
				foldPercentageCorrectNonN = foldCorrectNonN / foldProductions
				foldPercentageLeaves = foldLeaves / foldProductions
			print("Fold number " + str(fold) + " results:\nfoldCorrect: " + str(foldCorrect) + "\nfoldPercentageCorrect: " + str(foldPercentageCorrect) + "\nfoldCorrectNonN: " + str(foldCorrectNonN) + "\nfoldPercentageCorrectNonN: " + str(foldPercentageCorrectNonN) + "\nfoldProductions: " + str(foldProductions) + "\nfoldLeaves: " + str(foldLeaves) + "\nfoldPercentageLeaves: " + str(foldPercentageLeaves)+ "\nfoldFilesSkipped: " + str(foldFilesSkipped))
			print("Best: " + str(bestSolutionFiles) + ', ' + str(bestPercentage))
			print("Worst: " + worstSolutionFile + ', ' + str(worstPercentage)+ "\n")
		percentageCorrect = -1
		percentageCorrectNonN = -1
		percentageLeaves = -1
		if totalProductions > 0:
			percentageCorrect = totalCorrect / totalProductions
			percentageCorrectNonN = totalCorrectNonN / totalProductions
			percentageLeaves = totalLeaves / totalProductions
		print("Combined results:\ntotalCorrect: " + str(totalCorrect) + "\npercentageCorrect: " + str(percentageCorrect) + "\ntotalCorrectNonN: " + str(totalCorrectNonN) + "\npercentageCorrectNonN: " + str(percentageCorrectNonN) + "\ntotalProductions: " + str(totalProductions) + "\ntotalLeaves: " + str(totalLeaves) + "\npercentageLeavess: " + str(percentageLeaves) + "\n")
		#finish this case
		return

	#cross-validate
	crossVal(args)





if __name__ == "__main__":
	#sys.stdout = open('log.txt', 'w')
	#print(multiprocessing.cpu_count())
	main()