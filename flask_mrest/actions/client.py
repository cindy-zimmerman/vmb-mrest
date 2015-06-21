__author__ = 'cz'

from flask import request, redirect, url_for, flash, current_app, abort, render_template
from flask.ext.login import login_required, current_user
from vmb_db.contact_info import get_contact, get_contact_by_casillero, set_contact_by_casillero, iter_pages
from vmb_db.invoice_info import get_invoice_list_by_casillero, set_inv_by_guia, INVOICES_PER_PAGE
from vmb_db.accounts import insert_account


@login_required
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

    return render_template('clients/view.html', client=client, ilist=invoices)


@login_required
def editClient(cid):
    if cid == '0':
        client = {'contacto_nombre_1': '', 'casillero': '0', 'contacto_nombre_2': '',
                  'direccion_area': '', 'direccion_torre': '', 'direccion_calle': '',
                  'telefonocel': '', 'correo': '', 'ciudad': 'Panama',
                  'contacto_apellido_2': '', 'VMB_ACCOUNTS_id': 0, 'contacto_apellido_1': '', 'telefonofij': '',
                  'tarifa': 0,
                  'direccion_apt': ''}
    else:
        client = get_contact_by_casillero(casillero=cid)

    actItems = {'FT': True, 'telefonofij': False, 'telefonocel': False, 'tarifa': False}

    if not client:
        flash('User %s not found' % cid, 'error')
        return redirect(url_for('/'))

    if request.method.lower() == 'post':
        actItems['FT'] = False
        client['contacto_nombre_1'] = request.form.get('contacto_nombre_1', '').strip()
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

            if client['telefonofij'][:3] not in ('507', '506'):
                client['telefonofij'] = '507%s' % (client['telefonofij'])

            if client['telefonocel'][:3] not in ('507', '506'):
                client['telefonocel'] = '507%s' % (client['telefonocel'])

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
            if cid == '0':

                ncid = insert_account(contacto_nombre_1=client['contacto_nombre_1'],
                               contacto_nombre_2=client['contacto_nombre_2'],
                               contacto_apellido_1=client['contacto_apellido_1'],
                               contacto_apellido_2=client['contacto_apellido_2'],
                               telefonofij=client['telefonofij'],
                               telefonocel=client['telefonocel'],
                               correo=client['correo'],
                               direccion_calle=client['direccion_calle'],
                               direccion_torre=client['direccion_torre'],
                               direccion_apt=client['direccion_apt'],
                               direccion_area=client['direccion_area'],
                               ciudad=client['ciudad'],
                               tarifa=client['tarifa'])
                where = 'VMB_ACCOUNTS_id = %s' % (ncid)
                client = get_contact(where=where)
                cid = client['casillero']
            else:
                set_contact_by_casillero(newClient=client, casillero=cid, updatedUser=current_user.username)

            return redirect(url_for('viewClient', cid=cid))

    return render_template('clients/edit.html', client=client, actItems=actItems)
