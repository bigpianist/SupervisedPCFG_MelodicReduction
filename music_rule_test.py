import operator
import validate_tree
import music_grammar
import pcfg_generate
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
from nltk.compat import python_2_unicode_compatible


from nltk.draw import tree


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

def crossVal(args):
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
			trainingSet = []
			for index, fold in enumerate(foldIndices):
				if index != testFold:
					for i in fold:
						trainingSet.append(fileList[i])

			testSet = [fileList[j] for j in foldIndices[testFold]]
			solutionTreeDict, allProductions = music_grammar.getAllProductions(args.directory, args.type, trainingSet, args.type, args.verbose)

			foldFile = 'fold' + str(testFold) + '_' + args.type + '_trainingProductions.txt'
			f = open(foldFile, 'w')
			for prod in allProductions:
				f.write(prod + '\n')
			foldTestFile = 'fold' + str(testFold) + '_' + args.type + '_testSetFilenames.txt'
			f2 = open(foldTestFile, 'w')
			for filename in testSet:
				f2.write(filename + '\n')
			S = Nonterminal('S')
			smallTrees = music_grammar.collectProductions(allProductions, args.verbose)
			trainedGrammar = induce_pcfg(S, smallTrees)
			print(trainedGrammar)


			print('length of the trainingset is: ' + str(len(trainingSet)))
			print('length of the testset is: ' + str(len(testSet)))

			print("starting to get solutions for the test set ")
			testProductions = []

			solutionTreeDictForTestSet, testProductions = music_grammar.getAllProductions(args.directory, args.type, testSet, args.type, args.verbose)
			foldTestSolutionsFile = 'fold' + str(testFold) + '_' + args.type + '_testSolutions.txt'
			f3 = open(foldTestSolutionsFile, 'w')
			#for key, value in solutionTreeDictForTestSet.items():
			#	f3.write(key + '\n' + str(value) + '\n')
			json.dump(solutionTreeDictForTestSet,f3)
			print("parsing the test set")
			totalCorrect, totalCorrectNonN, totalProductions, totalLeaves, parseTreeStrings = music_grammar.parseAllTestXmls(testSet, trainedGrammar, solutionTreeDictForTestSet, args.verbose, False)#"./MusicXml/Test"

			#print the parses
			foldParsesFile = 'fold' + str(testFold) + '_' + args.type + '_parsedTestSet.txt'
			f4 = open(foldParsesFile, 'w')
			#for filename, parse in parseTreeStrings.items():
			#f4.write(filename + '\n' + parse + '\n')
			json.dump(parseTreeStrings, f4)

			percentageCorrect = -1
			percentageCorrectNonN = -1
			percentageLeaves = -1
			if totalProductions > 0:
				percentageCorrect = totalCorrect / totalProductions
				percentageCorrectNonN = totalCorrectNonN / totalProductions
				percentageLeaves = totalLeaves / totalProductions
			results.write("Fold number " + str(testFold) + " results:\ntotalCorrect: " + str(totalCorrect) + "\npercentageCorrect: " + str(percentageCorrect) + "\ntotalCorrectNonN: " + str(totalCorrectNonN) + "\npercentageCorrectNonN: " + str(percentageCorrectNonN) + "\ntotalProductions: " + str(totalProductions) + "\ntotalLeaves: " + str(totalLeaves) + "\npercentageLeavess: " + str(percentageLeaves) + "\n")


def removeProbability(treeString):
	probabilisticPart = re.findall('(\(p=[^()]*\))', treeString)
	indexOfProbPart = treeString.index(probabilisticPart[0])
	return treeString[:indexOfProbPart]

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("directory", help="Directory that contains melody files")
	parser.add_argument("solutions", help="Directory that contains the solution files")
	parser.add_argument("-g", "--grammar", help="The file that specifies a saved grammar, this grammar will be used instead of training a new one")
	parser.add_argument("-f", "--folds", help="number of folds desired")
	parser.add_argument("-o", "--outfile", help="The file that the grammar will be saved in")
	parser.add_argument("-t", "--type", help="The type of solutions file we're using, either 'PR' or 'TS' for Prolongational Reduction or Time-span Tree, respectively")
	parser.add_argument("-v", "--verbose", help="increase output verbosity")
	args = parser.parse_args()
	print(args)


	if args.verbose == None or args.verbose == 'False':
		args.verbose = False
	elif args.verbose == 'True':
		args.verbose = True

	#If the grammar is specified, then the "directory" folder will be used as a test set
	#If the grammar is not specified, it will use 20% of the files in "directory" as a test set, and the rest as a training set to create the grammar
	#If folds are specified, then it will split the files in "directory" into numFolds groups, applying training and testing, and then adding up the percentages overall
	allProductions = []
	stats = True
	if args.grammar != None and args.grammar != '':
		if not os.path.isfile(args.grammar):
			return
		f = open(args.grammar, 'r')
		for line in f.readlines():
			allProductions.append(line)
		S = Nonterminal('S')
		smallTrees = music_grammar.collectProductions(allProductions, args.verbose)
		trainedGrammar = induce_pcfg(S, smallTrees)
		print(trainedGrammar)
		np_productions = trainedGrammar.productions(Nonterminal('4'))
		dict = {}
		for pr in np_productions: dict[pr.rhs()] = pr.prob()
		np_probDist = DictionaryProbDist(dict)


		#Used this code for generating specific figures:
		exampleTree = Tree.fromstring('(S (N (N (5 5)) (N (m4 -4))) (N (6 6)))')
		#exampleTree.draw()
		exampleTreeToCompare = Tree.fromstring('(S (N (5 5)) (N (N (m4 -4)) (N (6 6))))')
		#exampleTreeToCompare.draw()
		validate_tree.compareTreesBottomUp(exampleTree, exampleTreeToCompare)
		#exampleTreeToCompare.draw()


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

		fileToTest = "./MusicXml/72_Preludes 1 La fille aux cheveux de lin.xml"
		musicXmlTest = converter.parse(fileToTest)

		curPitchList = music_grammar.getPitchListFromFile(fileToTest)

		intervalList = music_grammar.getIntervalStringsFromPitchList(curPitchList)


		with open(music_grammar.musicGrammarFilename, 'r') as f:
			musicGrammarString = f.read()
		musicGrammar = CFG.fromstring(musicGrammarString)
		parser = ChartParser(musicGrammar, trace=2)
		#parses = parser.parse(intervalList)

		print(intervalList)
		print('num intervals is: ' + str(len(intervalList)))
		#numTrees = sum(1 for _ in parses)
		#print('numTrees is: ' + str(numTrees))
		#return

		#this is for the musical examples

		trainedParser = ViterbiParser(trainedGrammar)
		parses = trainedParser.parse_all(intervalList)
		bestParse = parses[0]
		#bestParse.draw()
		treeType = bestParse.convert(ParentedTree)
		parse_depth = 0
		depth = score_from_tree.get_total_depth_of_tree_obj(bestParse, parse_depth)
		print('depth is : ' + str(depth))
		print('builtin height is : ' + str(bestParse.height()))
		print(bestParse)
		bestParse.draw()
		#score_from_tree.get_tree_obj_to_negative_depth(bestParse, 2, parse_depth)

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

	if stats == True:
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
			bestPercentage = .25
			worstPercentage = .2
			#get parses from file
			parseFilename = "fold" + str(fold) + "_" + args.type + "_parsedTestSet.txt"
			parseFile = open(parseFilename, 'r')
			parses = json.load(parseFile)
			#get solutions from file
			solutionsFilename = "fold" + str(fold) + "_" + args.type + "_testSolutions.txt"
			solutionsFile = open(solutionsFilename, 'r')
			solutions = json.load(solutionsFile)

			foldLeaves = 0
			foldProductions = 0
			foldCorrect = 0
			foldCorrectNonN = 0
			for filename, solutionTree in solutions.items():
				if parses[filename] != None and parses[filename] != '':
					solutionTreeObj = Tree.fromstring(solutionTree)
					parseStr = parses[filename]
					probabilisticPart = re.findall('(\(p=[^()]*\))', parseStr)
					indexOfProbPart = parseStr.index(probabilisticPart[0])
					parseTreeObj = Tree.fromstring(parseStr[:indexOfProbPart])

					#here's where we look at example reductions in musical scores
					curMusicXml = converter.parse(filename)
					if len(curMusicXml.flat.notes) >= 15 and len(curMusicXml.flat.notes) < 20 or filename == './MusicXml/03_Bagatelle \'Fur Elise\' WoO.59.xml':
						print(filename)
						if filename != './MusicXml/03_Bagatelle \'Fur Elise\' WoO.59.xml':
							continue
						#if args.type == 'PR':
						solutionFilename = args.type + "-" + basename(filename)
						solutionFilepath = args.directory + '/' + args.type + '/' + solutionFilename
						#else:

						#	solutionFilename = args.type + "-" + basename(filename)[4:]
						#	solutionFilepath = args.directory + '/' + args.type + '/' + solutionFilename[:-4] + '_1' + solutionFilename[-4:]

						ET = ElementTree()
						ET.parse(solutionFilepath)
						root = ET.getroot()
						rootName = args.type.lower()
						topXml = root.find(rootName)
						#topXml.show()
						if num_skip > 0:
							num_skip -= 1
							continue
						parseTreeObj.draw()
						#score_from_tree.print_reductions_for_parse_tree(parseTreeObj, curMusicXml)
						depth = 0
						depth = score_from_tree.get_total_depth_of_tree(topXml, depth, rootName)
						print('depth is ' + str(depth))
						curMusicXml.show()
						for d in reversed(range(0, depth - 1)):
							pitch_refs = score_from_tree.gather_note_refs_of_depth(topXml, [], rootName, d, 0)
							pitch_refs.sort(key=music_grammar.pitchRefToNum)
							melody_of_depth = score_from_tree.pitch_refs_to_notes(pitch_refs, curMusicXml)
							melody_of_depth.show()
							print (pitch_refs)

					continue
					parseTreeObjAfterComparison = copy.deepcopy(parseTreeObj)
					numProductions = len(solutionTreeObj.productions())
					foldProductions += numProductions
					bottomCorrect, bottomCorrectNonN = validate_tree.compareTreesBottomUp(solutionTreeObj, parseTreeObjAfterComparison)

					if bottomCorrect / numProductions > worstPercentage:# and bottomCorrect / numProductions < bestPercentage:
						bestSolutionFiles.append(filename)
						if filename in goodOnesPR and False:
							print(filename)
							print(parseTreeObj.leaves())
							solutionTreeObj.draw()
							parseTreeObj.draw()
							parseTreeObjAfterComparison.draw()
						#bestPercentage = bottomCorrect / numProductions

					#if bottomCorrect / numProductions < worstPercentage:
					#	worstSolutionFile = filename
					#	worstPercentage = bottomCorrect / numProductions
					foldLeaves = len(solutionTreeObj.leaves())

					foldCorrect += bottomCorrect
					foldCorrectNonN += bottomCorrectNonN
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
			print("Fold number " + str(fold) + " results:\nfoldCorrect: " + str(foldCorrect) + "\nfoldPercentageCorrect: " + str(foldPercentageCorrect) + "\nfoldCorrectNonN: " + str(foldCorrectNonN) + "\nfoldPercentageCorrectNonN: " + str(foldPercentageCorrectNonN) + "\nfoldProductions: " + str(foldProductions) + "\nfoldLeaves: " + str(foldLeaves) + "\nfoldPercentageLeaves: " + str(foldPercentageLeaves))
			print("Best: " + str(bestSolutionFiles) + ', ' + str(bestPercentage))
			print("Worst: " + worstSolutionFile + ', ' + str(worstPercentage)+ "\n")
		percentageCorrect = -1
		percentageCorrectNonN = -1
		percentageLeaves = -1
		if totalProductions > 0:
			percentageCorrect = totalCorrect / totalProductions
			percentageCorrectNonN = totalCorrectNonN / totalProductions
			percentageLeaves = totalLeaves / totalProductions
		print("results:\ntotalCorrect: " + str(totalCorrect) + "\npercentageCorrect: " + str(percentageCorrect) + "\ntotalCorrectNonN: " + str(totalCorrectNonN) + "\npercentageCorrectNonN: " + str(percentageCorrectNonN) + "\ntotalProductions: " + str(totalProductions) + "\ntotalLeaves: " + str(totalLeaves) + "\npercentageLeavess: " + str(percentageLeaves) + "\n")
		#finish this case
		return

	#cross-validate
	crossVal(args)





if __name__ == "__main__":
    main()