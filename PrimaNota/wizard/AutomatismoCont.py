# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import netsvc
import pooler
from osv import fields, osv
import decimal_precision as dp
from tools.translate import _




class account_automatismo_cont(osv.osv_memory):
    _name = "account.automatismo.cont"
    _columns = {
                'name': fields.char('Descrizione Operazione', size=64, required=True),
                }
    
    def scrivi(self, cr, uid, ids, context):
        result = {}
        pass
        # legge i dati di automatismo crea la registrazione
               
        return  {'type': 'ir.actions.act_window_close'}
    
    
    def action_call_wizard(self, cr, uid, ids, modello_id, ref, journal_id, period_id, date, context=None):
        if context is None: context = {}
        if modello_id:
               modello = self.pool.get('account.model').browse(cr, uid, [modello_id])[0]

        wizard_id = self.pool.get("account.automatismo.cont").create(
            cr, uid, {'name':modello.name}, context=dict(context, active_ids=ids))
        #import pdb;pdb.set_trace()
        return {
            'name':_("Automatismo Registrazione"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.automatismo.cont',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': dict(context, active_ids=ids)
        }
    
account_automatismo_cont()

