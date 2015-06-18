import math

from flask import render_template, request
from vmb_db.conn import get_one
from vmb_db.contact_info import get_contact_list, CLIENTS_PER_PAGE, iter_pages

# from flask.ext.login import login_required
#
# from coinapult_common.context import Context
#
# from vmbCore.common import TRANSACTION_PER_PAGE, iter_pages


# c = Context()

# @login_required
def go():

    try:
        page = int(request.args.get('page', '1'))

        allUsers = get_contact_list(where=None, sort=None, limit=CLIENTS_PER_PAGE, skip=(page - 1) * CLIENTS_PER_PAGE)
        n = get_one(query='SELECT COUNT(*) AS count FROM VMB.VMB_ACCOUNTS')
        count = int(n['count'])
        print count

        numpages = int(math.ceil(count / float(CLIENTS_PER_PAGE)))

        return render_template('main.html', tlist=allUsers,
                               tcount=count, tnumpages=numpages, tpage=page,
                               pagination=iter_pages)


    except Exception,e:
        errorMes = str(e)
        print errorMes
