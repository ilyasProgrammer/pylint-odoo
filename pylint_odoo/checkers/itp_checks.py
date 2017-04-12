import io
import re
import ast
import os
import types
import astroid
from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker
from .. import misc, settings

ITP_ODOO_MSGS = {
    # C->convention R->refactor W->warning E->error F->fatal
    'E%d99' % settings.BASE_OMODULE_ID: (
        'Placeholder "%s" is not updated',
        'manifest-template-field',
        settings.DESC_DFLT
    ),
    'E%d98' % settings.BASE_OMODULE_ID: (
        'File doc/index.rst is absent in module',
        'absent-doc',
        settings.DESC_DFLT
    ),
    'E%d97' % settings.BASE_OMODULE_ID: (
        'File doc/changelog.rst is absent in module',
        'absent-changelog',
        settings.DESC_DFLT
    ),
    'E%d96' % settings.BASE_OMODULE_ID: (
        'Module has no manifest file',
        'absent-manifest',
        settings.DESC_DFLT
    ),
    'E%d95' % settings.BASE_OMODULE_ID: (
        'File: %s - Template placeholder "%s" is not updated',
        'rst-template-field',
        settings.DESC_DFLT
    ),
}
TEMPLATE_RE = '{[_ a-zA-Z0-9]*}'
TEMPLATE_FILES = ('README.rst', 'doc/index.rst', 'doc/changelog.rst')
MANIFEST_FILES = ('__openerp__.py', '__manifest__.py')


class ITPModuleChecker(misc.WrapperModuleChecker):
    __implements__ = IAstroidChecker

    name = 'itplynt'
    msgs = ITP_ODOO_MSGS

    @utils.check_messages(*(ITP_ODOO_MSGS.keys()))
    def visit_module(self, node):
        self.wrapper_visit_module(node)

    def visit_dict(self, node):
        if not os.path.basename(self.linter.current_file) in settings.MANIFEST_FILES \
                or not isinstance(node.parent, astroid.Discard):
            return
        manifest_dict = ast.literal_eval(node.as_string())

        # Check all template fields filled
        for k, v in manifest_dict.items():
            if isinstance(v, types.StringTypes):
                match = re.match(TEMPLATE_RE, v)
                if match:
                    self.add_message('manifest-template-field', node=node, args=v)

    def open(self):
        """Define variables to use cache"""
        self.inh_dup = {}
        super(ITPModuleChecker, self).open()

    def close(self):
        """Final process get all cached values and add messages"""
        for (odoo_node, class_dup_name), nodes in self.inh_dup.items():
            if len(nodes) == 1:
                continue
            path_nodes = []
            for node in nodes[1:]:
                relpath = os.path.relpath(node.file,
                                          os.path.dirname(odoo_node.file))
                path_nodes.append("%s:%d" % (relpath, node.lineno))
            self.add_message('consider-merging-classes-inherited',
                             node=nodes[0],
                             args=(class_dup_name, ', '.join(path_nodes)))

    def _check_absent_doc(self):
        return os.path.isfile(os.path.join(self.module_path, 'doc/index.rst'))

    def _check_absent_changelog(self):
        return os.path.isfile(os.path.join(self.module_path, 'doc/changelog.rst'))

    def _check_absent_manifest(self):
        self.msg_args = []
        self.got_manifest = False
        for manifest_file in MANIFEST_FILES:
            if os.path.isfile(os.path.join(self.module_path, manifest_file)):
                self.got_manifest = True
                return True
        self.msg_args.append('Module has no manifest file.')
        return False

    def _check_rst_template_field(self):
        rst_files = self.filter_files_ext('rst')
        self.msg_args = []
        for rst_file in rst_files:
            if rst_file in TEMPLATE_FILES:
                f = io.open(os.path.join(self.module_path, rst_file))
                content = f.read()
                f.close()
                match = re.findall(TEMPLATE_RE, content)
                if len(match):
                    for rec in match:
                        self.msg_args.append(("%s" % rst_file, rec))
        if self.msg_args:
            return False
        return True
