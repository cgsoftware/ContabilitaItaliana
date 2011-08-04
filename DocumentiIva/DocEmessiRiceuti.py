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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import netsvc
import pooler
from osv import fields, osv
import decimal_precision as dp
from tools.translate import _




class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    _columns = {
                 'codice_iva_riga_id': fields.many2one('account.tax', "Codice Iva"),
                 'raggruppato':fields.boolean('Riga che ha sostituito + righe dello stesso conto')
                 }
    
    def conto_change(self, cr, uid, ids, name, parent_name):
        result = {}
        if not name:
            result = {'value':{'name':parent_name}}
        return result
            
    
    def codice_iva_change(self, cr, uid, ids, codice_iva_riga_id, invoice_line_tax_id):
        #import pdb;pdb.set_trace() 
        result = {'value':{'invoice_line_tax_id':[codice_iva_riga_id]}}
        
        return result

 

account_invoice_line()

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
                'data_registrazione': fields.date('Data Registrazione', required=True, states={'open':[('readonly', True)]}, select=True),
                'protocollo':fields.integer('Numero Protocollo ', required=True),
                'tipo_registro': fields.related('journal_id', 'tipo_registro', string='Tipo Registro', type='char', relation='account.journal'),
                'tipo_documento': fields.related('journal_id', 'tipo_documento', string='Tipo Documento', type='char', relation='account.journal'),
                'codice_ivar': fields.related('journal_id', 'codice_ivar', string='Codice Iva Standard', type='many2one', relation='account.journal'),
                'default_credit_account_id': fields.related('journal_id', 'default_credit_account_id', string='Conto Ricavi Standard', type='integer', relation='account.journal'),
                'default_debit_account_id': fields.related('journal_id', 'default_debit_account_id', string='Conto Costo Standard', type='integer', relation='account.journal'),
     }
    
    def _get_protocollo(self, cr, uid, context=None):
        if context is None:
            context = {}
        return 1
    
    def check_tax_lines(self, cr, uid, inv, compute_taxes, ait_obj):
        if not inv.tax_line:
            for tax in compute_taxes.values():
                ait_obj.create(cr, uid, tax)
        else:
            tax_key = []
            for tax in inv.tax_line:
                if tax.manual:
                    continue
                key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id)
                tax_key.append(key)
                if not key in compute_taxes:
                    raise osv.except_osv(_('Warning !'), _('Global taxes defined, but are not in invoice lines !'))
                base = compute_taxes[key]['base']
                if abs(base - tax.base) > inv.company_id.currency_id.rounding:
                    raise osv.except_osv(_('Warning !'), _('Tax base different !\nClick on compute to update tax base'))
            for key in compute_taxes:
                if not key in tax_key:
                    pass
                   # raise osv.except_osv(_('Warning !'), _('Taxes missing !'))

    def onchange_journal_id(self, cr, uid, ids, journal_id=False):
       result = {}
       result = super(account_invoice, self).onchange_journal_id(cr, uid, ids, journal_id)
       
       if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            # currency_id = journal.currency and journal.currency.id or journal.company_id.currency_id.id standard 
            result['value'].update({
                                 # 'protocollo' : journal.protocollo, ## deve essere preso dao dati annuali account.fiscalyear.protocolli
                                 'tipo_registro' : journal.tipo_registro,
                                 'tipo_documento' : journal.tipo_documento,
                                 'codice_ivar' : journal.codice_ivar.id,
                                 'default_credit_account_id' : journal.default_credit_account_id.id,
                                 'default_debit_account_id' : journal.default_debit_account_id.id,
                    
                    })
                
     #period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', inv.date_invoice or time.strftime('%Y-%m-%d')),                                                               ('date_stop', '>=', inv.date_invoice or time.strftime('%Y-%m-%d')), ('company_id', '=', inv.company_id.id)])
       #import pdb;pdb.set_trace() 
       return result
   
    def  date_invoice_change(self, cr, uid, ids, journal_id, company_id, data_registrazione, partner_id, type, reference):
        # import pdb;pdb.set_trace() 
        result = {}
        period_id = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', data_registrazione), ('date_stop', '>=', data_registrazione), ('company_id', '=', company_id)])[0]
        periodo = self.pool.get('account.period').browse(cr, uid, [period_id])[0]
        fiscalyear = periodo.fiscalyear_id
        protocollo_ids = self.pool.get('account.fiscalyear.protocolli').search(cr, uid, [('fiscalyear_id', '=', fiscalyear.id),
                                                                                        ('registro', '=', journal_id)                                                                                       
                                                                                        ])
        if protocollo_ids:
            protocollo = self.pool.get('account.fiscalyear.protocolli').browse(cr, uid, protocollo_ids)[0].protocollo
        else:
            proto = {
                     'fiscalyear_id':fiscalyear.id,
                     'registro':journal_id,
                                          }
            id_proto = self.pool.get('account.fiscalyear.protocolli').create(cr, uid, proto)
            protocollo = 0
         
        result = {'value':{
                                 # 'protocollo' : journal.protocollo, ## deve essere preso dao dati annuali account.fiscalyear.protocolli
                                 'period_id' : periodo.id,
                                 'protocollo':protocollo + 1,
                        }
                    }
        #import pdb;pdb.set_trace()
        registro = self.pool.get('account.journal').browse(cr, uid, [journal_id])[0]
        if partner_id:
            if 'invoice' in type:
                    Descrizione = "Fat. N. " + reference + " " + self.pool.get('res.partner').browse(cr, uid, [partner_id])[0].name
            else:
                    Descrizione = "Nota Credito N. " + reference + " " + self.pool.get('res.partner').browse(cr, uid, [partner_id])[0].name
            
            # c'è già il partner ora prepara lo scheletro della registrazione di  prima nota
            partner_auto_ids = self.pool.get("account.partner_autominvoice").search(cr, uid, [("partner_id", "=", partner_id), ('type', "=", type)])
            if partner_auto_ids:
                # c'è un automatismo personalizzato
                righe = []
                for riga in self.pool.get("account.partner_autominvoice").browse(cr, uid, partner_auto_ids):
                    righe.append({
                          "product_id":None,
                          "account_id":riga.account_id.id,
                          "account_analytic_id":None,
                          "quantity":1,
                          "price_unit":0.0,
                          "price_subtotal":0.0,
                          "name":Descrizione , # qui dovresti creare una decrizione del documento
                          "uos_id":None,
                          'invoice_line_tax_id':[riga.codice_iva.id],
                          'codice_iva_riga_id':registro.codice_ivar.id,
                          } 
                                 )

            else:
                #prende gli standard del registro assegnato
                righe = [{
                          "product_id":None,
                          "account_id":registro.default_credit_account_id.id,
                          "account_analytic_id":None,
                          "quantity":1,
                          "price_unit":0.0,
                          "price_subtotal":0.0,
                          "name":Descrizione , # qui dovresti creare una decrizione del documento
                          "uos_id":None,
                          'invoice_line_tax_id':[registro.codice_ivar.id],
                          'codice_iva_riga_id':registro.codice_ivar.id,
                          }]
            if result:
                    result['value'].update({
                                            "name":Descrizione ,
                                            "invoice_line":righe,
                                            })
            else:
                    result = {'value':{"name":Descrizione , "invoice_line":righe, }}
            
        return  result   
    



    def button_reset_taxes(self, cr, uid, ids, context=None):
        # prima di ricalcolare l'iva verifica che non ci siano righe raggruppate che non abbiano
        # codice iva altrimenti non fa il calcolare l'automatico e setta tutte le righe iva in manuale 
        # mandando un messaggio ( il codice iva se la riga è raggruppata è readonly)
        # poi verifca che invece non ci siano righe raggruppabili, cioè che che hanno lo stesso conto se è così
        # cancella quelle righe ricreandone dellle nuove poi se è il caso fa il calcolo standard
        # import pdb;pdb.set_trace() 
        if context is None:
            context = {}
        ctx = context.copy()
        righe_obj = self.pool.get('account.invoice')
        if not  righe_obj.browse(cr, uid, ids)[0].tax_line:
            # è la prima volta che ci entra e quindi lancia il calcolo brutale
            superiore = super(account_invoice, self).button_reset_taxes(cr, uid, ids, context=None)
        for id in ids: # ciclo sulle varie fatture ma è solo una comunque 
               no_calc = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', '=', id), ('raggruppato', '=', 'true')])
               if no_calc:
                    #import pdb;pdb.set_trace()
                    for tax_line in self.pool.get('account.invoice.line').browse(cr, uid, no_calc):
                        if len(tax_line.invoice_line_tax_id) > 1 or len(tax_line.invoice_line_tax_id) == 0:
                            raise osv.except_osv(_('Errore !'),
                                             _('Ci sono righe per cui non è possibile il ricalcolo Procedere Manualmente'))
                            break
                        else:
                            superiore = super(account_invoice, self).button_reset_taxes(cr, uid, ids, context=None)
                
               # ora invece verifica se è possibile raggruppare qualcosa 
               fatt_rec = self.browse(cr, uid, [id])[0]
               lista_gr = {}
               for rig in fatt_rec.invoice_line:
                   lista_conto = lista_gr.get(rig.account_id.id, []) # prende la lista degli id del conto interessato
                   lista_conto.append(rig.id)
                   lista_gr[rig.account_id.id] = lista_conto
                   
               if len(lista_gr) <> len(fatt_rec.invoice_line):
                    #le due liste generate sono diverse quindi ora ciclo per quelle righe che hanno una lista >1 e raggruppo
                    
                    for riga_conto in lista_gr.items():
                        if len(riga_conto[1]) > 1:
                            # questa è la riga da raggruppare
                            totale_importo = 0
                            codici_iva = {}
                            #import pdb;pdb.set_trace() 
                            for rr in self.pool.get('account.invoice.line').browse(cr, uid, riga_conto[1]):
                                # SOMMA IL TOTALE IMPORTO E CREA UNA LISTA DI CODICI_IVA CHE SE MAGGIORE DI DUE NON CALCOLERÀ
                                # I DATI IVA
                                totale_importo += rr.price_unit
                                codici_iva[rr.codice_iva_riga_id.id] = rr.codice_iva_riga_id.id
                            if len(codici_iva) > 1:
                                # le aliquote iva sono + di una
                                cod_iva = None
                                # mette in mauale tutte le righe iva in modo amnuale che non si possano fare casini
                                righe_iva = self.pool.get('account.invoice.tax').search(cr, uid, [('invoice_id', "=", id)])
                                ok = self.pool.get('account.invoice.tax').write(cr, uid, righe_iva, {'manual':True})
                            else:
                                cod_iva = codici_iva.values()[0]
                            if cod_iva:
                                codiva = [(6, 0, [cod_iva])]
                            else:
                                codiva = [(6, 0, [])]
                            riga_corr = self.pool.get('account.invoice.line').browse(cr, uid, riga_conto[1])[0]
                            import pdb;pdb.set_trace()
                            new_riga = {
                                        'name':riga_corr.name,
                                        'invoice_id':riga_corr.invoice_id.id,
                                        'codice_iva_riga_id':cod_iva,
                                        'uos_id':riga_corr.uos_id.id,
                                        'raggruppato':True,
                                        'product_id':riga_corr.product_id.id,
                                        'account_id':riga_corr.account_id.id,
                                        'price_unit':totale_importo,
                                        'price_subtotal':totale_importo,
                                        'quantity':riga_corr.quantity,
                                        'discount':riga_corr.discount,
                                        'note':riga_corr.note,
                                        'account_analytic_id':riga_corr.account_analytic_id.id,
                                        'company_id':riga_corr.company_id.id,
                                        'partner_id':riga_corr.partner_id.id,
                                        'invoice_line_tax_id':codiva,
                                        }
                            id_new = self.pool.get('account.invoice.line').create(cr, uid, new_riga)
                            ok = self.pool.get('account.invoice.line').unlink(cr, uid, riga_conto[1])
               # lancia il ricalcolo che se manale non avrà effetto e nei giri successivi non sarà effettuato
               #superiore = super(account_invoice, self).button_reset_taxes(cr, uid, ids, context=None)         

        
        return True    
      
    _defaults = {
                 'data_registrazione': lambda * a: time.strftime('%Y-%m-%d'),
                 # 'protocollo':_get_protocollo,
                 }
    

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, \
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False, journal_id=False):

        #import pdb;pdb.set_trace() 
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,
            date_invoice, payment_term, partner_bank_id, company_id)
        
        result['value']['date_due'] = False
        partner = self.pool.get('res.partner').browse(cr, uid, [partner_id])[0]
        if partner.autom_invoice_ids: # ci sono degli automatismi anche se non sappiamo per questo registro
                pass
        else:
               pass
        return result
     

        
account_invoice()        


class account_partner_autominvoice(osv.osv):
    _name = "account.partner_autominvoice"
    _description = 'Conti Automatici da Presentare in Prima Nota'
    _columns = {
                'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, required=True,),
                'type': fields.selection([
                                          ('out_invoice', 'Customer Invoice'),
                                          ('in_invoice', 'Supplier Invoice'),
                                          ('out_refund', 'Customer Refund'),
                                          ('in_refund', 'Supplier Refund'),
                                          ], 'Type', readonly=False,),

                'sequence':fields.integer('Sequanza ', required=True),
                'account_id': fields.many2one('account.account', 'Account', required=True, domain=[('type', '<>', 'view'), ('type', '<>', 'closed')], help="Conto di Costo o di Ricavo a seconda dei casi"),
                'codice_iva':fields.many2one('account.tax', 'Codice Iva', required=False, readonly=False),
                }


    
account_partner_autominvoice()


class res_partner(osv.osv):
    """ Inherits partner and adds invoice information in the partner form """
    _inherit = 'res.partner'
    _columns = {
        'autom_invoice_ids': fields.one2many('account.partner_autominvoice', 'partner_id', 'Automatismi Documenti Contabili', readonly=False),
    }

res_partner()






