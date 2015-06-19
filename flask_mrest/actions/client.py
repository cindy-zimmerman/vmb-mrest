__author__ = 'cz'

from flask import request, redirect, url_for, flash, current_app, abort, render_template
from vmb_db.contact_info import get_contact, get_contact_by_casillero, set_contact_by_casillero, iter_pages
from vmb_db.invoice_info import get_invoice_list_by_casillero, set_inv_by_guia, INVOICES_PER_PAGE


# @login_required
def viewClient(cid):
    if request.method.lower() == 'post':
        guia = int(request.form.get('update', '').strip())
        amt = request.form.get('amt', '').strip()
        subtotal = request.form.get('subtotal', '').strip()
        try:
            amt = float(amt)
            subtotal = float(subtotal)
            paid = 0
            if amt >= subtotal:
                paid = 1
            set_inv_by_guia(guia, paid, amt)
        except:
            flash('El numero de paga que ha introducido no es valido')
    client = get_contact_by_casillero(casillero=cid)
    invoices = get_invoice_list_by_casillero(casillero=cid)
    for i in invoices:
        print i
    invoices = get_invoice_list_by_casillero(casillero=cid)

    return render_template('clients/view.html', client=client, ilist=invoices)


# @login_required
# @roles_permitted('support')
def editClient(cid):
    client = get_contact_by_casillero(casillero=cid)
    actItems = {'FT': True, 'telefonofij': False, 'telefonocel': False, 'tarifa': False}

    if not client:
        flash('User %s not found' % cid, 'error')
        # return redirect(url_for('searchCustomers'))
        return redirect(url_for('/'))

    if request.method.lower() == 'post':
        actItems['FT'] = False
        client['contacto_nombre_1'] = request.form.get('contacto_nombre_1', '').strip()
        print client['contacto_nombre_1']
        client['contacto_nombre_2'] = request.form.get('contacto_nombre_2', '').strip()
        client['contacto_apellido_1'] = request.form.get('contacto_apellido_1', '').strip()
        client['contacto_apellido_2'] = request.form.get('contacto_apellido_2', '').strip()
        client['correo'] = request.form.get('correo', '').strip()
        client['direccion_calle'] = request.form.get('direccion_calle', '').strip()
        client['direccion_torre'] = request.form.get('direccion_torre', '').strip()
        client['direccion_apt'] = request.form.get('direccion_apt', '').strip()
        client['direccion_area'] = request.form.get('direccion_area', '').strip()
        client['ciudad'] = request.form.get('ciudad', '').strip()

        client['telefonofij'] = request.form.get('telefonofij', '').strip()
        client['telefonocel'] = request.form.get('telefonocel', '').strip()
        if request.form.get('tarifa', None):
            try:
                 client['tarifa'] = float(request.form.get('tarifa', 0))
            except:
                flash('El numero de tarifa que ha introducido no es valido')
                actItems['tarifa'] = True
                actItems['FT'] = True


        try:
            client['telefonofij'] = int(client['telefonofij'])
            client['telefonocel'] = int(client['telefonocel'])
        except:
            flash('El numero de telefono que ha introducido no es valido')
            actItems['telefonofij'] = True
            actItems['FT'] = True

        try:
            client['telefonocel'] = int(client['telefonocel'])
        except:
            flash('El numero de telefono que ha introducido no es valido')
            actItems['telefonocel'] = True
            actItems['FT'] = True

        update = request.form.get('update', '').strip()
        if int(update) > 0:
            set_contact_by_casillero(newClient=client, casillero=cid)
            #TODO store the old contact

            return redirect(url_for('viewClient', cid=cid))

    return render_template('clients/edit.html', client=client, actItems=actItems)
