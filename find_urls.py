import os
import re

d = r'd:\medical-book-of-case-histories\templates'
urls = set()

for r, _, fs in os.walk(d):
    for f in fs:
        if f.endswith('.html'):
            path = os.path.join(r, f)
            with open(path, encoding='utf-8') as fp:
                for line in fp:
                    matches = re.findall(r'{%\s*url\s+[\'"]([^\'"]+)[\'"]', line)
                    urls.update(matches)

print('URLs found:', urls)
