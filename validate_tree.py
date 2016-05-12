import re
from nltk.tree import ParentedTree

def getAllPitchReferencesAsList(solutionXml):
	root = solutionXml.getroot()
	topPRXml = root.find('pr')
	allPitchRefs = set()
	headTuple = getPitchReferenceRecursive(topPRXml, allPitchRefs)
	return allPitchRefs


def getPitchReferenceRecursive(topNodeXml, pitchRefs):
	headNote = topNodeXml.find('head/chord/note')
	headPitchRef = headNote.attrib['id']
	pitchRefs.add(headPitchRef)
	primaryXml = topNodeXml.find('primary')
	if primaryXml != None:
		primaryTuple = getPitchReferenceRecursive(primaryXml.find('pr'), pitchRefs)
		#if primaryTuple.primary != None and primaryTuple.secondary != None:
		secondaryXml = topNodeXml.find('secondary')
		if secondaryXml == None:
			print('this is bad- no secondary tag when a primary tag exists')
		secondaryTuple = getPitchReferenceRecursive(secondaryXml.find('pr'), pitchRefs)

def validateSolutionTree(treeObj, originalIntervalList, originalPitchList, solutionFile):
	pitchRefs = getAllPitchReferencesAsList(treeObj)
	#we can use the sorted pitch references to index the pitch, and by extension the interval
	sortedPitchRefs = sorted(list(pitchRefs))

def traverseNode(node):
	print(node)
	if isinstance(node, str) == True:
		return
	for child in node:
		traverseNode(child)


def traverseTree(tree):
	traverseNode(tree)


def compareNodes(node1, node2, numCorrect, numCorrectNonN):
	if isinstance(node1, str) == True:
		return numCorrect, numCorrectNonN

	headToken1 = node1._label
	headToken2 = node2._label

	if headToken1 == headToken2 and len(node1) == len(node2):
		numCorrect += 1
		if headToken1 != 'N':
			numCorrectNonN += 1

		for index, child in enumerate(node1):
			childNumCorrect, childNumCorrectNonN = compareNodes(node1[index], node2[index], 0, 0)
			numCorrect += childNumCorrect
			numCorrectNonN += childNumCorrectNonN
	return numCorrect, numCorrectNonN



def compareNodesAndReplace(node1, node2, numCorrect, numCorrectNonN):
	if isinstance(node1, str) == True:
		return numCorrect, numCorrectNonN

	headToken1 = node1._label
	headToken2 = node2._label

	if headToken1 == headToken2 and len(node1) == len(node2):
		numCorrect += 1
		if headToken1 != 'N':
			numCorrectNonN += 1
		node2.setlabel('X')

		for index, child in enumerate(node1):
			childNumCorrect, childNumCorrectNonN = compareNodesAndReplace(node1[index], node2[index], 0, 0)
			numCorrect += childNumCorrect
			numCorrectNonN += childNumCorrectNonN
	return numCorrect, numCorrectNonN

def isNodeLeftChild(tree, node, nodePos):
	parentNodePos = nodePos[:-1]
	parentNode = tree[parentNodePos]
	for index, child in enumerate(parentNode):
		if child == node:
			if index == 0:
				return True
			else:
				return False
	return False


def compareNodesBottomUp(tree1, tree2, node1Pos, node2Pos, numCorrect, numCorrectNonN):
	if node1Pos == [] or node2Pos == []:
		return numCorrect, numCorrectNonN

	node1 = tree1[node1Pos]
	node2 = tree2[node2Pos]

	if isinstance(node1, str) == False:
		headToken1 = node1._label
		headToken2 = node2._label
	else:
		headToken1 = node1
		headToken2 = node2

	node1IsLeft = isNodeLeftChild(tree1, node1, node1Pos)
	node2IsLeft = isNodeLeftChild(tree2, node2, node2Pos)
	if headToken1 == headToken2 and node1IsLeft == node2IsLeft:
		if isinstance(node1, str) == False:
			tree2[node2Pos].set_label('X')
			numCorrect += 1
			if headToken1 != 'N':
				numCorrectNonN += 1

		parentNode1Pos = node1Pos[:-1]
		parentNode2Pos = node2Pos[:-1]
		parentNumCorrect, parentNumCorrectNonN = compareNodesBottomUp(tree1, tree2, parentNode1Pos, parentNode2Pos, 0, 0)
		numCorrect += parentNumCorrect
		numCorrectNonN += parentNumCorrectNonN
	return numCorrect, numCorrectNonN

def createAlignmentMatrix(list1, list2):

	m = len(list1)
	n = len(list2)

	d = [[0 for col in range(n)] for row in range(m)]

	for i in range(m):
		if i == 0:
			continue
		d[i][0] = i


	for j in range(n):
		if j == 0:
			continue
		d[0][j] = j
	for j in range(n):
		if j == 0:
			continue
		for i in range(m):
			if i == 0:
				continue
			if list1[i] == list2[j]:
				d[i][j] = d[i-1][j-1]
			else:
				deletionCost = d[i-1][j] + 1
				insertionCost = d[i][j-1] + 1
				#substitutionCost = d[i-1][j-1] + 1
				d[i][j] = min(deletionCost,insertionCost)#, substitutionCost)
	return d

	#return indices

def getIndexOffsetFromPath(path):
	indicesOffset = []
	for i in path:
		for j in range(i):
			if j == 0:
				continue

def alignLeaves(list1, list2):
	matrix = createAlignmentMatrix(list1, list2)
	path = []
	m = len(list1)
	n = len(list2)
	i = m - 1
	j = n - 1
	currentLength = 0
	while i >= 0 and j >= 0:
		if i > 0 and j > 0:
			if matrix[i-1][j] > matrix[i-1][j-1] and matrix[i][j-1] > matrix[i-1][j-1] and matrix[i-1][j-1] == matrix[i][j]:
				i -= 1
				j -= 1
				path.insert(0, currentLength)
				currentLength = 0
			elif matrix[i-1][j] < matrix[i][j-1]:
				i -= 1
				currentLength -= 1
			else:
				j -= 1
				currentLength += 1
			#print(matrix[i][j])
		elif i == 0:
			if j > 0:
				currentLength += 1
			j -= 1
		else:
			if i > 0:
				currentLength += 1
			i -= 1
	path.insert(0, currentLength)
	return path, matrix


def compareTreesBottomUp2(tree1, tree2):
	from nltk.draw.tree import draw_trees
	#tree1.draw()
	#tree2.draw()
	tree2Leaves = tree2.leaves()
	tree2LeafPositions = tree2.treepositions('leaves')
	tree1Leaves = tree1.leaves()
	bestPath = alignLeaves(tree1Leaves, tree2Leaves)
	#print(bestPath)
	tree2LeafIndex = 0
	difference = 5#len(tree1.leaves()) - len(tree2.leaves())
	#sometimes there are extra leaves in the solution tree
	offset = 0
	totalNumCorrect = 0
	totalNumCorrectNonN = 0
	for index, leafPos in enumerate(tree1.treepositions('leaves')):
		if (offset + tree2LeafIndex) >= len(tree2.leaves()):
			break
		if tree1Leaves[index] == tree2Leaves[tree2LeafIndex + offset]:
			numCorrect, numCorrectNonN = compareNodesBottomUp(tree1, tree2, leafPos, tree2LeafPositions[tree2LeafIndex + offset], 0, 0)
			totalNumCorrect += numCorrect
			totalNumCorrectNonN += numCorrectNonN
		else:
			tempOffset = 1
			while (tree2LeafIndex + offset + tempOffset) < (len(tree2.leaves()) - 1) and tree1Leaves[index] != tree2Leaves[tree2LeafIndex + offset + tempOffset]:
				tempOffset += 1
			if (tree2LeafIndex + offset + tempOffset) < len(tree2.leaves()) and tree1Leaves[index] == tree2Leaves[tree2LeafIndex + offset + tempOffset]:
				numCorrect, numCorrectNonN = compareNodesBottomUp(tree1, tree2, leafPos, tree2LeafPositions[tree2LeafIndex + offset + tempOffset], 0, 0)
				totalNumCorrect += numCorrect
				totalNumCorrectNonN += numCorrectNonN
				offset += tempOffset
	return totalNumCorrect, totalNumCorrectNonN

def compareTreesBottomUp(tree1, tree2):
	from nltk.draw.tree import draw_trees
	#tree1.draw()
	#tree2.draw()
	tree1Leaves = tree1.leaves()
	tree1LeafPositions = tree1.treepositions('leaves')
	tree2Leaves = tree2.leaves()
	tree2LeafPositions = tree2.treepositions('leaves')
	bestPath, matrix = alignLeaves(tree1Leaves, tree2Leaves)

	print("tree1Leaves" + str(tree1Leaves))
	print("tree2Leaves" + str(tree2Leaves))
	print("bestpath" + str(bestPath))
	tree2LeafIndex = 0
	difference = 5#len(tree1.leaves()) - len(tree2.leaves())
	#sometimes there are extra leaves in the solution tree
	offset = 0
	totalNumCorrect = 0
	totalNumCorrectNonN = 0
	tree1LeafIndex = len(tree1Leaves) - 1
	tree2LeafIndex = len(tree2Leaves) - 1
	for p in reversed(bestPath):
		if p > 0:
			tree2LeafIndex -= p
		if p < 0:
			tree1LeafIndex += p
		#print('p is "'+ str(p) + '", comparing: tree1(' + str(tree1LeafIndex) + ', ' + str(tree1Leaves[tree1LeafIndex]) + ') with tree2(' + str(tree2LeafIndex) + ', ' + str(tree2Leaves[tree2LeafIndex]) + ')')
		numCorrect, numCorrectNonN = compareNodesBottomUp(tree1, tree2, tree1LeafPositions[tree1LeafIndex], tree2LeafPositions[tree2LeafIndex], 0, 0)
		totalNumCorrect += numCorrect
		totalNumCorrectNonN += numCorrectNonN
		tree1LeafIndex -= 1
		tree2LeafIndex -= 1
	return totalNumCorrect, totalNumCorrectNonN

def compareTrees(tree1, tree2):
	numCorrect = 0
	numCorrectNonN = 0
	copyTree = tree2
	numCorrect, numCorrectNonN = compareNodes(tree1, copyTree, numCorrect, numCorrectNonN)
	return numCorrect, numCorrectNonN



