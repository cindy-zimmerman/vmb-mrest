__author__ = 'cz'
import os
import math
from vmb_db.conn import get_one

from flask import request, redirect, url_for, flash, current_app, abort, render_template
from flask.ext.login import login_required
from werkzeug import secure_filename

from vmb_db.contact_info import get_contact, get_contact_by_casillero, set_contact_by_casillero, iter_pages
from vmb_db.invoice_info import get_invoice_list, set_inv_panama_by_guia, INVOICES_PER_PAGE
from vmb_db.upLoadZoom import accounts
from vmb_db.conf import getModule
configVMB = getModule('config')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in configVMB.ALLOWED_EXTENSIONS

@login_required
def viewInvoice():
    page = int(request.args.get('page', '1'))
    if request.method.lower() == 'post':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(configVMB.UPLOAD_FOLDER, filename))
            fileFullName = '%s/%s' % (configVMB.UPLOAD_FOLDER, filename)
            uploaded = accounts(fileFullName=fileFullName)
            if uploaded > 0:
                uploadedMes = 'The file was uploaded. %s rows were processed' % (uploaded)
                flash(uploadedMes)

            else:
                flash('There was a problem with uploading the file')
    client = {'casillero' : 0}
    sort = 'fecha_proceso DESC, hora_proceso DESC'
    invoices = get_invoice_list(where=None, sort=sort, limit=INVOICES_PER_PAGE, skip=(page - 1) * INVOICES_PER_PAGE)
    n = get_one(query='SELECT COUNT(*) AS count FROM VMB.INVOICES')
    count = int(n['count'])

    numpages = int(math.ceil(count / float(INVOICES_PER_PAGE)))

    return render_template('invoices/view.html', client=client, ilist=invoices,
                               tcount=count, tnumpages=numpages, tpage=page,
                               pagination=iter_pages)

@login_required
def packageArrived():
    print 'packageArrived'
    if request.method.lower() == 'post':
        guia = request.form.get('update', '').strip()
        set_inv_panama_by_guia(guia)
    return redirect(url_for('viewInvoice'))
