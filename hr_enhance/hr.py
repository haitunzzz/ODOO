#!/usr/bin/env python
#coding: utf8
# by zhangxue
# 
from openerp.osv import fields, osv
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

KPI_RATE = [
            ('1', 'Normal - 1'),
            ('2', 'Normal - 2'),
            ('3', 'Normal - 3'),
            ('4', 'Critical - 4'),
            ('5', 'Critical - 5'),
        ]

class hr_job(osv.osv):
    _inherit = "hr.job"
    
    _columns = {
        'kpi_rate': fields.selection(KPI_RATE, 'KPI Rate'),
        'kpi': fields.text('KPI'),
        'lines': fields.one2many('hr.evaluation.line','job_id','Staff KPI Targets'),
        }

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    def _days_of_service(self, cr, user, ids, name, arg, context=None):
        res = {}
        for hr in self.browse(cr, user, ids, context=context):
            res[hr.id] = (datetime.today() - datetime.strptime(hr.date_entry, '%Y-%m-%d')).days
        return res

    _columns = {
        'days_service': fields.function(
            _days_of_service,
            string='Days of Service',
            type='integer'),
        'date_entry': fields.date("Date of Entry"),
        'lines': fields.one2many('hr.evaluation.line','employee_id','Staff KPI Targets'),
        'pjob_id': fields.many2one('hr.job', 'Potential Positions'),
            }

    _defaults = {
        'date_entry': fields.date.context_today,
            }

    def onchange_job_id(self, cr, uid, ids, job_id, context=None):
        #vals =  super(hr_employee, self).onchange_job_id(cr, uid, ids, job_id, context=context)
        vals = {}
        vals['lines'] = []
        if job_id:
            job = self.pool.get('hr.job').browse(cr, uid, job_id, context=context)
            for line in job.lines:
                vals['lines'].append(line.id)
        return {'value': vals}

    ###########################   Send Email   ###############################
    def action_service_email(self, cr, uid, days, context=None):
        cr.execute("select id from hr_employee where parent_id is not null")
        ids = cr.fetchall()
        ids = [id[0] for id in ids] or []
        for em in self.browse(cr, uid, ids):
            if em.active and em.days_service in days and em.parent_id.work_email:
                #send email
                ir_model_data = self.pool.get('ir.model.data')
                try:
                    template_id = ir_model_data.get_object_reference(cr, uid, 'hr_enhance', 'email_template_hr_service')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    self.pool.get('email.template').send_mail(cr, uid, template_id, em.id, True)
        return True
    
class hr_expense_expense(osv.osv):
    _inherit = "hr.expense.expense"
    
    #Issue346
    def expense_confirm(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids):
            if expense.employee_id.parent_id and expense.employee_id.parent_id.work_email:
                #send email
                ir_model_data = self.pool.get('ir.model.data')
                try:
                    template_id = ir_model_data.get_object_reference(cr, uid, 'hr_enhance', 'email_template_hr_expense_expense_confirm')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    self.pool.get('email.template').send_mail(cr, uid, template_id, expense.id, True)
        return  super(hr_expense_expense, self).expense_confirm(cr, uid, ids, context=context)

    def expense_accept(self, cr, uid, ids, context=None):
        result = super(hr_expense_expense, self).expense_accept(cr, uid, ids, context=context)
        for expense in self.browse(cr, uid, ids):
                #send email
                ir_model_data = self.pool.get('ir.model.data')
                try:
                    template_id = ir_model_data.get_object_reference(cr, uid, 'hr_enhance', 'email_template_hr_expense_expense_approve')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    self.pool.get('email.template').send_mail(cr, uid, template_id, expense.id, True)
        return result

#Issue
class hr_evaluation(osv.osv):
    _inherit = "hr_evaluation.evaluation"
    _columns = {
        'lines': fields.one2many('hr.evaluation.line','evaluation_id','Staff KPI Targets'),
        'pjob_id': fields.related('employee_id', 'pjob_id', relation='hr.job', type='many2one', string='Potential Positions', readonly=True),
            }

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        vals =  super(hr_evaluation, self).onchange_employee_id(cr, uid, ids, employee_id, context=context)
        vals['lines'] = []
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
            for line in employee.lines:
                vals['lines'].append(line.id)
        return {'value': vals}

PERIOD = [
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly')
        ]

UNIT = [
            ('$', '$'),
            ('¥', '¥'),
            ('€', '€'),
            ('%', '%'),
            ('times', 'Times'),
            ('units', 'Units')
        ]

class hr_evaluation_line(osv.osv):
    _name = 'hr.evaluation.line'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'job_id': fields.many2one('hr.job', 'Job'),
        'evaluation_id': fields.many2one('hr_evaluation.evaluation', 'Appraisal Form'),
        'kpicateg_id': fields.many2one('kpi.category', 'KPI', required=True),
        'name': fields.char('Description', size=256, required=True),
        'period': fields.selection(PERIOD, 'Period'),
        'unit': fields.selection(UNIT, 'Unit'),
        'target': fields.float('Target'),
        'actual': fields.float('Actual'),
        'rate': fields.float('Rate'),
        'kpi_rate': fields.selection(KPI_RATE, 'KPI Rate'),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'hr.evaluation.line', context=c),
    }

    '''
    def create(self, cr, uid, vals, context=None):
        if vals.get('kpicateg_id'):
            categ = self.pool.get('kpi.category').browse(cr, uid, vals['kpicateg_id'], context=context)
            vals.update({

                })
        return super(hr_evaluation_line, self).create(cr, uid, vals, context=context)
    '''

    def onchange_kpicateg_id(self, cr, uid, ids, kpicateg_id, context=None):
        vals = {}
        if kpicateg_id:
            categ = self.pool.get('kpi.category').browse(cr, uid, kpicateg_id, context=context)
            for obj in self.browse(cr, uid ,ids, context=context):
                if not obj.name:
                    vals.update({'name': categ.ref})
                if not obj.period:
                    vals.update({'period': categ.period})
                if not obj.unit:
                    vals.update({'unit': categ.unit})
            if not ids:
                vals.update({
                    'name': categ.ref,
                    'period': categ.period,
                    'unit': categ.unit
                    })
        return {'value': vals}


class kpi_category(osv.osv):
    _name = "kpi.category"
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'ref': fields.char('Description',size=256),
        'period': fields.selection(PERIOD, 'Period'),
        'unit': fields.selection(UNIT, 'Unit'),
        'kpi_rate': fields.selection(KPI_RATE, 'KPI Rate'),
        'company_id': fields.many2one('res.company', 'Company'),
        }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'kpi.category', context=c),
    }

