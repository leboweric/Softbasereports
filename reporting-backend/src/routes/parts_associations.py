"""
Parts Associations API
Stores manager-configured and AI-discovered part associations for upsell intelligence.
Used by:
  - Parts Association Manager (config UI)
  - Real-Time Counter Assistant (lookup tool)
  - Missed Opportunity Report (analytics)
"""
import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.postgres_service import PostgreSQLService
from src.models.user import User
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema

logger = logging.getLogger(__name__)

parts_associations_bp = Blueprint(
    'parts_associations', __name__, url_prefix='/api/parts-associations'
)


def _get_org_id():
    """Get the current user's organization ID."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        return user.organization_id if user else None
    except Exception:
        return None


def _get_db():
    return get_tenant_db()


# ── GET all associations for this org ─────────────────────────────────────────
@parts_associations_bp.route('/', methods=['GET'])
@jwt_required()
def get_associations():
    """Return all active parts associations for the current org."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_parts_associations_sql())
            cursor.execute("""
                SELECT id, trigger_part_no, trigger_description,
                       recommended_part_no, recommended_description,
                       relationship_type, reason, confidence, source,
                       is_active, created_at, created_by, updated_at, updated_by
                FROM parts_associations
                WHERE org_id = %s
                ORDER BY trigger_part_no, confidence DESC
            """, (org_id,))
            rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                'id': r['id'],
                'triggerPartNo': r['trigger_part_no'],
                'triggerDescription': r['trigger_description'],
                'recommendedPartNo': r['recommended_part_no'],
                'recommendedDescription': r['recommended_description'],
                'relationshipType': r['relationship_type'],
                'reason': r['reason'],
                'confidence': float(r['confidence'] or 0),
                'source': r['source'],
                'isActive': r['is_active'],
                'createdAt': r['created_at'].isoformat() if r['created_at'] else None,
                'createdBy': r['created_by'],
                'updatedAt': r['updated_at'].isoformat() if r['updated_at'] else None,
                'updatedBy': r['updated_by'],
            })
        return jsonify({'associations': result, 'total': len(result)}), 200
    except Exception as e:
        logger.error(f"Error fetching parts associations: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── GET associations for a specific trigger part (used by counter assistant) ──
@parts_associations_bp.route('/lookup/<string:part_no>', methods=['GET'])
@jwt_required()
def lookup_associations(part_no):
    """Return active associations for a given trigger part number."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_parts_associations_sql())
            cursor.execute("""
                SELECT id, trigger_part_no, trigger_description,
                       recommended_part_no, recommended_description,
                       relationship_type, reason, confidence, source
                FROM parts_associations
                WHERE org_id = %s
                  AND UPPER(trigger_part_no) = UPPER(%s)
                  AND is_active = TRUE
                ORDER BY confidence DESC
            """, (org_id, part_no.strip()))
            rows = cursor.fetchall()
        # Also fetch current stock for each recommended part
        db = _get_db()
        schema = get_tenant_schema()
        recommendations = []
        for r in rows:
            rec_part_no = r['recommended_part_no']
            stock_info = {'onHand': None, 'stockStatus': 'Unknown'}
            try:
                stock_rows = db.execute_query(f"""
                    SELECT OnHand, Cost
                    FROM {schema}.Parts
                    WHERE PartNo = ?
                """, (rec_part_no,))
                if stock_rows:
                    on_hand = stock_rows[0].get('OnHand', 0) or 0
                    stock_info = {
                        'onHand': float(on_hand),
                        'stockStatus': 'In Stock' if on_hand > 0 else 'Out of Stock',
                        'unitCost': float(stock_rows[0].get('Cost', 0) or 0),
                    }
            except Exception:
                pass
            recommendations.append({
                'id': r['id'],
                'recommendedPartNo': rec_part_no,
                'recommendedDescription': r['recommended_description'],
                'relationshipType': r['relationship_type'],
                'reason': r['reason'],
                'confidence': float(r['confidence'] or 0),
                'source': r['source'],
                **stock_info,
            })
        return jsonify({
            'triggerPartNo': part_no.upper(),
            'recommendations': recommendations,
            'count': len(recommendations),
        }), 200
    except Exception as e:
        logger.error(f"Error looking up parts associations for {part_no}: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── POST — create a single association ────────────────────────────────────────
@parts_associations_bp.route('/', methods=['POST'])
@jwt_required()
def create_association():
    """Create a new parts association."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        data = request.get_json() or {}
        username = get_jwt_identity()
        trigger = (data.get('triggerPartNo') or '').strip().upper()
        recommended = (data.get('recommendedPartNo') or '').strip().upper()
        if not trigger or not recommended:
            return jsonify({'error': 'triggerPartNo and recommendedPartNo are required'}), 400
        if trigger == recommended:
            return jsonify({'error': 'Trigger and recommended parts cannot be the same'}), 400
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_parts_associations_sql())
            cursor.execute("""
                INSERT INTO parts_associations
                    (org_id, trigger_part_no, trigger_description,
                     recommended_part_no, recommended_description,
                     relationship_type, reason, confidence, source,
                     is_active, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (org_id, trigger_part_no, recommended_part_no) DO UPDATE SET
                    trigger_description      = EXCLUDED.trigger_description,
                    recommended_description  = EXCLUDED.recommended_description,
                    relationship_type        = EXCLUDED.relationship_type,
                    reason                   = EXCLUDED.reason,
                    confidence               = EXCLUDED.confidence,
                    source                   = EXCLUDED.source,
                    is_active                = EXCLUDED.is_active,
                    updated_at               = CURRENT_TIMESTAMP,
                    updated_by               = EXCLUDED.created_by
                RETURNING id
            """, (
                org_id,
                trigger,
                data.get('triggerDescription', ''),
                recommended,
                data.get('recommendedDescription', ''),
                data.get('relationshipType', 'often_needed_together'),
                data.get('reason', ''),
                float(data.get('confidence', 80)),
                data.get('source', 'manual'),
                data.get('isActive', True),
                username,
            ))
            row = cursor.fetchone()
            conn.commit()
        return jsonify({'message': 'Association saved', 'id': row['id'] if row else None}), 201
    except Exception as e:
        logger.error(f"Error creating parts association: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── PUT — update an association by id ─────────────────────────────────────────
@parts_associations_bp.route('/<int:assoc_id>', methods=['PUT'])
@jwt_required()
def update_association(assoc_id):
    """Update a parts association."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        data = request.get_json() or {}
        username = get_jwt_identity()
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE parts_associations SET
                    trigger_description     = %s,
                    recommended_description = %s,
                    relationship_type       = %s,
                    reason                  = %s,
                    confidence              = %s,
                    is_active               = %s,
                    updated_at              = CURRENT_TIMESTAMP,
                    updated_by              = %s
                WHERE id = %s AND org_id = %s
            """, (
                data.get('triggerDescription', ''),
                data.get('recommendedDescription', ''),
                data.get('relationshipType', 'often_needed_together'),
                data.get('reason', ''),
                float(data.get('confidence', 80)),
                data.get('isActive', True),
                username,
                assoc_id,
                org_id,
            ))
            conn.commit()
        return jsonify({'message': 'Association updated'}), 200
    except Exception as e:
        logger.error(f"Error updating parts association: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── DELETE ────────────────────────────────────────────────────────────────────
@parts_associations_bp.route('/<int:assoc_id>', methods=['DELETE'])
@jwt_required()
def delete_association(assoc_id):
    """Delete a parts association."""
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM parts_associations WHERE id = %s AND org_id = %s",
                (assoc_id, org_id)
            )
            conn.commit()
        return jsonify({'message': 'Association deleted'}), 200
    except Exception as e:
        logger.error(f"Error deleting parts association: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── POST /bulk-import — import AI-discovered associations ─────────────────────
@parts_associations_bp.route('/bulk-import', methods=['POST'])
@jwt_required()
def bulk_import_associations():
    """
    Bulk-import a list of associations (from AI market basket analysis or CSV).
    Each item: {triggerPartNo, triggerDescription, recommendedPartNo,
                recommendedDescription, relationshipType, reason, confidence, source}
    Uses upsert — safe to call repeatedly.
    """
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400
        data = request.get_json() or {}
        assoc_list = data.get('associations', [])
        if not isinstance(assoc_list, list):
            return jsonify({'error': 'associations must be a list'}), 400
        username = get_jwt_identity()
        pg = PostgreSQLService()
        saved = 0
        skipped = 0
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_parts_associations_sql())
            for item in assoc_list:
                trigger = (item.get('triggerPartNo') or '').strip().upper()
                recommended = (item.get('recommendedPartNo') or '').strip().upper()
                if not trigger or not recommended or trigger == recommended:
                    skipped += 1
                    continue
                cursor.execute("""
                    INSERT INTO parts_associations
                        (org_id, trigger_part_no, trigger_description,
                         recommended_part_no, recommended_description,
                         relationship_type, reason, confidence, source,
                         is_active, created_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (org_id, trigger_part_no, recommended_part_no) DO UPDATE SET
                        trigger_description     = EXCLUDED.trigger_description,
                        recommended_description = EXCLUDED.recommended_description,
                        relationship_type       = EXCLUDED.relationship_type,
                        reason                  = EXCLUDED.reason,
                        confidence              = CASE
                            WHEN parts_associations.source = 'manual'
                            THEN parts_associations.confidence
                            ELSE EXCLUDED.confidence
                        END,
                        source                  = CASE
                            WHEN parts_associations.source = 'manual' THEN 'manual'
                            ELSE EXCLUDED.source
                        END,
                        updated_at              = CURRENT_TIMESTAMP,
                        updated_by              = EXCLUDED.created_by
                """, (
                    org_id,
                    trigger,
                    item.get('triggerDescription', ''),
                    recommended,
                    item.get('recommendedDescription', ''),
                    item.get('relationshipType', 'often_needed_together'),
                    item.get('reason', ''),
                    float(item.get('confidence', 70)),
                    item.get('source', 'ai_analysis'),
                    True,
                    username,
                ))
                saved += 1
            conn.commit()
        return jsonify({'message': f'{saved} associations saved, {skipped} skipped', 'saved': saved, 'skipped': skipped}), 200
    except Exception as e:
        logger.error(f"Error bulk-importing parts associations: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── GET /market-basket — run AI market basket analysis on WOParts history ─────
@parts_associations_bp.route('/market-basket', methods=['GET'])
@jwt_required()
def run_market_basket():
    """
    Analyze WOParts history to find parts that are frequently bought together.
    Returns top co-occurrence pairs sorted by confidence score.
    Query params:
      - min_support: minimum number of WOs both parts appear in together (default 3)
      - min_confidence: minimum confidence % (default 40)
      - lookback_days: how many days of history to analyze (default 365)
    """
    try:
        db = _get_db()
        schema = get_tenant_schema()
        min_support = int(request.args.get('min_support', 3))
        min_confidence = float(request.args.get('min_confidence', 40))
        lookback_days = int(request.args.get('lookback_days', 365))

        # Market basket analysis using self-join on WOParts
        # For each pair (A, B) that appear on the same WO:
        #   support = count of WOs where both A and B appear
        #   confidence(A->B) = support(A,B) / support(A)
        #   confidence(B->A) = support(A,B) / support(B)
        query = f"""
        WITH RecentWOs AS (
            SELECT DISTINCT wp.WONo, wp.PartNo,
                   MAX(wp.Description) as Description
            FROM {schema}.WOParts wp
            INNER JOIN {schema}.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(day, -{lookback_days}, GETDATE())
              AND wp.Qty > 0
              AND wp.PartNo IS NOT NULL
              AND wp.PartNo != ''
              AND w.DeletionTime IS NULL
            GROUP BY wp.WONo, wp.PartNo
        ),
        PartFrequency AS (
            SELECT PartNo, Description, COUNT(DISTINCT WONo) as freq
            FROM RecentWOs
            GROUP BY PartNo, Description
        ),
        Pairs AS (
            SELECT
                a.PartNo as part_a,
                a.Description as desc_a,
                b.PartNo as part_b,
                b.Description as desc_b,
                COUNT(DISTINCT a.WONo) as co_occurrence
            FROM RecentWOs a
            INNER JOIN RecentWOs b ON a.WONo = b.WONo AND a.PartNo < b.PartNo
            GROUP BY a.PartNo, a.Description, b.PartNo, b.Description
            HAVING COUNT(DISTINCT a.WONo) >= {min_support}
        )
        SELECT
            p.part_a as TriggerPartNo,
            p.desc_a as TriggerDescription,
            p.part_b as RecommendedPartNo,
            p.desc_b as RecommendedDescription,
            p.co_occurrence as CoOccurrence,
            fa.freq as TriggerFreq,
            fb.freq as RecommendedFreq,
            CAST(p.co_occurrence AS FLOAT) / fa.freq * 100 as ConfidenceAtoB,
            CAST(p.co_occurrence AS FLOAT) / fb.freq * 100 as ConfidenceBtoA
        FROM Pairs p
        INNER JOIN PartFrequency fa ON p.part_a = fa.PartNo
        INNER JOIN PartFrequency fb ON p.part_b = fb.PartNo
        WHERE CAST(p.co_occurrence AS FLOAT) / fa.freq * 100 >= {min_confidence}
           OR CAST(p.co_occurrence AS FLOAT) / fb.freq * 100 >= {min_confidence}
        ORDER BY p.co_occurrence DESC, ConfidenceAtoB DESC
        """
        results = db.execute_query(query)

        # Expand each pair into two directional associations
        associations = []
        for r in results:
            conf_a_to_b = float(r.get('ConfidenceAtoB', 0) or 0)
            conf_b_to_a = float(r.get('ConfidenceBtoA', 0) or 0)
            co = int(r.get('CoOccurrence', 0) or 0)
            if conf_a_to_b >= min_confidence:
                associations.append({
                    'triggerPartNo': r['TriggerPartNo'],
                    'triggerDescription': r['TriggerDescription'] or '',
                    'recommendedPartNo': r['RecommendedPartNo'],
                    'recommendedDescription': r['RecommendedDescription'] or '',
                    'coOccurrence': co,
                    'triggerFreq': int(r.get('TriggerFreq', 0) or 0),
                    'confidence': round(conf_a_to_b, 1),
                    'source': 'ai_analysis',
                    'relationshipType': 'often_needed_together',
                    'reason': f'Appeared together on {co} work orders ({round(conf_a_to_b, 1)}% of {r["TriggerPartNo"]} WOs also included {r["RecommendedPartNo"]})',
                })
            if conf_b_to_a >= min_confidence:
                associations.append({
                    'triggerPartNo': r['RecommendedPartNo'],
                    'triggerDescription': r['RecommendedDescription'] or '',
                    'recommendedPartNo': r['TriggerPartNo'],
                    'recommendedDescription': r['TriggerDescription'] or '',
                    'coOccurrence': co,
                    'triggerFreq': int(r.get('RecommendedFreq', 0) or 0),
                    'confidence': round(conf_b_to_a, 1),
                    'source': 'ai_analysis',
                    'relationshipType': 'often_needed_together',
                    'reason': f'Appeared together on {co} work orders ({round(conf_b_to_a, 1)}% of {r["RecommendedPartNo"]} WOs also included {r["TriggerPartNo"]})',
                })

        # Sort by confidence descending
        associations.sort(key=lambda x: x['confidence'], reverse=True)

        return jsonify({
            'associations': associations,
            'total': len(associations),
            'params': {
                'minSupport': min_support,
                'minConfidence': min_confidence,
                'lookbackDays': lookback_days,
            }
        }), 200
    except Exception as e:
        logger.error(f"Error running market basket analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── GET /missed-opportunities — find invoices where upsell was missed ─────────
@parts_associations_bp.route('/missed-opportunities', methods=['GET'])
@jwt_required()
def get_missed_opportunities():
    """
    Find invoices/WOs where a trigger part was sold but the recommended part was NOT.
    Returns summary by salesperson and by month.
    Query params:
      - start_date: YYYY-MM-DD (default: 90 days ago)
      - end_date: YYYY-MM-DD (default: today)
    """
    try:
        org_id = _get_org_id()
        if not org_id:
            return jsonify({'error': 'Could not determine organization'}), 400

        from datetime import datetime, timedelta
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        # Get all active associations for this org
        pg = PostgreSQLService()
        with pg.get_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database connection not available'}), 500
            cursor = conn.cursor()
            cursor.execute(pg._get_parts_associations_sql())
            cursor.execute("""
                SELECT trigger_part_no, recommended_part_no,
                       trigger_description, recommended_description,
                       reason, confidence
                FROM parts_associations
                WHERE org_id = %s AND is_active = TRUE
                ORDER BY confidence DESC
            """, (org_id,))
            assoc_rows = cursor.fetchall()

        if not assoc_rows:
            return jsonify({
                'missedOpportunities': [],
                'summary': {'totalMissed': 0, 'estimatedRevenueMissed': 0},
                'byRep': [],
                'byMonth': [],
                'message': 'No associations configured. Add associations in the Parts Association Manager first.'
            }), 200

        db = _get_db()
        schema = get_tenant_schema()

        # Build a query that finds WOs where trigger was sold but recommended was NOT
        # We'll do this per association and union them
        all_missed = []
        for assoc in assoc_rows:
            trigger = assoc['trigger_part_no']
            recommended = assoc['recommended_part_no']
            try:
                missed_query = f"""
                SELECT
                    wp_trigger.WONo,
                    w.OpenDate,
                    YEAR(w.OpenDate) as YearNum,
                    MONTH(w.OpenDate) as MonthNum,
                    w.Salesman,
                    wp_trigger.PartNo as TriggerPartNo,
                    wp_trigger.Description as TriggerDescription,
                    SUM(wp_trigger.Sell * wp_trigger.Qty) as TriggerRevenue,
                    '{trigger}' as AssocTrigger,
                    '{recommended}' as AssocRecommended
                FROM {schema}.WOParts wp_trigger
                INNER JOIN {schema}.WO w ON wp_trigger.WONo = w.WONo
                WHERE wp_trigger.PartNo = ?
                  AND w.OpenDate >= ?
                  AND w.OpenDate <= ?
                  AND w.DeletionTime IS NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM {schema}.WOParts wp_rec
                      WHERE wp_rec.WONo = wp_trigger.WONo
                        AND wp_rec.PartNo = ?
                  )
                GROUP BY wp_trigger.WONo, w.OpenDate, w.Salesman,
                         wp_trigger.PartNo, wp_trigger.Description
                """
                rows = db.execute_query(missed_query, (trigger, start_date, end_date, recommended))
                for r in rows:
                    all_missed.append({
                        'woNo': r.get('WONo', ''),
                        'date': r['OpenDate'].strftime('%Y-%m-%d') if r.get('OpenDate') else '',
                        'year': int(r.get('YearNum', 0) or 0),
                        'month': int(r.get('MonthNum', 0) or 0),
                        'salesman': r.get('Salesman', 'Unknown') or 'Unknown',
                        'triggerPartNo': r.get('TriggerPartNo', trigger),
                        'triggerDescription': r.get('TriggerDescription', ''),
                        'triggerRevenue': float(r.get('TriggerRevenue', 0) or 0),
                        'recommendedPartNo': recommended,
                        'recommendedDescription': assoc['recommended_description'] or '',
                        'reason': assoc['reason'] or '',
                        'confidence': float(assoc['confidence'] or 0),
                    })
            except Exception as qe:
                logger.warning(f"Missed opp query failed for {trigger}->{recommended}: {qe}")
                continue

        # Deduplicate by WONo + recommendedPartNo (a WO can only miss once per recommendation)
        seen = set()
        deduped = []
        for m in all_missed:
            key = (m['woNo'], m['recommendedPartNo'])
            if key not in seen:
                seen.add(key)
                deduped.append(m)

        # Aggregate by rep
        by_rep = {}
        for m in deduped:
            rep = m['salesman']
            if rep not in by_rep:
                by_rep[rep] = {'salesman': rep, 'missedCount': 0, 'triggerRevenue': 0}
            by_rep[rep]['missedCount'] += 1
            by_rep[rep]['triggerRevenue'] += m['triggerRevenue']
        by_rep_list = sorted(by_rep.values(), key=lambda x: x['missedCount'], reverse=True)

        # Aggregate by month
        by_month = {}
        for m in deduped:
            key = f"{m['year']}-{str(m['month']).zfill(2)}"
            if key not in by_month:
                by_month[key] = {'yearMonth': key, 'year': m['year'], 'month': m['month'], 'missedCount': 0}
            by_month[key]['missedCount'] += 1
        by_month_list = sorted(by_month.values(), key=lambda x: x['yearMonth'])

        return jsonify({
            'missedOpportunities': deduped[:500],  # cap at 500 rows for performance
            'total': len(deduped),
            'summary': {
                'totalMissed': len(deduped),
                'uniqueWOs': len(set(m['woNo'] for m in deduped)),
            },
            'byRep': by_rep_list,
            'byMonth': by_month_list,
            'dateRange': {'startDate': start_date, 'endDate': end_date},
        }), 200
    except Exception as e:
        logger.error(f"Error getting missed opportunities: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ── POST /ai-suggest — use AI to suggest reason/description for a part pair ───
@parts_associations_bp.route('/ai-suggest', methods=['POST'])
@jwt_required()
def ai_suggest():
    """
    Use OpenAI to suggest why two parts are related and what the upsell pitch should be.
    Body: {triggerPartNo, triggerDescription, recommendedPartNo, recommendedDescription}
    """
    try:
        import os
        from openai import OpenAI
        data = request.get_json() or {}
        trigger_no = data.get('triggerPartNo', '')
        trigger_desc = data.get('triggerDescription', '')
        rec_no = data.get('recommendedPartNo', '')
        rec_desc = data.get('recommendedDescription', '')

        client = OpenAI()
        prompt = (
            f"You are an expert parts advisor for a material handling equipment dealership (forklifts, reach trucks, pallet jacks).\n"
            f"A customer is buying: {trigger_no} — {trigger_desc}\n"
            f"We want to recommend: {rec_no} — {rec_desc}\n\n"
            f"In 1-2 sentences, explain WHY the customer likely needs the recommended part when buying the trigger part, "
            f"and give the parts rep a natural, helpful upsell phrase they can say to the customer. "
            f"Be specific and practical. Do not use jargon."
        )
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=150,
            temperature=0.4,
        )
        suggestion = response.choices[0].message.content.strip()
        return jsonify({'suggestion': suggestion}), 200
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}")
        return jsonify({'error': str(e)}), 500
