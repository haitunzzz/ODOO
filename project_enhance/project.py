#Issue313
from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)
from openerp.tools import SUPERUSER_ID

class project(osv.osv):
    _inherit = "project.project"

    def _get_visibility_selection(self, cr, uid, context=None):
        """ Overriden in portal_project to offer more options """
        return [('public', 'All Users'),
                ('employees', 'Employees Only'),
                ('followers', 'Followers Only'),
                ('members', 'Team member only')]

    #Issue313
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        result = super(project, self).search(cr, uid, args, offset, limit=limit, order=order, context=context, count=count)
        #_logger.info('------- context %s args %s result %s order %s',context,args,result,order)
        if result and uid != SUPERUSER_ID:
            query = "select id from project_project \
                where privacy_visibility = 'members' and id in ("+ ','.join([str(i) for i in result])+") "
            cr.execute(query)
            projects = cr.fetchall()
            #_logger.info(' projects-- %s',projects)
            for p_id in projects:
                #_logger.info(' p_id-- %s',p_id)
                if uid not in [m.id for m in self.browse(cr, uid, p_id[0]).members]:
                    result.remove(p_id[0])
        return result

