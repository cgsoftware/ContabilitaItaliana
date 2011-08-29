# -*- encoding: utf-8 -*-

import wizard
import decimal_precision as dp
import pooler
import time
from tools.translate import _
from osv import osv, fields
from tools.translate import _
import netsvc


class stampa_registri_iva(osv.osv_memory):
    _name = 'stampa.registri.iva'
    _description = 'funzioni stampa ordini jasper'
    _columns = {
                'data_stampa': fields.date('Data Stampa', required=True),
                'journal_id': fields.many2one('account.journal', 'Registro Iva', required=True),
                'period_id': fields.many2one('account.period', 'Periodo di Stampa', required=True),
                'ultima_pagina':fields.integer('Ultima Pagina Stampata', required=True),
    }
    _defaults = {
               'data_stampa': lambda * a: time.strftime('%Y-%m-%d'),
               }
    
    def _build_contexts(self, cr, uid, ids, data, context=None):
        #import pdb;pdb.set_trace()
        if context is None:
            context = {}
        result = {}
        result = {'dadata':data['form']['dadata'], 'adata':data['form']['adata'],
                  'order_method':data['form']['ord']}
        return result
    
    def ultima_pagina(self, cr, uid, ids, journal_id=False, period_id=False):
        ultima_pagina = 0
        if journal_id and period_id:
            if period_id:
               #import pdb;pdb.set_trace() 
               ids = self.pool.get('account.journal.period').search(cr, uid, [('journal_id', '=', journal_id), ('period_id', '=', period_id)])
               if ids:
                period_obj = self.pool.get("account.period")
                code = self.pool.get('account.journal.period').browse(cr, uid, ids)[0].period_id.code.split('/')
                nper = int(code[0])
                if nper - 1 <> 0:
                    mese = str(nper - 1).zfill(2)                
                    new_code = mese + '/' + code[1]
                    period_ids = period_obj.search(cr, uid, [('code', '=', new_code)])
                    if period_ids:
                        ids = self.pool.get('account.journal.period').search(cr, uid, [('journal_id', '=', journal_id), ('period_id', '=', period_ids[0])])
                        if ids:
                            ultima_pagina = self.pool.get('account.journal.period').browse(cr, uid, ids)[0].ultima_pagina      
        return { 'value':{
                          'ultima_pagina' : ultima_pagina,
                        }
                    }
        
    def creaEstampa(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
            
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        #data['form'] = self.read(cr, uid, ids, ['dadata', 'adata', 'ord'])[0]
        #used_context = self._build_contexts(cr, uid, ids, data, context=context)
        #data['form']['parameters'] = used_context
         
        param = self.browse(cr, uid, ids)[0]
        temp = self.pool.get('account.temp.regiva').crea_temp(cr, uid, param.period_id.id, param.journal_id.id)
        if temp: # sono stati creati i due temporanei ora è possibile stampare.
            
            pass 
            # lancia la stampa e ritorna il numero di pagina  che deve essere salvato
            # context = context.copy()
            context = {'return_pages': True}
            report_name = "RegistroIVA"
            report = netsvc.LocalService('report.%s' % report_name)
            result, format, pages = report.create(cr, uid, ids, data, context)
        #{'type': 'ir.actions.act_window_close'}
        import pdb;pdb.set_trace()
        return  {'type': 'ir.actions.report.xml',
                    'report_name': report_name,
                    'datas': data,
 
                    }
  
    def _print_report(self, cr, uid, ids, data, context=None):
        #import pdb;pdb.set_trace()
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        effetti = pool.get('effetti')
        active_ids = context and context.get('active_ids', [])
        Primo = True
        var = data['form']['ord']
        if var == 'D':

            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'DistinteData',
                    'datas': data,
                   }
        else:
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'Distinte',
                    'datas': data,
                    }
 



    
stampa_registri_iva()  

