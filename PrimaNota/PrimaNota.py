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




class account_move(osv.osv):
    _inherit = "account.move"
    _columns = {
                'modello_id': fields.many2one('account.model', 'Causale ', required=False),
                }
    
    def change_model(self, cr, uid, ids, modello_id, line_id, date, period_id):
        
        #import pdb;pdb.set_trace()
        result = {}
        if not line_id: # se esistono già righe l'automatismo non scatta
            if modello_id:
               modello = self.pool.get('account.model').browse(cr, uid, [modello_id])[0]
               righe = []
               for riga in modello.lines_id:
                   righe.append({
                                 'date':date,
                                 'period_id':period_id,
                                 'ref': modello.name,
                                 'journal_id':modello.journal_id.id,
                                 'move_id':False,
                                 'invioce':False,
                                 'partner_id':False,
                                 'name':modello.name,
                                 'account_id':riga.account_id.id,
                                })
               result = {'value':{
                                
                                 'ref' : modello.name,
                                 'journal_id':modello.journal_id.id,
                                 'line_id':righe,
                        }
                    }
               
        return result
    

    
    
 
  
    
    
    
    
account_move()

