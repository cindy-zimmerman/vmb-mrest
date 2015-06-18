__author__ = 'cz'

from flask import request, redirect, url_for, flash, current_app, abort, render_template
from vmb_db.contact_info import get_contact, get_contact_by_casillero, iter_pages
from vmb_db.invoice_info import get_invoice_list_by_casillero, INVOICES_PER_PAGE


# @login_required
# def viewTransaction(tid):
#     t = getTransaction(tid, current_app.coinapultContext)
#     return render_template('transactions/view.html', trans=t)

# @login_required
def viewClient(cid):
    print cid
    client = get_contact_by_casillero(casillero=cid)
    invoices = get_invoice_list_by_casillero(casillero=cid)
    for i in invoices:
        print i
    invoices = get_invoice_list_by_casillero(casillero=cid)

    return render_template('clients/view.html', client=client, ilist=invoices)
