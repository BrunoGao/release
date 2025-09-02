from flask import jsonify
from .models import db, DeviceInfo, CustomerConfig

def check_license(customerId):
    if not customerId:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    try:
        # Count unique device serial numbers for the given customer_id using DeviceInfo model
        device_count = DeviceInfo.query.filter_by(customer_id=customerId).distinct(DeviceInfo.serial_number).count()

        # Get the license_key for the given customer_id using CustomerConfig model
        customer_config = CustomerConfig.query.filter_by(id=customerId).first()

        if customer_config is None:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404

        # Compare device count with license key
        is_exceeded = device_count > customer_config.license_key

        return jsonify({
            'success': True,
            'isExceeded': is_exceeded,
            'license_key': customer_config.license_key  # Include license_key in the response
        })
    except Exception as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500