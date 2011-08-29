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


class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
                'tipo_registro': fields.selection([('V', 'Vendite'),
                                                    ('A', 'Acquisti'),
                                                    ('C', 'Corrispettivi Scorp'),
                                                    ('CV', 'Corr.Ventilazione'),
                                                    ('G', 'Libro Giornale'),
                                                    ('N', 'Non FIscale')
                                                    ], 'Tipo Registro Iva', size=32, required=True,),
                'tipo_documento': fields.selection([('FA', 'Fattura'),
                                                    ('NC', 'Nota Credito'),
                                                    ('FC', 'Fattura Corr. Scorp./Ricevuta'),
                                                    ('FCEE', 'Fattura CEE'),
                                                    ('NCEE', 'Nota Credito CEE'),
                                                    ('N', 'No  Documenti')
                                                    ], 'Tipo Documento Iva', size=32, required=True,),
                'liquidazione': fields.boolean('Stampa Liquidazione', help="Registro su cui si stampa la Liquidazione"),
                'codice_ivar':fields.many2one('account.tax', 'Codice Iva Standard per il Registro', required=False, readonly=False),
                'partner_id': fields.many2one('res.partner', 'Partner', readonly=False, required=False),
                'conto_cassa_id':fields.many2one('account.account', 'Conto Cassa', readonly=False, required=False)
                                         }
                                         
account_journal()

class account_fiscalyear_iva_crediti(osv.osv):
    _name = 'account.fiscalyear.iva.crediti'
    _description = ' Utilizzi del credito iva di inizio anno'
    _columns = {
                'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True, select=True),
                'data_utilizzo':fields.date('Data Utilizzo', required=True),
                'tipo_utilizzo':fields.selection([
                                                  ('F24', 'Utilizzo in F24'),
                                                  ('IVA', 'Utilizzo in Liquidazione Iva')
                                                  ], "Tipo Utilizzo Iva", size=15, required=True),
                'importo_utilizzato': fields.float('Importo Utilizzato', digits_compute=dp.get_precision('Account')),
                }
    

account_fiscalyear_iva_crediti()

class progressivi_iva_period(osv.osv):
    _name = 'progressivi.iva.period'
    _description = ' Progressivi dei Registri Iva per periodo'
    
    def _get_id_juornal_period(self, cr, uid, journal_id, period_id):
            ids = self.pool.get('account.journal.period').search(cr, uid, [('journal_id', '=', journal_id), ('period_id', '=', period_id)])
            if ids:
                return ids[0]
            else:
                return False
                
    """  si aggiornano quando si lancia la stampa del registro non importa lo azzera e lo ricalcola' """
    _columns = {
                'period_registro_id': fields.many2one('account.journal.period', 'Periodo Registro', required=True, select=True),
                'codice_iva':fields.many2one('account.tax', 'Codice Iva', required=True, readonly=False),
                'totale_imponibile': fields.float('Imponibile Periodo', help='Totale Imponibile del Periodo ', digits_compute=dp.get_precision('Account')),
                'totale_imposta': fields.float('Imposta del Periodo', help='Totale Imposta del Periodo ', digits_compute=dp.get_precision('Account')),
                }
    
    def svuota(self, cr, uid, journal_id, period_id):
        ids = self._get_id_juornal_period(cr, uid, journal_id, period_id)
        if ids:
            ids_p = self.search(cr, uid, [('period_registro_id', '=', ids)])
            ok = self.unlink(cr, uid, ids_p)
        return True
    
    def aggiorna_prog(self, cr, uid, journal_id, period_id):
        self.svuota(cr, uid, journal_id, period_id)
        #import pdb;pdb.set_trace()
        id_perido_journal = self._get_id_juornal_period(cr, uid, journal_id, period_id)
        if id_perido_journal:
            ids_reg = self.pool.get('account.temp.regiva').search(cr, uid, [])
            if ids_reg:
                for riga_reg in self.pool.get('account.temp.regiva').browse(cr, uid, ids_reg):
                    prog_id = self.search(cr, uid, [('period_registro_id', '=', id_perido_journal), ('codice_iva', '=', riga_reg.codice_iva_riga_id.id)])
                    if prog_id:
                        riga_prog = self.browse(cr, uid, prog_id)[0]
                        riga = {
                               'period_registro_id': id_perido_journal,
                               'codice_iva':riga_reg.codice_iva_riga_id.id,
                               'totale_imponibile': riga_prog.totale_imponibile + riga_reg.base,
                               'totale_imposta': riga_prog.totale_imposta + riga_reg.amount,
                              }
                        ok = self.write(cr, uid, prog_id, riga)
                        
                    else:
                        riga = {
                               'period_registro_id': id_perido_journal,
                               'codice_iva':riga_reg.codice_iva_riga_id.id,
                               'totale_imponibile': riga_reg.base,
                               'totale_imposta':riga_reg.amount,
                              }
                        id_prog = self.create(cr, uid, riga)
            return True

    
progressivi_iva_period()


class account_journal_period(osv.osv):
    _inherit = 'account.journal.period'
    ''' Aggiunge sul periodo del registro l'ultima pagina per il libro giornale, l'ultima riga ed i progressivi del periodo e
     se registro iva si segna tutti i dati  progressivi per codice iva. Anche il calcolo della liquidazione si aggiorna automaticamente alla 
     stampa della liquidazione stessa
     
     '''
    _columns = {
               'tipo_registro': fields.related('journal_id', 'tipo_registro', string='Tipo Registro', type='selection', relation='account.journal'),
               'tipo_documento': fields.related('journal_id', 'tipo_documento', string='Tipo Documento', type='selection', relation='account.journal'),
               'ultima_pagina': fields.float('ultima pagina stampata', digits=(7, 0)),
               'ultima_riga_tipog':fields.float('ultima riga stampata', digits=(7, 0), help='Ultima riga Stampata sul libro Giornale'),
               'totale_dare': fields.float('Toatle Dare', help='Totale del Periodo Libro Giornale', digits_compute=dp.get_precision('Account')),
               'totale_avere': fields.float('Totale Avere', help='Totale del Periodo Libro Giornale', digits_compute=dp.get_precision('Account')),
               'data_ultima_riga': fields.date('Data ultima Riga', help='Data dell ultima riga stampata del periodo', required=False),
               'data_ultima_stampa': fields.date('Data ultima Riga', help='Data dell ultima stampa e quindi del calcolo dei progressivi del periodo', required=False),
               'data_versamento': fields.date('Data Versamento', help='Data dell eventuale versamento, solo sul registro di liquidazione', required=False),
               'banca_versamento':fields.many2one('res.partner.bank', 'Banca di Versamento', required=False, help="Banca del Azienda "),
               'importo_iva_credito': fields.float('Iva a Credito', help='Importo iva a Credito Calcolata nel periodo', digits_compute=dp.get_precision('Account')),
               'importo_iva_dovuta': fields.float('Iva a dovuta', help='Importo iva a Dovuta Calcolata nel periodo', digits_compute=dp.get_precision('Account')),
               'righe_progressivi_iva': fields.one2many('progressivi.iva.period', 'period_registro_id', 'Righe Progressivi Iva', required=True),
                }
    

    def _check(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            cr.execute('select * from account_move_line where journal_id=%s and period_id=%s limit 1', (obj.journal_id.id, obj.period_id.id))
            res = cr.fetchall()
            if res:
                pass # eliminato il controllo
              #  raise osv.except_osv(_('Error !'), _('You can not modify/delete a journal with entries for this period !'))
        return True
account_journal_period()



class account_fiscalyear_protocolli(osv.osv):
    _name = 'account.fiscalyear.protocolli'
    _description = ' Utilizzi del credito iva di inizio anno'
    _columns = {
                'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True, select=True),
                'registro': fields.many2one('account.journal', 'Registro Iva', required=True, select=True),
                'protocollo':fields.integer('Numero Protocollo ', required=False),
                'data_registrazione': fields.date('Data Registrazione', required=False,),
               }
    
    def check_sequence(self, cr, uid, data_reg, registro, protocollo, context=None):
        
        ok = True
        warning = ''
        #import pdb;pdb.set_trace()
        old_prot = self.get_prot(cr, uid, data_reg, registro)
        if old_prot['protocollo'] < protocollo and old_prot['data_registrazione'] > data_reg:
            # protocollo maggiore e data di registrazione inferiore all'ultimo protocollo inserito
            ok = False
            warning = 'Protocollo Maggiore e Data di Registrazione Inferiore all ultimo protocollo inserito'

           
        fiscalyear = self.get_fiscal_year(cr, uid, data_reg)
        fiscalyear_obj = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear)
        cerca = [('journal_id', '=', registro),
                 ('data_registrazione', '>=', fiscalyear_obj.date_start),
                 ('data_registrazione', '<=', fiscalyear_obj.date_stop),
                 ('protocollo', '=', protocollo)
                 ]
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, cerca)
        if invoice_ids:
            ok = False
            # protocollo protocollo esistente registrazione del 
            registrazione = self.pool.get('account.invoice').browse(cr, uid, invoice_ids)[0]
            warning = 'protocollo esistente alla registrazione ' + registrazione.name
        return {'ok':ok, 'warning':warning}
    
    def get_prot(self, cr, uid, data_reg, registro, context=None):
        #import pdb;pdb.set_trace() 
        fiscalyear = self.get_fiscal_year(cr, uid, data_reg)
        id_prot = self.search(cr, uid, [('fiscalyear_id', '=', fiscalyear), ('registro', '=', registro)])
        if id_prot:
            protocollo = { 
                         'protocollo':self.browse(cr, uid, id_prot)[0].protocollo,
                         'data_registrazione':self.browse(cr, uid, id_prot)[0].data_registrazione,
                         'id':id_prot[0],
                        }
        else:
            # non esiste un record del protocollo lo crea
            riga_prot = {
                         'fiscalyear_id':fiscalyear,
                         'registro':registro,
                         'protocollo':0,
                         'data_registrazione':data_reg,
                         }
            id = self.create(cr, uid, riga_prot)
            protocollo = { 
                         'protocollo':self.browse(cr, uid, id).protocollo,
                         'data_registrazione':self.browse(cr, uid, id).data_registrazione,
                         'id':id,
                        }
        return protocollo
    
    def get_fiscal_year(self, cr, uid, data_reg, context=None):
        #import pdb;pdb.set_trace() 
        period_id = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', data_reg), ('date_stop', '>=', data_reg)])[0]
        periodo = self.pool.get('account.period').browse(cr, uid, [period_id])[0]
        fiscalyear = periodo.fiscalyear_id.id

        return fiscalyear
    
    def agg_prot(self, cr, uid, data_reg, registro, protocollo, context=None):
        #import pdb;pdb.set_trace() 
        prot_list = self.get_prot(cr, uid, data_reg, registro, context)
        if prot_list['protocollo'] < protocollo and prot_list['data_registrazione'] <= data_reg:
            riga = {
                    'protocollo':protocollo,
                    'data_registrazione':data_reg,
                    }
            ok = self.write(cr, uid, [prot_list['id']], riga)
            
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        
         res = super(account_fiscalyear_protocolli, self).write(cr, uid, ids, vals, context=context)
         return res

account_fiscalyear_protocolli()




class account_fiscalyear(osv.osv):
    _inherit = "account.fiscalyear"
    _columns = {


                'tipo_liquidazione': fields.selection([('M', 'Mensile'),
                                                    ('T', 'Trimestrale'),
                                                 ], 'Tipo Registro Iva', size=15, required=True,),
                'plafond_iniziale': fields.float('Plafond Iva Inizio Anno', digits_compute=dp.get_precision('Account')),
                'plafond_residuo': fields.float('Plafond Iva Residuo', digits_compute=dp.get_precision('Account')),
                'credito_iva_iniziale': fields.float('Credito Iva Inizio Anno', digits_compute=dp.get_precision('Account')),
                'debito_iva_27': fields.float('Debito Iva Art.27-33', digits_compute=dp.get_precision('Account')),
                'percentuale_prorata': fields.float('Percentuale prorata', digits=(7, 3)),
                'maggiorazione_trimestrale': fields.float('% Maggiorrazione iva Trimestrale', digits=(7, 3)),
                'perc_acconto_iva': fields.float('% Acconto Iva', digits=(7, 3)),
                'acconto_iva': fields.float('Acconto iva di Dicembre', digits_compute=dp.get_precision('Account')),
                'versamento_minimo': fields.float('Versamento Minimo', digits_compute=dp.get_precision('Account')),
                'righe_utilizzi_crediti': fields.one2many('account.fiscalyear.iva.crediti', 'fiscalyear_id', 'Righe Utlizzi Crediti', required=False),
                'righe_protocolli': fields.one2many('account.fiscalyear.protocolli', 'fiscalyear_id', 'Ultimi Protocolli Registri', required=False),
                }

account_fiscalyear()            


class account_tax(osv.osv):
      _inherit = 'account.tax'
      _columns = {
                  'indetraibile':fields.boolean('flag iva indetraibile'),
                  }
      
    
account_tax()                




