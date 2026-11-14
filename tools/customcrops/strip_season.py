import sys, re, pathlib

def indent(l): return len(l) - len(l.lstrip(' '))
def meaningful(l): s = l.strip(); return s and not s.startswith('#')

def block_end(lines, i):
    """i번 줄(키)의 블록이 끝나는 다음 줄 번호"""
    base = indent(lines[i]); j = i + 1
    while j < len(lines) and (not meaningful(lines[j]) or indent(lines[j]) > base):
        j += 1
    # 블록 끝에 붙은 빈 줄·주석은 다음 블록 몫으로 남긴다
    while j > i + 1 and not meaningful(lines[j - 1]):
        j -= 1
    return j

def parent(lines, i):
    base = indent(lines[i]); j = i - 1
    while j >= 0 and (not meaningful(lines[j]) or indent(lines[j]) >= base):
        j -= 1
    return j

def has_children(lines, i):
    end = block_end(lines, i)
    return any(meaningful(l) for l in lines[i + 1:end])

def strip(text, report):
    lines = text.split('\n')
    while True:
        for i, l in enumerate(lines):
            m = re.match(r'\s*type:\s*(season|suitable-season|unsuitable-season)\s*$', l)
            if not m:
                continue
            kind = m.group(1)
            target = parent(lines, i)                      # requirement_1 / season_condition / condition_1
            if kind == 'unsuitable-season':
                # 죽는 조건은 항목 전체를 지운다 (조건만 지우면 무조건 죽는 항목이 남음)
                while lines[parent(lines, target)].strip() != 'death-conditions:':
                    target = parent(lines, target)
            owner = parent(lines, target)
            report.append(f'{kind}: remove "{lines[target].strip()}" under "{lines[owner].strip()}"')
            del lines[target:block_end(lines, target)]
            if not has_children(lines, owner):
                key = lines[owner].rstrip().rstrip(':')
                lines[owner] = key + ': {}'
                report.append(f'  -> "{key.strip()}" is now empty ({{}})')
            break
        else:
            return '\n'.join(lines)

for path in sys.argv[1:]:
    p = pathlib.Path(path); report = []
    new = strip(p.read_text(encoding='utf-8'), report)
    if report:
        p.write_text(new, encoding='utf-8')
        print(f'== {p.name}'); [print('  ' + r) for r in report]
