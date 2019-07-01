#!/usr/bin/python
"""
Small script to extract helptexts from the ACC ServerAdminHandbook.
Usage: First, use pdftohtml with the pdf, then
    python extractMessages.py ../path/to/ServerAdminHandbook_v1s.html
"""

import re, sys, json


if __name__== "__main__":
    if len(sys.argv)!=2:
        print('Usage: python extractMessages.py ../path/to/ServerAdminHandbook_v1s.html')
        exit(1)

    outer = """<b>Property.*\n<b>Remarks.*\n((?:.|\n)*?)<br\/>\n(?:<b>)?&#160;(?:<\/b>)?<br\/>"""
    pattern = """(?:<b>(.*)<\/b>((?:.|\n)+?(?=<b>|\Z)))"""

    messages = {}
    for b in re.findall(outer, open(sys.argv[1]).read()):
        for (key, value) in re.findall(pattern, b):
            key = key.replace('&#160;',' ').replace('<br/>','').strip()
            value = value.replace('&#160;',' ').replace('<br/>','').strip()
            value = re.sub(r'href="(.*)"',r'href="https://www.assettocorsa.net/forum/index.php?threads/the-server-admin-handbook-thread.58245/"', value)
            messages[key] = value

    print(messages.keys())
    json.dump(messages, open('messages.json', 'w'))