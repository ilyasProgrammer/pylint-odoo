import ast
import os
import types
import astroid
from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker
from .. import settings

ITP_CHECK_PREFIX_ID = 77
ITP_ODOO_MSGS = {
    # C->convention R->refactor W->warning E->error F->fatal
    'E%d01' % ITP_CHECK_PREFIX_ID: (
        'Necessary manifest field "%s" got wrong value "%s"',
        'skipped-field',
        settings.DESC_DFLT
    ),
}


class ITPModuleChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = settings.CFG_SECTION
    msgs = ITP_ODOO_MSGS

    def visit_dict(self, node):
        if not os.path.basename(self.linter.current_file) in settings.MANIFEST_FILES \
                or not isinstance(node.parent, astroid.Discard):
            return
        manifest_dict = ast.literal_eval(node.as_string())

        # Check all template fields filled
        for k, v in manifest_dict.items():
            if isinstance(v, types.StringTypes):
                if '{' in v or '}' in v:
                    self.add_message('skipped-field', node=node, args=(k, v))
