"""This module processes inline code."""
import base64
import html
import io

from ..markdown.converter import markdown_convert
from .renderer import delete_style
from .config import config

# from ..number import config as config_number


def convert_inline(obj, **kwargs):
    # FIXME: how to determine the function for conversion.
    if hasattr(obj, '__module__'):
        module = obj.__module__
        if module.startswith('matplotlib.'):
            source = matplotlib_to_base64(obj, **kwargs)
        elif module.startswith('pandas.'):
            source = pandas_to_html(obj)
        elif module.startswith('bokeh.'):
            source = bokeh_to_html(obj)
        elif module.startswith('holoviews.'):
            source = holoviews_to_html(obj)
        else:
            source = f'Unknown module: {module}'
    else:
        is_str = isinstance(obj, str)
        if not is_str:
            obj = str(obj)

        if 'html' == kwargs.get('output'):
            source = markdown_convert(obj)
        elif is_str:
            source = obj
        else:
            source = html.escape(obj)

    return source

    # begin = config_number['begin_pattern']
    # end = config_number['end_pattern']
    # return f'{begin}{source}{end}'


def to_html(obj, **kwargs):
    return convert_inline(obj, output='html')


def to_markdown(obj, **kwargs):
    return convert_inline(obj, output='markdown')


def pandas_to_html(dataframe) -> str:
    """Convert a pandas.DataFrame into a <table> tag."""
    html = dataframe.to_html(escape=False)
    html = delete_style(html)
    return html


def bokeh_to_html(figure) -> str:
    """Convert a Bokeh's figure into <script> and <div> tags."""
    from bokeh.embed import components
    script, div = components(figure)
    return script + div


def matplotlib_to_base64(obj, output='markdown') -> str:
    """Convert a Matplotlib's figure into base64 string."""
    format = config['matplotlib_format']
    buf = io.BytesIO()

    if not hasattr(obj, 'savefig'):
        obj = obj.figure  # obj is axes.

    obj.savefig(buf, format=format, bbox_inches='tight', transparent=True)

    return base64image(buf, format, output)


def holoviews_to_html(figure, output='markdown') -> str:
    import holoviews as hv
    backend = config['holoviews_backend']
    format = config[f'{backend}_format']
    renderer = hv.renderer(backend)
    html, info = renderer(figure, fmt=format)

    if format == 'png':
        return base64image(html, format, output)
    else:
        return html


def base64image(buf, format, output):
    if isinstance(buf, bytes):
        source = buf
    else:
        buf.seek(0)
        source = buf.getvalue()

    data = base64.b64encode(source).decode('utf8')
    data = f'data:image/{format};base64,{data}'

    if output == 'markdown':
        return f'![{format}]({data})'
    elif output == 'html':
        return f'<img alt="{format}" src="{data}"/>'
