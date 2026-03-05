"""
Aloha Holdings — Subsidiary Access Management
Manages per-user subsidiary access assignments.
Provides helper to get allowed subsidiaries for any user.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Organization, db
import logging

logger = logging.getLogger(__name__)

aloha_subsidiary_access_bp = Blueprint('aloha_subsidiary_access', __name__)

# Master list of all subsidiaries
ALL_SUBSIDIARY_IDS = [
    'sap_sandia', 'sap_mercury', 'sap_ultimate_solutions', 'sap_avalon', 'sap_orbot',
    'ns_hawaii_care', 'ns_kauai_exclusive', 'ns_heavenly_vacations'
]

ALL_SUBSIDIARIES = {
    'sap_sandia': {'name': 'Sandia', 'erp_type': 'SAP'},
    'sap_mercury': {'name': 'Mercury', 'erp_type': 'SAP'},
    'sap_ultimate_solutions': {'name': 'Ultimate Solutions', 'erp_type': 'SAP'},
    'sap_avalon': {'name': 'Avalon', 'erp_type': 'SAP'},
    'sap_orbot': {'name': 'Orbot', 'erp_type': 'SAP'},
    'ns_hawaii_care': {'name': 'Hawaii Care and Cleaning', 'erp_type': 'NetSuite'},
    'ns_kauai_exclusive': {'name': 'Kauai Exclusive', 'erp_type': 'NetSuite'},
    'ns_heavenly_vacations': {'name': 'Heavenly Vacations', 'erp_type': 'NetSuite'},
}


def get_user_allowed_subsidiaries(user_id):
    """
    Returns the list of subsidiary IDs the user is allowed to access.
    If user has 'all' assignment, returns all subsidiary IDs.
    If user has no assignments, returns empty list (secure by default).
    """
    try:
        rows = db.session.execute(
            db.text("SELECT subsidiary_id FROM user_subsidiary_access WHERE user_id = :uid"),
            {'uid': user_id}
        ).fetchall()

        if not rows:
            return []

        sub_ids = [r[0] for r in rows]

        if 'all' in sub_ids:
            return list(ALL_SUBSIDIARY_IDS)

        # Only return valid subsidiary IDs
        return [s for s in sub_ids if s in ALL_SUBSIDIARY_IDS]
    except Exception as e:
        logger.error(f"Error fetching subsidiary access for user {user_id}: {e}")
        return []


def filter_subsidiaries_for_user(user_id, data_dict):
    """
    Filters a dictionary keyed by subsidiary_id to only include
    subsidiaries the user has access to.
    """
    allowed = get_user_allowed_subsidiaries(user_id)
    return {k: v for k, v in data_dict.items() if k in allowed}


def _verify_aloha_admin(user_id):
    """Verify user is an Aloha Holdings admin"""
    user = User.query.get(user_id)
    if not user or not user.organization_id:
        return None, None, ('User not found', 404)

    org = Organization.query.get(user.organization_id)
    if not org or org.name != 'Aloha Holdings':
        return None, None, ('Access denied — not an Aloha Holdings user', 403)

    # Check if user has Aloha Admin role
    role_check = db.session.execute(
        db.text("""
            SELECT r.name FROM user_roles ur
            JOIN role r ON ur.role_id = r.id
            WHERE ur.user_id = :uid AND r.name = 'Aloha Admin'
        """),
        {'uid': user_id}
    ).fetchone()

    if not role_check:
        return None, None, ('Admin access required', 403)

    return user, org, None


@aloha_subsidiary_access_bp.route('/api/aloha/subsidiary-access/<int:target_user_id>', methods=['GET'])
@jwt_required()
def get_subsidiary_access(target_user_id):
    """
    Get subsidiary access assignments for a specific user.
    Only Aloha Admins can view this.
    """
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_admin(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]

        # Verify target user is in same org
        target_user = User.query.get(target_user_id)
        if not target_user or target_user.organization_id != org.id:
            return jsonify({'error': 'User not found in this organization'}), 404

        allowed = get_user_allowed_subsidiaries(target_user_id)
        has_all = False

        # Check if they have the 'all' flag
        all_check = db.session.execute(
            db.text("SELECT 1 FROM user_subsidiary_access WHERE user_id = :uid AND subsidiary_id = 'all'"),
            {'uid': target_user_id}
        ).fetchone()
        if all_check:
            has_all = True

        return jsonify({
            'user_id': target_user_id,
            'username': target_user.username,
            'has_all_access': has_all,
            'assigned_subsidiaries': allowed,
            'all_subsidiaries': [
                {'id': sid, 'name': info['name'], 'erp_type': info['erp_type']}
                for sid, info in ALL_SUBSIDIARIES.items()
            ]
        })

    except Exception as e:
        logger.error(f"Error getting subsidiary access: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_subsidiary_access_bp.route('/api/aloha/subsidiary-access/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_subsidiary_access(target_user_id):
    """
    Update subsidiary access assignments for a specific user.
    Only Aloha Admins can modify this.

    Body: { "subsidiary_ids": ["sap_sandia", "sap_mercury", ...] }
    Or:   { "all_access": true }
    """
    try:
        user_id = get_jwt_identity()
        user, org, error = _verify_aloha_admin(user_id)
        if error:
            return jsonify({'error': error[0]}), error[1]

        # Verify target user is in same org
        target_user = User.query.get(target_user_id)
        if not target_user or target_user.organization_id != org.id:
            return jsonify({'error': 'User not found in this organization'}), 404

        data = request.get_json()
        all_access = data.get('all_access', False)
        subsidiary_ids = data.get('subsidiary_ids', [])

        # Validate subsidiary IDs
        if not all_access:
            invalid = [s for s in subsidiary_ids if s not in ALL_SUBSIDIARY_IDS]
            if invalid:
                return jsonify({'error': f'Invalid subsidiary IDs: {invalid}'}), 400

        # Clear existing assignments
        db.session.execute(
            db.text("DELETE FROM user_subsidiary_access WHERE user_id = :uid"),
            {'uid': target_user_id}
        )

        # Insert new assignments
        if all_access:
            db.session.execute(
                db.text("INSERT INTO user_subsidiary_access (user_id, subsidiary_id) VALUES (:uid, 'all')"),
                {'uid': target_user_id}
            )
        else:
            for sid in subsidiary_ids:
                db.session.execute(
                    db.text("INSERT INTO user_subsidiary_access (user_id, subsidiary_id) VALUES (:uid, :sid)"),
                    {'uid': target_user_id, 'sid': sid}
                )

        db.session.commit()

        allowed = get_user_allowed_subsidiaries(target_user_id)
        logger.info(f"Updated subsidiary access for user {target_user_id}: {'all' if all_access else subsidiary_ids}")

        return jsonify({
            'message': 'Subsidiary access updated successfully',
            'user_id': target_user_id,
            'has_all_access': all_access,
            'assigned_subsidiaries': allowed
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating subsidiary access: {e}")
        return jsonify({'error': str(e)}), 500


@aloha_subsidiary_access_bp.route('/api/aloha/subsidiary-access', methods=['GET'])
@jwt_required()
def get_my_subsidiary_access():
    """
    Get the current user's own subsidiary access.
    Any Aloha user can call this.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        org = Organization.query.get(user.organization_id)
        if not org or org.name != 'Aloha Holdings':
            return jsonify({'error': 'Not an Aloha Holdings user'}), 403

        allowed = get_user_allowed_subsidiaries(user_id)

        return jsonify({
            'user_id': user_id,
            'assigned_subsidiaries': allowed,
            'subsidiary_details': [
                {'id': sid, 'name': ALL_SUBSIDIARIES[sid]['name'], 'erp_type': ALL_SUBSIDIARIES[sid]['erp_type']}
                for sid in allowed if sid in ALL_SUBSIDIARIES
            ]
        })

    except Exception as e:
        logger.error(f"Error getting own subsidiary access: {e}")
        return jsonify({'error': str(e)}), 500
