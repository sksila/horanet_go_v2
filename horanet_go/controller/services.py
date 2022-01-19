
from odoo import exceptions, http
from odoo.http import Controller, request

try:
    from odoo.addons.horanet_go.tools import git_source
    from odoo.addons.horanet_go import version
    from odoo.addons.horanet_web.tools import route
except ImportError:
    from horanet_go.tools import git_source
    from horanet_go import version
    from horanet_web.tools import route


class SourceVersion(Controller):
    @http.route(['/web/version'], type='http', auth="user", methods=['GET'], website=True)
    def page_module_version(self):
        if not request.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied()
        qcontext = {}

        horanet_go_module = request.env['ir.module.module'].search([('name', '=', 'horanet_go')])
        repo = git_source.get_module_git_repository(horanet_go_module)
        if repo:
            active_branch = repo.active_branch
            remote_branch = [b for b in repo.branches if b.path == repo.active_branch.path]
            remote_tag = [b for b in repo.tags if b.path == repo.active_branch.path]
            remote_branch = remote_branch[0] if remote_branch else None
            remote_tag = remote_tag[0] if remote_tag else None
            is_detached = False
            if remote_branch:
                is_detached = remote_branch.commit == active_branch.commit
            elif remote_tag:
                is_detached = remote_tag.commit == active_branch.commit

        qcontext.update({
            'version': version.__version__,
            'repo': {
                'active_branch': active_branch.name,
                'remote_branch': remote_branch and remote_branch.name or '',
                'remote_tag': remote_tag and remote_tag.name or '',
                'is_detached': is_detached,
                'status': repo.git.status(),
                'log': repo.git.log(max_count=100),
            }
        })
        return request.render('horanet_go.display_module_version', qcontext=qcontext)

    @route.jsonRoute(['/web/version/horanet'], auth='user', csrf=True)
    def horanet_version(self, **data):
        """
        Webservice JSON de récupération d'information sur le dépôt git d'horanet_go.

        :param data:
        :return: Dictionary with various informations about git repository
        """
        if not request.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied()
        horanet_go_module = request.env['ir.module.module'].search([('name', '=', 'horanet_go')])

        horanet_version = 'null'
        repo = git_source.get_module_git_repository(horanet_go_module)
        if repo:
            active_branch = repo.active_branch
            remote_branch = [b for b in repo.branches if b.path == repo.active_branch.path]
            remote_tag = [b for b in repo.tags if b.path == repo.active_branch.path]
            remote_branch = remote_branch[0] if remote_branch else None
            remote_tag = remote_tag[0] if remote_tag else None
            git_status = repo.git.status()
            git_log = repo.git.log(max_count=4)
            is_detached = False
            if remote_branch:
                is_detached = remote_branch.commit == active_branch.commit

            return {
                'version': str(horanet_version),
                'branch': repo.active_branch.name,
                'commit': repo.active_branch.commit.summary,
                'remote_tag': remote_tag,
                'git_status': git_status,
                'git_log': git_log,
                'is_detached': is_detached,

            }
        elif horanet_go_module:
            horanet_version = horanet_go_module.installed_version
        else:
            horanet_version = 'Impossible code to reach (using route on an uninstalled module ?!)'

        return {'version': str(horanet_version)}
