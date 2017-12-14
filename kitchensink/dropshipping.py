from collections import defaultdict
from datetime import date
from flask_login import login_required
from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired
import unicodecsv as csv
from .extensions import fulfil

dropshipping = Blueprint('dropshipping', __name__, url_prefix="/drop-shipping")


class UploadForm(FlaskForm):
    quantum_file = FileField(
        'Upload File',
        validators=[DataRequired()]
    )


@dropshipping.route('/update-tracking', methods=['POST'])
@login_required
def update_tracking():
    DropShipment = fulfil.model('stock.shipment.drop')
    Tracking = fulfil.model('shipment.tracking')
    carrier_id = request.form.get('carrier', type=int)
    tracking_id, = Tracking.create([{
        'carrier': carrier_id,
        'tracking_number': request.form['tracking_number'],
    }])
    shipment_id = request.form.get('shipment', type=int)
    DropShipment.write(
        [shipment_id],
        {
            'tracking_number': tracking_id,
            'carrier': carrier_id,
        }
    )
    DropShipment.ship([shipment_id])
    DropShipment.done([shipment_id])
    return 'OK'


@dropshipping.route('/', methods=['GET', 'POST'])
@login_required
def shipments():
    "Show a quick view"
    shipments = get_open_drop_shipments()

    form = UploadForm()
    quantum_data = None
    if form.validate_on_submit():
        filename = secure_filename(form.quantum_file.data.filename)
        form.quantum_file.data.save('/tmp/' + filename)
        quantum_data = dict([
            (row['Tracking Number'], row) for row in
            list(csv.DictReader(open('/tmp/' + filename, 'r')))
        ])
        match_quantum_data(shipments, quantum_data)
    return render_template(
        'drop-shipping.html',
        shipments=sorted(
            shipments.values(),
            key=lambda o: o.get('order_date', date.today())
        ),
        quantum_data=quantum_data,
        form=form,
    )


def match_quantum_data(shipments, quantum_data):
    for shipment in shipments.values():
        for row in quantum_data.values():
            if (
                (shipment['delivery_state'] is not None) and
                (shipment['delivery_state'][-2:] == row['Ship To State/Province']) and
                    (row['Ship To Postal Code'][-4:] == shipment['delivery_zip'][-4:])):
                shipment['tracking_number'] = row['Tracking Number']
                break


def get_open_drop_shipments():
    Move = fulfil.model('stock.move')
    moves = list(Move.search_read_all(
        [
            ('shipment.state', '=', 'waiting', 'stock.shipment.drop'),
            ('origin', 'like', 'purchase.line,%'),
        ],
        None,
        [
            'shipment.rec_name',
            'shipment.customer.name',
            'shipment.supplier.name',
            'origin.purchase',
            'origin.purchase.number',
            'origin.purchase.reference',
            'origin.purchase.purchase_date',
            'origin',
            'shipment',
            'shipment.delivery_address.full_address',
            'shipment.delivery_address.subdivision.code',
            'shipment.delivery_address.zip',
        ]
    ))
    moves.extend(list(Move.search_read_all(
        [
            ('shipment.state', '=', 'waiting', 'stock.shipment.drop'),
            ('origin', 'like', 'sale.line,%'),
        ],
        None,
        [
            'shipment.rec_name',
            'shipment.customer.name',
            'shipment.supplier.name',
            'origin.sale',
            'origin.sale.number',
            'origin.sale.reference',
            'origin.sale.sale_date',
            'origin',
            'shipment',
            'shipment.delivery_address.full_address',
            'shipment.delivery_address.subdivision.code',
            'shipment.delivery_address.zip',
        ]
    )))
    shipments = defaultdict(lambda: {
        'id': None,
        'number': None,
        'supplier_moves': [],
        'customer_moves': [],
        'keywords': [],
    })
    for move in moves:
        shipment = shipments[move['shipment.rec_name']]
        if move['origin'].startswith('purchase.line'):
            shipment['supplier_moves'].append(move)
            shipment['keywords'].append(move['origin.purchase.number'])
            shipment['keywords'].append(move['origin.purchase.reference'])
        elif move['origin'].startswith('sale.line'):
            shipment['customer_moves'].append(move)
            shipment['keywords'].append(move['origin.sale.number'])
            shipment['order_date'] = move['origin.sale.sale_date']
        shipment['customer.name'] = move['shipment.customer.name']
        shipment['supplier.name'] = move['shipment.supplier.name']
        shipment['number'] = move['shipment.rec_name']
        shipment['id'] = move['shipment']
        shipment['delivery_address'] = move[
            'shipment.delivery_address.full_address'
        ]
        shipment['delivery_state'] = move[
            'shipment.delivery_address.subdivision.code'
        ]
        shipment['delivery_zip'] = move[
            'shipment.delivery_address.zip'
        ]
        shipment['keywords'].extend([
            move['shipment.customer.name'],
            move['shipment.supplier.name'],
        ] + move[
            'shipment.delivery_address.full_address'
        ].split('\r\n'))

    for shipment in shipments.values():
        shipment['keywords'] = ' '.join(filter(None, set(shipment['keywords'])))
    return shipments
