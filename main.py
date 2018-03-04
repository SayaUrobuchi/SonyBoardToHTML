# coding: utf-8

from __future__ import print_function

import sys;
import os;
import shutil;
import re;
import cgi;

from cStringIO import StringIO;

def read_until_0(f, idx):
	res = [];
	f.seek(idx);
	while True:
		b = f.read(1);
		if ord(b[0]) == 0x00:
			break;
		res.append(b[0]);
	return ''.join(res);

def main():
	# get current path
	path = os.getcwd();
	# if argv[1] isn't empty, combine with it will allow related path
	# os.path.join() also accept absolute path
	if len(sys.argv) > 1:
		path = os.path.join(path, sys.argv[1]);
		
	more_info = False;
	if len(sys.argv) > 2:
		more_info = True;
	
	print('target path: [{0}]; finding INDEX FILE..'.format(path));
	# read index file '.DIR'
	try:
		index_f = open(os.path.join(path, '.DIR'), 'rb');
		index_len = os.fstat(index_f.fileno()).st_size;
	except Exception as e:
		print('read INDEX FILE error: '+str(e));
		quit();
	print('success. loading INDEX FILE..');
	
	# template of html
	header = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>sa072686.bbs@sony.tfcis.org</title>
<link rel="stylesheet" type="text/css" href="bbs.css">
</head>
<body>
	""";
	footer = """
</body>
</html>
	""";
	# template of every article div
	pattern = """
<div class="article">
	<a name="{idx}" /><a name="{id}" />
	<div class="title"><a href="#{id}">#{idx}: {title}</a></div>
	<div class="author">作者: {author} at {date}</div>
	<div class="content">{content}</div>
</div>
	""";
	
	res = StringIO();
	res.write(header);
	# for index parse
	start_idx = 0x0C;
	article_len = 0x0100;
	id_shift = 0x00;
	author_shift = 0x20;
	date_shift = 0xA2;
	title_shift = 0xAB;
	code = 'big5hkscs';
	#code = 'cp950';
	code_u = 'utf8';
	# parse every article
	article_count = 0;
	fail_count = 0;
	idx = start_idx;
	while idx < index_len:
		article_id = read_until_0(index_f, idx+id_shift).decode('ASCII');
		article_path = os.path.join(path, '{0}/{1}'.format(article_id[-1], article_id));
		if more_info:
			print('reading article {idx} [{id}].. '.format(idx=article_count, id=article_id), end='');
		try:
			article_f = open(os.path.join(path, article_path), 'rb');
			article_f.readline();
			article_f.readline();
			article_f.readline();
			article_f.readline();
			buff = article_f.read();
			content = re.sub(r'\x1B\x5B.*?\x6D', '', buff);
			res.write(pattern.format(
				idx = ("%04d" % (article_count)), 
				id = article_id, 
				title = cgi.escape(read_until_0(index_f, idx+title_shift).decode(code, 'replace').encode(code_u)), 
				author = read_until_0(index_f, idx+author_shift), 
				date = read_until_0(index_f, idx+date_shift), 
				content = cgi.escape(content.decode(code, 'replace').encode(code_u)), 
			));
			if more_info:
				print('success.');
		except Exception as e:
			fail_count += 1;
			print('failed {1} [{2}]: {0}.'.format(str(e), article_count, article_id));
		finally: 
			article_f.close();
		article_count += 1;
		idx += article_len;
		
	res.write(footer);
	print('finished with failed {0}/{1}.'.format(fail_count, article_count));
	
	hp_f = open(os.path.join(path, 'index.html'), 'wb');
	hp_f.write(res.getvalue());
	hp_f.close();
	shutil.copyfile(os.path.join(os.getcwd(), 'bbs.css'), os.path.join(path, 'bbs.css'));
	
	index_f.close();

if __name__ == '__main__':
	main();