import sys

# merge
dict_cid_res = {}
with open('student_target.txt', 'r') as handle_f:
	for line in handle_f:
		arr_content = line.strip().split('\t')
		cid, rec_question = int(arr_content[0]), arr_content[6]
		dict_cid_res[cid] = rec_question


dict_cid_text = {}
with open('student_rec.txt', 'r') as r_handle:
	for line in r_handle:
		arr_res = line.strip().split('\t')
		cid = int(arr_res[0])
		if cid in dict_cid_res:
			arr_res[3] = dict_cid_res[cid]

		str_update = '\t'.join(str(x) for x in arr_res)
		dict_cid_text[cid] = str_update

with open('student_rec.txt', 'w') as w_handle:
	for cid in dict_cid_text:
		str_text = dict_cid_text[cid]
		w_handle.write("%s\n" % str_text)

