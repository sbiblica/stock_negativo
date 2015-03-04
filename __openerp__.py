# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    realizado por Miguel Chuga -- miguelchuga@gmail.com
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
'name' : "Stock Negativo",
'category' : "Test",
'version' : "1.0",
'depends' : ['base','point_of_sale'],
'author' : "Miguel Chuga",
'description' : """\
Desarrollo personalizado para control del stock negativo en el puno de venta:
- Calendario de programacion TV""",
'data' : ["point_of_sale_view.xml"],
}
