#!/usr/bin/python
"""
Small script to extract helptexts from the ACC ServerAdminHandbook.
Usage: First, use pdftohtml with the pdf, then
    python extractMessages.py ../path/to/ServerAdminHandbooks.html
"""

import re, sys, json


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python extractMessages.py ../path/to/ServerAdminHandbooks.html')
        exit(1)

    outer = """Property.*\nRemarks.*\n((?:.|\n)*?)<br\/>\n(?:<b>)?&#160;(?:<\/b>)?<br\/>"""
    pattern = """(.*)<b>(?:.*)<br\/>\n((?:.|\n)+?(?=.*<b>|\Z))"""

    messages = {}
    for b in re.findall(outer, open(sys.argv[1]).read()):
        for (key, value) in re.findall(pattern, b):
            for c in [('<br/>',''), ('\n',''), ('&#160;',' '), ('“','"'), ('”','"')]:
                key = key.replace(*c).strip()
                value = value.replace(*c).strip()
            value = re.sub('<hr/><a.*</a>', '', value)
            value = re.sub('((?:S|s)ee\s+".*")', r'\1 (ServerAdminHandbook)', value)
            value = re.sub('(?:S|s)ee.*next table', 'see table in ServerAdminHandbook', value)
            messages[key] = value

    print(messages.keys())
    json.dump(messages, open('messages.json', 'w'), sort_keys=True, indent=4)