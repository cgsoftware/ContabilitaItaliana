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
{
    'name': 'Verticalizzazione C & G Software',
    'version': '1.0',
    'category': 'Generic Modules/Base',
    'description': """
     Modifche Specifiche per la gestione della Contabilità
    """,
    'author': 'C & G Software',
    "depends" : ['base', 'account'],
    "update_xml" : ['base_partner_sequence/partner_sequence.xml',
   'ItalianFiscalDocument/wizard/GeneraFattDifferite.xml',
 'ItalianFiscalDocument/wizard/StampaDoc.xml',
 'ItalianFiscalDocument/wizard/EvadiOrdini.xml', 
'ItalianFiscalDocument/FiscalDocument_view.xml',
 'ItalianFiscalDocument/FiscalDocumentAccessori_view.xml',
                    'ItalianFiscalDocument/security/ir.model.access.csv',
'product_change_percent_price/product_change_price.xml',
                    ],
    'website': 'http://www.cgsoftware.it',
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: