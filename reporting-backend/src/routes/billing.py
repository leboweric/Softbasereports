"""
Stripe Billing Routes
Handles subscription management for $700/month flat-rate billing
"""
import os
import stripe
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from src.models.user import db, Organization, User

billing_bp = Blueprint('billing', __name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID')  # Your $700/month price ID from Stripe Dashboard

# Frontend URLs for redirects
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://softbasereports.netlify.app')


@billing_bp.route('/billing/status', methods=['GET'])
@jwt_required()
def get_billing_status():
    """Get current subscription status for the organization"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        return jsonify({
            'subscription_status': org.subscription_status,
            'subscription_ends_at': org.subscription_ends_at.isoformat() if org.subscription_ends_at else None,
            'trial_ends_at': org.trial_ends_at.isoformat() if org.trial_ends_at else None,
            'has_active_subscription': org.has_active_subscription(),
            'stripe_customer_id': org.stripe_customer_id is not None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/billing/create-checkout-session', methods=['POST'])
@jwt_required()
def create_checkout_session():
    """Create a Stripe Checkout session for new subscriptions

    Accepts optional JSON body:
    - coupon_code: Stripe coupon code for discount
    """
    try:
        if not stripe.api_key:
            return jsonify({'error': 'Stripe API key not configured. Please set STRIPE_SECRET_KEY environment variable.'}), 500

        if not STRIPE_PRICE_ID:
            return jsonify({'error': 'Stripe price ID not configured. Please set STRIPE_PRICE_ID environment variable.'}), 500

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        # Get optional coupon code from request
        data = request.get_json() or {}
        coupon_code = data.get('coupon_code')

        # Create or retrieve Stripe customer
        if org.stripe_customer_id:
            customer_id = org.stripe_customer_id
        else:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=org.name,
                metadata={
                    'organization_id': str(org.id),
                    'organization_name': org.name
                }
            )
            customer_id = customer.id
            org.stripe_customer_id = customer_id
            db.session.commit()

        # Build checkout session params
        checkout_params = {
            'customer': customer_id,
            'payment_method_types': ['card'],
            'line_items': [{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': f'{FRONTEND_URL}?billing=success',
            'cancel_url': f'{FRONTEND_URL}?billing=canceled',
            'allow_promotion_codes': True,  # Allow customers to enter promo codes at checkout
            'metadata': {
                'organization_id': str(org.id)
            }
        }

        # Apply coupon if provided (for pre-applied discounts)
        if coupon_code:
            checkout_params['discounts'] = [{'coupon': coupon_code}]
            # Can't use both discounts and allow_promotion_codes
            del checkout_params['allow_promotion_codes']

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(**checkout_params)

        return jsonify({'checkout_url': checkout_session.url}), 200

    except stripe.error.StripeError as e:
        print(f"Stripe error in create-checkout-session: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in create-checkout-session: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/billing/apply-coupon', methods=['POST'])
@jwt_required()
def apply_coupon_to_subscription():
    """Apply a coupon/discount to an existing subscription (admin use)"""
    try:
        if not stripe.api_key:
            return jsonify({'error': 'Stripe not configured'}), 500

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        org_id = data.get('organization_id')
        coupon_code = data.get('coupon_code')

        if not org_id or not coupon_code:
            return jsonify({'error': 'organization_id and coupon_code required'}), 400

        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        if not org.stripe_subscription_id:
            return jsonify({'error': 'No active subscription found'}), 400

        # Apply coupon to subscription
        stripe.Subscription.modify(
            org.stripe_subscription_id,
            coupon=coupon_code
        )

        return jsonify({'message': f'Coupon {coupon_code} applied successfully'}), 200

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/billing/create-portal-session', methods=['POST'])
@jwt_required()
def create_portal_session():
    """Create a Stripe Customer Portal session for managing subscription"""
    try:
        if not stripe.api_key:
            return jsonify({'error': 'Stripe not configured'}), 500

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        org = Organization.query.get(user.organization_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        if not org.stripe_customer_id:
            return jsonify({'error': 'No billing account found. Please subscribe first.'}), 400

        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=org.stripe_customer_id,
            return_url=f'{FRONTEND_URL}?page=billing'
        )

        return jsonify({'portal_url': portal_session.url}), 200

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/billing/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    if not STRIPE_WEBHOOK_SECRET:
        # In development, process without signature verification
        event = stripe.Event.construct_from(
            request.get_json(), stripe.api_key
        )
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    try:
        if event['type'] == 'checkout.session.completed':
            handle_checkout_completed(event['data']['object'])

        elif event['type'] == 'customer.subscription.created':
            handle_subscription_created(event['data']['object'])

        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])

        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event['data']['object'])

        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])

        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


def handle_checkout_completed(session):
    """Handle successful checkout"""
    org_id = session.get('metadata', {}).get('organization_id')
    if not org_id:
        # Try to find org by customer ID
        customer_id = session.get('customer')
        org = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    else:
        org = Organization.query.get(int(org_id))

    if org:
        subscription_id = session.get('subscription')
        if subscription_id:
            org.stripe_subscription_id = subscription_id
            org.subscription_status = 'active'
            db.session.commit()
            print(f"✅ Checkout completed for org {org.name}")


def handle_subscription_created(subscription):
    """Handle new subscription"""
    customer_id = subscription.get('customer')
    org = Organization.query.filter_by(stripe_customer_id=customer_id).first()

    if org:
        org.stripe_subscription_id = subscription.get('id')
        org.subscription_status = subscription.get('status', 'active')

        # Set subscription end date
        current_period_end = subscription.get('current_period_end')
        if current_period_end:
            org.subscription_ends_at = datetime.fromtimestamp(current_period_end)

        db.session.commit()
        print(f"✅ Subscription created for org {org.name}")


def handle_subscription_updated(subscription):
    """Handle subscription updates (renewals, status changes)"""
    customer_id = subscription.get('customer')
    org = Organization.query.filter_by(stripe_customer_id=customer_id).first()

    if org:
        org.subscription_status = subscription.get('status', 'active')

        # Update subscription end date
        current_period_end = subscription.get('current_period_end')
        if current_period_end:
            org.subscription_ends_at = datetime.fromtimestamp(current_period_end)

        db.session.commit()
        print(f"✅ Subscription updated for org {org.name}: {org.subscription_status}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')
    org = Organization.query.filter_by(stripe_customer_id=customer_id).first()

    if org:
        org.subscription_status = 'canceled'
        # Keep subscription_ends_at so they have access until period ends
        db.session.commit()
        print(f"⚠️ Subscription canceled for org {org.name}")


def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice.get('customer')
    org = Organization.query.filter_by(stripe_customer_id=customer_id).first()

    if org:
        # Ensure status is active after successful payment
        if org.subscription_status == 'past_due':
            org.subscription_status = 'active'
            db.session.commit()
        print(f"✅ Payment succeeded for org {org.name}")


def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice.get('customer')
    org = Organization.query.filter_by(stripe_customer_id=customer_id).first()

    if org:
        org.subscription_status = 'past_due'
        db.session.commit()
        print(f"⚠️ Payment failed for org {org.name}")
