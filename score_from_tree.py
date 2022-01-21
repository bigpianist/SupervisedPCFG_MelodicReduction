#This module will take a GTTM tree and its corresponding MusicXML document,
# and create a MusicXML melody at the tree depth desired.

import music_grammar
import music21
import nltk
import copy

def get_pitch_list_from_solution_tree(head_xml, tag_name, pitch_list):
	primary_xml = None
	try:
		head_note = head_xml.find('head/chord/note')
	except:
		print("failed!!!")
	#print(head_note)
	head_pitch_ref = head_note.attrib['id']
	primary_xml = head_xml.find('primary')
	if primary_xml != None:
		pitch_list = get_pitch_list_from_solution_tree(primary_xml.find(tag_name), tag_name, pitch_list)
		secondary_xml = head_xml.find('secondary')
		pitch_list = get_pitch_list_from_solution_tree(secondary_xml.find(tag_name), tag_name, pitch_list)
	else:
		if head_pitch_ref not in pitch_list:
			pitch_list.append(head_pitch_ref)
	return pitch_list

def get_total_depth_of_tree(head_xml, depth, tag_name):

	primary_xml = None

	try:
		head_note = head_xml.find('head/chord/note')
	except:
		print("failed!!!")
	#print(head_note)
	head_pitch_ref = head_note.attrib['id']
	primary_xml = head_xml.find('primary')
	depth += 1
	if primary_xml != None:
		primary_depth = get_total_depth_of_tree(primary_xml.find(tag_name), depth, tag_name)
		secondary_xml = head_xml.find('secondary')
		secondary_depth = get_total_depth_of_tree(secondary_xml.find(tag_name), depth, tag_name)
		if primary_depth > secondary_depth:
			depth = primary_depth
		else:
			depth = secondary_depth
	return depth

def get_total_depth_of_tree_obj(head, depth):
	depth += 1
	sub_tree_max = depth
	for subtree in head:
		if type(subtree) == nltk.tree.Tree or type(subtree) == nltk.tree.ProbabilisticTree:
			subtree_depth = get_total_depth_of_tree_obj(subtree, depth)
			if subtree_depth > sub_tree_max:
				sub_tree_max = subtree_depth
	if sub_tree_max > depth:
		depth = sub_tree_max
	return depth

#this grabs everything that is not 'N'
def remove_embellishment_rules_from_tree_below_depth(tree_root, removed_leaves, desired_depth, depth, leaf_index):
	parent_label = tree_root._label
	cur_num_children = 0
	depth += 1
	for index, subtree in enumerate(tree_root):
		print('subtree type is: ' + str(type(subtree)))
		if (parent_label == 'N' or parent_label == 'S') and (type(subtree) == nltk.tree.Tree or type(subtree) == nltk.tree.ProbabilisticTree):
			tree_root[index], removed_leaves, leaf_index = remove_embellishment_rules_from_tree_below_depth(subtree, removed_leaves, desired_depth, depth, leaf_index)
		elif parent_label != 'N':
			#KILL THE CHILDREN!!!!!
			if depth > desired_depth and len(tree_root) > 1:
				num_leaves = len(tree_root.leaves())
				#you're leaving one leaf remaining.
				removed_leaves[leaf_index] = num_leaves - 1
				leaf_index += 1
				del tree_root[:]
				tree_root.append(parent_label)
			elif (type(subtree) == nltk.tree.Tree or type(subtree) == nltk.tree.ProbabilisticTree):
				tree_root[index], removed_leaves, leaf_index = remove_embellishment_rules_from_tree_below_depth(subtree, removed_leaves, desired_depth, depth, leaf_index)
			else:
				leaf_index += 1
	return tree_root, removed_leaves, leaf_index


def remove_embellishment_rules_from_tree_negative_depth(tree_root, removed_leaves, desired_depth, depth, leaf_index, num_removed_leaves, stop_labels=[]):
	parent_label = tree_root._label
	max_subtree_depth = 0
	for index, subtree in enumerate(tree_root):
		#print('subtree type is: ' + str(type(subtree)))
		tree_depth = 1
		if type(tree_root) == nltk.tree.Tree or type(tree_root) == nltk.tree.ProbabilisticTree:
			tree_depth = tree_root.height()
		if parent_label in stop_labels and (type(subtree) == nltk.tree.Tree or type(subtree) == nltk.tree.ProbabilisticTree):
			tree_root[index], removed_leaves, leaf_index, max_subtree_depth, num_removed_leaves = remove_embellishment_rules_from_tree_negative_depth(subtree, removed_leaves, desired_depth, depth, leaf_index, num_removed_leaves)
		elif (len(stop_labels) == 2 and parent_label in stop_labels and parent_label != 'S') or len(stop_labels) != 2:
			#KILL THE CHILDREN!!!!!
			if tree_depth <= desired_depth and max_subtree_depth + 1 <= desired_depth and len(tree_root) > 1:
				num_leaves = len(tree_root.leaves())
				max_subtree_depth = tree_depth
				#you're leaving one leaf remaining.
				child_leaves = 0

				for i in range(num_leaves):
					if (i + leaf_index + num_removed_leaves) in removed_leaves:
						child_leaves += 1#removed_leaves[i + leaf_index + num_removed_leaves]
				#		del removed_leaves[i + leaf_index + num_removed_leaves]
				#It's possible that the left-hand side index has already been added
				#You're collapsing two leaves into one, so if the left is already collapsed
				#then you have to add the right child leaf.
				if (leaf_index + num_removed_leaves) in removed_leaves:
					removed_leaves.append(leaf_index + num_removed_leaves + child_leaves)
				else:
					removed_leaves.append(leaf_index + num_removed_leaves)
				#removed_leaves[leaf_index + num_removed_leaves] = num_leaves - 1 + child_leaves
				num_removed_leaves += num_leaves - 1 + child_leaves
				leaf_index += 1
				del tree_root[:]
				tree_root.append(parent_label)
			elif (type(subtree) == nltk.tree.Tree or type(subtree) == nltk.tree.ProbabilisticTree):
				tree_root[index], removed_leaves, leaf_index, max_subtree_depth, num_removed_leaves = remove_embellishment_rules_from_tree_negative_depth(subtree, removed_leaves, desired_depth, depth, leaf_index, num_removed_leaves)
			else:
				if (leaf_index + num_removed_leaves) in removed_leaves:
					num_removed_leaves += 1
				leaf_index += 1
		#elif isinstance(subtree, str):
		#		leaf_index += 1
	return tree_root, removed_leaves, leaf_index, max_subtree_depth, num_removed_leaves


def get_melody_from_parse_tree(parse_tree, removed_leaves, music_xml):
	melody_stream = music21.stream.Stream()
	#HAX this should be measure 1, but with an anacrusis, the time signature is in measure 2
	time_sig = music_xml.parts[0].measure(1).getContextByClass('TimeSignature')
	key_sig = music_xml.parts[0].measure(1).getContextByClass('KeySignature')
	melody_stream.append(time_sig)
	melody_stream.append(key_sig)
	notes = music_xml.flat.notes
	tree_leaves = parse_tree.leaves()
	note_index = 0
	leaf_index = 0
	num_ties = 0
	num_skipped_notes = 0
	#insert the first note of the song
	#HAX
	melody_stream.insert(notes[note_index].offset, notes[note_index])
	if notes[note_index].tie != None:
		next_note = notes[note_index + 1]
		if next_note.tie and next_note.tie.type == 'stop':
			melody_stream.insert(next_note.offset, next_note)
			note_index += 1
	note_index += 1
	cur_skips = 0
	skippedANote = False
	for leaf in tree_leaves:
		if leaf_index in removed_leaves:
			#print('skipping note index of: ' + str(note_index))
			skippedANote = True
			note_index += 1
			leaf_index += 1
			continue
		if note_index >= len(notes):
			print("this bad")
		melody_stream.insert(notes[note_index].offset, notes[note_index])
		if skippedANote:
			cur_note = melody_stream[-1]
			prev_note = melody_stream[-2]
			new_dur_value = cur_note.offset - prev_note.offset
			new_dur = music21.duration.Duration(new_dur_value)
			prev_note.duration = new_dur
			skippedANote = False

		if notes[note_index].tie != None:
			next_note = notes[note_index + 1]
			if next_note.tie and next_note.tie.type == 'stop':
				melody_stream.insert(next_note.offset, next_note)
				note_index += 1

		note_index += 1
		leaf_index += 1
	if note_index < len(notes):
		melody_stream.insert(notes[note_index].offset, notes[note_index])
		if skippedANote:
			cur_note = melody_stream[-1]
			prev_note = melody_stream[-2]
			new_dur_value = cur_note.offset - prev_note.offset
			new_dur = music21.duration.Duration(new_dur_value)
			prev_note.duration = new_dur
			skippedANote = False
	melody_stream.show()
	return melody_stream


#this modifies the input tree
def get_tree_obj_to_negative_depth(tree_root, negative_depth, depth):
	depth += 1
	sub_tree_max = depth
	leaf_index = 0
	leaf_positions = tree_root.treepositions('leaves')
	for index, leaf_pos in enumerate(tree_root.treepositions('leaves')):
		if len(leaf_pos) > 0:
			print(leaf_pos)
			print(len(leaf_pos))
			print(type(leaf_pos))
			print(tree_root)
			print(type(tree_root))
			parent = tree_root[leaf_pos]
			print(parent.right_sibling())
			print(parent)
	while leaf_index < len(tree_root.leaves()):
		next_leaf_index = leaf_index
		cur_leaf = tree_root.leaves()[leaf_index]
		right_sib = cur_leaf.right_sibling()
		if right_sib is not None:
			next_leaf_index += 2
			print('right sib is: ' + str(right_sib._label))

		if depth <= negative_depth:
			print('poo')
	if sub_tree_max > depth:
		depth = sub_tree_max
	return depth

def gather_note_refs_of_depth(head_xml, note_refs, tag_name, desired_depth, depth = 0):
	primary_xml = None
	try:
		head_note = head_xml.find('head/chord/note')
	except:
		print("failed!!!")
	#print(head_note)
	head_pitch_ref = head_note.attrib['id']
	if head_pitch_ref not in note_refs:
		note_refs.append(head_pitch_ref)
	primary_xml = head_xml.find('primary')
	depth += 1
	if primary_xml != None and depth <= desired_depth:
		primary_notes = gather_note_refs_of_depth(primary_xml.find(tag_name), note_refs, tag_name, desired_depth, depth)
		secondary_xml = head_xml.find('secondary')
		secondary_notes = gather_note_refs_of_depth(secondary_xml.find(tag_name), note_refs, tag_name, desired_depth, depth)
		for nr in primary_notes:
			if nr not in note_refs:
				note_refs.append(nr)
		for nr2 in secondary_notes:
			if nr2 not in note_refs:
				note_refs.append(nr2)
	return note_refs

def pitch_refs_to_notes(ordered_pitch_ref_list, music_xml):
	melody_stream = music21.stream.Stream()
	time_sig = music_xml.parts[0].measure(1).getContextByClass('TimeSignature')
	melody_stream.append(time_sig)
	prev_offset = 0
	for p in ordered_pitch_ref_list:
		note = music_grammar.lookUpPitchReference(p, music_xml, False, True)
		#print(note.offset)
		#print(note)
		if len(melody_stream) > 1:
			dur_between = music21.duration.Duration(note.offset - melody_stream[-1].offset)
			#print('melody_stream[-1] is : ' + str(melody_stream[-1]))
			#print('dur_between is : ' + str(dur_between))
			melody_stream[-1].duration = dur_between
		melody_stream.insert(note.offset, note)
	return melody_stream

def print_reductions_for_solution_xml(solution_xml, music_xml, reduction_type):
	depth = get_total_depth_of_tree(solution_xml, 0, reduction_type)
	for d in reversed(range(0, depth - 1)):
		pitch_refs = gather_note_refs_of_depth(solution_xml, [], reduction_type, d, 0)
		pitch_refs.sort(key=music_grammar.pitchRefToNum)
		melody_of_depth = pitch_refs_to_notes(pitch_refs, music_xml)
		melody_of_depth.show()


def print_reductions_for_parse_tree(parse_tree, music_xml, stop_labels=['S', 'N']):
	depth = parse_tree.height()
	music_xml.show()
	original_parse_tree_copy = copy.deepcopy(parse_tree)
	parse_tree_copy = copy.deepcopy(parse_tree)
	original_parse_tree_copy.draw()
	#get_melody_from_parse_tree(parse_tree, {}, music_xml)
	pruned_parse, removed_leaves, leaf_index, max_subtree_depth, num_removed_leaves = remove_embellishment_rules_from_tree_negative_depth(parse_tree, [], 3, 0, 0, 0, stop_labels)

	while pruned_parse != parse_tree_copy:
		print(removed_leaves)
		pruned_melody = get_melody_from_parse_tree(original_parse_tree_copy, removed_leaves, music_xml)
		pruned_parse.draw()

		parse_tree_copy = copy.deepcopy(pruned_parse)
		pruned_parse, removed_leaves, leaf_index, max_subtree_depth, num_removed_leaves = remove_embellishment_rules_from_tree_negative_depth(parse_tree, removed_leaves, 3, 0, 0, 0, stop_labels)


