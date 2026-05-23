"""
MiniHTML utilities for syntax-aware HTML generation.
"""
import sublime

def get_selector_style_map(view, selectors):
    """Get a map of selector to style for the current view."""
    styles_by_selector = {}
    for selector in selectors:
        scope_name = view.scope_name(0)
        if selector in scope_name:
            styles_by_selector[selector] = {}
    return styles_by_selector

def generate_style_html(view, selectors):
    """Generate CSS style HTML for the given selectors."""
    css = []
    for selector in selectors:
        scope_regions = view.find_by_selector(selector)
        if scope_regions:
            scope_name = view.scope_name(scope_regions[0].begin())
            styles = view.style_for_scope(scope_name)
            css_parts = []
            if 'foreground' in styles:
                css_parts.append('color: {}'.format(styles['foreground']))
            if styles.get('italic'):
                css_parts.append('font-style: italic')
            if styles.get('bold'):
                css_parts.append('font-weight: bold')
            if css_parts:
                css.append('.{} {{ {}; }}'.format(selector.replace('.', '_'), '; '.join(css_parts)))
    return '\n'.join(css)