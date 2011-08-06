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
    """  si aggiornano quando si lancia la stampa del registro non importa lo azzera e lo ricalcola' """
    _columns = {
                'period_registro_id': fields.many2one('account.journal.period', 'Periodo Registro', required=True, select=True),
                'codice_iva':fields.many2one('account.tax', 'Codice Iva', required=True, readonly=False),
                'totale_imponibile': fields.float('Imponibile Periodo', help='Totale Imponibile del Periodo ', digits_compute=dp.get_precision('Account')),
                'totale_imposta': fields.float('Imposta del Periodo', help='Totale Imposta del Periodo ', digits_compute=dp.get_precision('Account')),
                }
    
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

    
                




