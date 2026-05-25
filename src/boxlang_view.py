"""
BoxLang view context analysis.
Provides information about the current cursor position and context.
"""
import re
import sublime
from collections import defaultdict
from collections import namedtuple
from . import utils
from . import buffer_metadata
CompletionList = namedtuple('CompletionList', 'completions priority exclude_lower_priority')
Documentation = namedtuple('Documentation', 'doc_regions doc_html_variables on_navigate priority')
MethodPreview = namedtuple('MethodPreview', 'preview_regions preview_html_variables on_navigate priority')
CompletionDoc = namedtuple('CompletionDoc', 'doc_regions doc_html_variables on_navigate')
GotoBoxlangFile = namedtuple('GotoBoxlangFile', 'file_path symbol')

class BoxlangFunctionCallParams:
    """Parse function call parameters."""
    param_regex = re.compile('^(?:([\\w]+)\\s*=\\s*)?(.*)$', re.M | re.S)

    def __init__(self, boxlang_view, position):
        self.support = False
        self.method = False
        self.dot_context = None
        self.named_params = False
        self.current_index = None
        self.params = []
        self.function_name, self.function_region, self.params_region = boxlang_view.get_function_call(position)
        if 'support' in boxlang_view.view.scope_name(self.function_region.begin()).strip().split(' ')[-1]:
            self.support = True
        prev_pt = self.function_region.begin() - 1
        if boxlang_view.view.match_selector(prev_pt, 'source.boxlang punctuation.accessor.boxlang'):
            self.method = True
            self.dot_context = boxlang_view.dot_context = boxlang_view.get_dot_context(prev_pt)
        start_scope_list = boxlang_view.view.scope_name(self.params_region.begin()).strip().split(' ')[:-1]
        separator_scope = ' '.join(start_scope_list) + ' '
        last_key = start_scope_list[-2].replace('meta.', 'punctuation.separator.') + ' '
        for scope_name in ['entity.', 'createcomponent.', 'createjavaobject.']:
            last_key = last_key.replace(scope_name, '')
        separator_scope += last_key
        start = self.params_region.begin() + 1
        end = self.params_region.end() - 1  # exclude closing paren
        for pt in range(self.params_region.begin() + 1, self.params_region.end()):
            if pt == position:
                self.current_index = len(self.params)
            if boxlang_view.view.scope_name(pt) == separator_scope:
                current_element = boxlang_view.view.substr(sublime.Region(start, pt)).strip()
                param = re.match(BoxlangFunctionCallParams.param_regex, current_element)
                self.params.append(param.groups())
                start = pt + 1
        final_element = boxlang_view.view.substr(sublime.Region(start, end)).strip()
        if len(final_element) > 0 or start != self.params_region.begin() + 1:
            param = re.match(BoxlangFunctionCallParams.param_regex, final_element)
            self.params.append(param.groups())
        if len(self.params) > 0:
            self.named_params = self.params[0][0] is not None

    def __repr__(self):
        return repr((self.support, self.method, self.function_name, self.function_region, self.params_region, self.dot_context, self.named_params, self.current_index, self.params))

class BoxlangView:
    """Analyzes the current view context for completions and documentation."""

    def __init__(self, view, position, prefix=''):
        self.view = view
        self.prefix = prefix
        self.position = position
        self.function_call_params = None
        self.tag_name = None
        self.tag_attribute_name = None
        self.tag_in_script = False
        self.tag_location = None
        self._cache = defaultdict(dict)
        self.CompletionList = CompletionList
        self.Documentation = Documentation
        self.CompletionDoc = CompletionDoc
        self.MethodPreview = MethodPreview
        self.GotoBoxlangFile = GotoBoxlangFile
        self.prefix_start = self.position - len(self.prefix)
        self.determine_type()
        if self.type:
            self.set_base_info()
            self.view_metadata = buffer_metadata.get_cached_view_metadata(view)

    def set_base_info(self):
        """Set basic file information."""
        self.file_path = utils.normalize_path(self.view.file_name())
        self.file_name = self.file_path.split('/').pop().lower() if self.file_path else None
        self.project_name = utils.get_project_name(self.view)
        self.previous_char = self.view.substr(self.prefix_start - 1)

    def determine_type(self):
        """Determine the context type at the current position."""
        base_script_scope = 'source.boxlang'
        self.type = None
        if self.view.match_selector(self.prefix_start, 'embedding.boxlang.markup - source.boxlang'):
            self.type = 'tag'
            self.set_tag_info()
        elif self.view.match_selector(self.prefix_start - 1, base_script_scope + ' punctuation.accessor.boxlang'):
            self.type = 'dot'
            self.set_dot_context()
            self.function_call_params = self.get_function_call_params(self.position)
        elif self.view.match_selector(self.prefix_start, base_script_scope + ' meta.tag, ' + base_script_scope + ' meta.class.declaration'):
            self.type = 'tag_attributes'
            self.set_tag_info(True)
        elif self.view.match_selector(self.prefix_start, 'source.boxlang'):
            self.type = 'script'
            self.function_call_params = self.get_function_call_params(self.position)

    def set_dot_context(self):
        """Set the dot context at the current position."""
        self.dot_context = self.get_dot_context(self.prefix_start - 1)

    def set_tag_info(self, tag_in_script=False):
        """Set tag information."""
        self.tag_in_script = tag_in_script
        if self.view.match_selector(self.prefix_start, 'meta.tag - punctuation.definition.tag.begin, meta.class.declaration.boxlang'):
            if self.view.match_selector(self.prefix_start - 1, 'punctuation.definition.tag.begin, entity.name.tag'):
                self.tag_location = 'tag_name'
            elif self.view.match_selector(self.prefix_start, 'entity.other.attribute-name.boxlang'):
                self.tag_location = 'tag_attribute_name'
            else:
                self.tag_location = 'tag_attributes'
            if self.view.match_selector(self.prefix_start, 'source.boxlang meta.class.declaration'):
                self.tag_name = 'component'
            else:
                self.tag_name = utils.get_tag_name(self.view, self.prefix_start)
            if self.tag_in_script and (not self.tag_name.startswith('bx:')):
                self.tag_name = 'bx:' + self.tag_name if not self.tag_name.startswith('bx:') else self.tag_name
            if self.tag_location != 'tag_name':
                self.tag_attribute_name = utils.get_tag_attribute_name(self.view, self.prefix_start)
                self.type = 'tag_attributes'

    def get_dot_context(self, pt, cachable=True):
        """Get the dot context at the given point."""
        if not cachable or pt not in self._cache['get_dot_context']:
            self._cache['get_dot_context'][pt] = utils.get_dot_context(self.view, pt)
        return self._cache['get_dot_context'][pt]

    def get_struct_context(self, pt, cachable=True):
        """Get the struct context at the given point."""
        if not cachable or pt not in self._cache['get_struct_context']:
            self._cache['get_struct_context'][pt] = utils.get_struct_context(self.view, pt)
        return self._cache['get_struct_context'][pt]

    def get_struct_var_assignment(self, pt):
        """Get the struct variable assignment at the given point."""
        struct_context = self.get_struct_context(pt)
        variable_name = '.'.join([symbol.name for symbol in reversed(struct_context)])
        return variable_name

    def get_function(self, pt, cachable=True):
        """Get function info at the given point."""
        if not cachable or pt not in self._cache['get_function']:
            self._cache['get_function'][pt] = utils.get_function(self.view, pt)
        return self._cache['get_function'][pt]

    def get_function_call(self, pt, support=False, cachable=True):
        """Get function call info at the given point."""
        cache_key = (pt, support)
        if not cachable or cache_key not in self._cache['get_function_call']:
            self._cache['get_function_call'][cache_key] = utils.get_function_call(self.view, pt, support)
        return self._cache['get_function_call'][cache_key]

    def get_function_call_params(self, pt):
        """Get function call parameters at the given point."""
        if self.view.match_selector(pt, 'source.boxlang meta.function-call.arguments'):
            return BoxlangFunctionCallParams(self, pt)
        return None

    def get_string_metadata(self, file_string):
        """Parse metadata from a file string."""
        return buffer_metadata.parse_bx_file_string(file_string)

    def find_variable_assignment(self, position, variable_name, cachable=True):
        """Find a variable assignment before the given position."""
        cache_key = (position, variable_name)
        if not cachable or cache_key not in self._cache['find_variable_assignment']:
            var_assignment = utils.find_variable_assignment(self.view, position, variable_name)
            self._cache['find_variable_assignment'][cache_key] = var_assignment
        return self._cache['find_variable_assignment'][cache_key]