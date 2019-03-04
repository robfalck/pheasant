import os
from typing import Generator

import nbformat
from nbformat import NotebookNode

from pheasant.code.config import config
from pheasant.jupyter.renderer import run_and_render
from pheasant.markdown.splitter import escaped_splitter_join
from pheasant.number import config as config_number
from pheasant.utils import read_source


def convert(source: str) -> str:
    source = ''.join(render(source))
    return source


def render(source: str) -> Generator[str, None, None]:
    pattern_escape = r'(```(.*?)```)|(~~~(.*?)~~~)'
    pattern_code = config['code_pattern']

    splitter = escaped_splitter_join(pattern_code, pattern_escape, source)
    for splitted in splitter:
        if isinstance(splitted, str):
            yield splitted
        else:
            language, reference = splitted.group(1, 2)
            if splitted.group().startswith('#'):
                yield generate_header(language, reference)
            if language == 'python':
                yield inspect(language, reference)
            elif language == 'file':
                yield read_file(reference)
            else:
                yield splitted.group()


def generate_header(language: str, reference: str) -> str:
    if language == 'python':
        code = 'Code'
    elif language == 'file':
        code = 'File'
    else:
        return ''
    return f'#{code} {reference}\n'


def inspect(language: str, reference: str,
            func: str = 'inspect.getsourcelines') -> str:
    """Inspect source code."""
    name, *options = reference.split(' ')  # `Options` is not implemented.
    name, *line_range = name.split(':')  # `line_range` is not implemented.

    cell = nbformat.v4.new_code_cell(f'{func}({name})')
    return run_and_render(cell, lambda cell: inspect_render(cell, language))


def inspect_render(cell: NotebookNode, language: str) -> str:
    """Convert a cell generated by inspection into markdown."""
    for output in cell['outputs']:
        if 'data' in output and 'text/plain' in output['data']:
            lines, lineno = eval(output['data']['text/plain'])
            source = ''.join(lines)
            return fenced_code(source, language)
    return ''


def read_file(path: str) -> str:
    """Read a file from disc.

    `path`: `<path_to_file>:<language>` form is avaiable.
    Otherwise, the language is determined from the path's extension.
    For example, If the path is `a.py`, then the language is Python.
    """
    if ':' in path:
        path, language = path.split(':')
    else:
        language = ''

    if path.startswith('~'):
        path = os.path.expanduser(path)

    if not os.path.exists(path):
        return f'<p style="font-color:red">File not found: {path}</p>'

    if not language:
        ext = os.path.splitext(path)[-1]
        if ext:
            ext = ext[1:]  # Remove a dot.
        for language in config['language']:
            if ext in config['language'][language]:
                break
        else:
            language = ''

    source = read_source(path)
    return fenced_code(source, language)


def fenced_code(source: str, language: str = '') -> str:
    begin = config_number['begin_pattern']
    end = config_number['end_pattern']
    cls = '.pheasant-fenced-code .pheasant-code'
    return f'{begin}\n~~~{language} {cls}\n{source}~~~\n{end}\n'
