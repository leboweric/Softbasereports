    @reports_bp.route('/departments/customer-profitability', methods=['GET'])
    @jwt_required()
    def get_customer_profitability():
        """
        Get comprehensive customer profitability analysis.
        Shows all customers with revenue vs costs, margin analysis, and actionable recommendations.
        
        Includes:
        - All revenue sources (not just maintenance contracts)
        - Labor costs from work orders
        - Parts costs from work orders
        - Health status and action recommendations
        """
        try:
            from datetime import datetime
            db = get_db()
            
            # Get date parameters from query string
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            min_revenue = request.args.get('min_revenue', 0)
            
            # Build date filter based on parameters
            if start_date and end_date:
                # Custom date range
                date_filter = f"AND i.InvoiceDate >= '{start_date}' AND i.InvoiceDate <= '{end_date}'"
                wo_date_filter = f"AND wo.DateCompleted >= '{start_date}' AND wo.DateCompleted <= '{end_date}'"
            else:
                # Default: trailing 12 months
                date_filter = "AND i.InvoiceDate >= DATEADD(month, -12, GETDATE())"
                wo_date_filter = "AND wo.DateCompleted >= DATEADD(month, -12, GETDATE())"

            # Get revenue by customer (all sale codes)
            customer_revenue_query = """
            SELECT
                i.ShipTo as customer_number,
                COALESCE(
                    c.Name,
                    CASE 
                        WHEN bc.Name IS NOT NULL THEN bc.Name + ' (Location #' + i.ShipTo + ')'
                        ELSE 'Unknown'
                    END
                ) as customer_name,
                COUNT(*) as invoice_count,
                MIN(i.InvoiceDate) as first_invoice,
                MAX(i.InvoiceDate) as last_invoice,
                SUM(COALESCE(i.GrandTotal, 0)) as total_revenue
            FROM [ben002].InvoiceReg i
            LEFT JOIN [ben002].Customer c ON i.ShipTo = c.Number
            LEFT JOIN [ben002].Customer bc ON i.BillTo = bc.Number
            WHERE 1=1
                {date_filter}
                AND i.ShipTo IS NOT NULL
                AND i.ShipTo != ''
            GROUP BY i.ShipTo, c.Name, bc.Name
            HAVING SUM(COALESCE(i.GrandTotal, 0)) >= {min_revenue}
            ORDER BY total_revenue DESC
            """.format(date_filter=date_filter, min_revenue=min_revenue)

            customer_revenue_results = db.execute_query(customer_revenue_query)

            # Get labor costs by customer
            labor_costs_query = """
            SELECT
                wo.ShipTo as customer_number,
                SUM(COALESCE(wol.Cost, 0)) as total_labor_cost,
                SUM(COALESCE(wol.Hours, 0)) as total_hours
            FROM [ben002].WO wo
            INNER JOIN [ben002].WOLabor wol ON wo.WONo = wol.WONo
            WHERE 1=1
                {wo_date_filter}
                AND wo.ShipTo IS NOT NULL
                AND wo.ShipTo != ''
            GROUP BY wo.ShipTo
            """.format(wo_date_filter=wo_date_filter)

            labor_costs_results = db.execute_query(labor_costs_query)

            # Get parts costs by customer
            parts_costs_query = """
            SELECT
                wo.ShipTo as customer_number,
                SUM(COALESCE(wop.Cost, 0)) as total_parts_cost
            FROM [ben002].WO wo
            INNER JOIN [ben002].WOParts wop ON wo.WONo = wop.WONo
            WHERE 1=1
                {wo_date_filter}
                AND wo.ShipTo IS NOT NULL
                AND wo.ShipTo != ''
            GROUP BY wo.ShipTo
            """.format(wo_date_filter=wo_date_filter)

            parts_costs_results = db.execute_query(parts_costs_query)

            # Get misc costs by customer
            misc_costs_query = """
            SELECT
                wo.ShipTo as customer_number,
                SUM(COALESCE(wom.Cost, 0)) as total_misc_cost
            FROM [ben002].WO wo
            INNER JOIN [ben002].WOMisc wom ON wo.WONo = wom.WONo
            WHERE 1=1
                {wo_date_filter}
                AND wo.ShipTo IS NOT NULL
                AND wo.ShipTo != ''
            GROUP BY wo.ShipTo
            """.format(wo_date_filter=wo_date_filter)

            misc_costs_results = db.execute_query(misc_costs_query)

            # Build cost lookups
            labor_costs_by_customer = {row['customer_number']: {
                'labor_cost': float(row['total_labor_cost'] or 0),
                'hours': float(row['total_hours'] or 0)
            } for row in labor_costs_results}

            parts_costs_by_customer = {row['customer_number']: float(row['total_parts_cost'] or 0) 
                                      for row in parts_costs_results}

            misc_costs_by_customer = {row['customer_number']: float(row['total_misc_cost'] or 0) 
                                     for row in misc_costs_results}

            # Build customer data with profitability analysis
            customer_data = []
            total_revenue = 0
            total_cost = 0
            healthy_count = 0
            warning_count = 0
            critical_count = 0
            revenue_at_risk = 0

            for row in customer_revenue_results:
                customer_num = row['customer_number']
                revenue = float(row['total_revenue'] or 0)
                
                # Get costs for this customer
                labor_info = labor_costs_by_customer.get(customer_num, {'labor_cost': 0, 'hours': 0})
                labor_cost = labor_info['labor_cost']
                parts_cost = parts_costs_by_customer.get(customer_num, 0)
                misc_cost = misc_costs_by_customer.get(customer_num, 0)
                
                total_customer_cost = labor_cost + parts_cost + misc_cost
                gross_profit = revenue - total_customer_cost
                margin = (gross_profit / revenue * 100) if revenue > 0 else 0
                
                # Determine health status
                if margin >= 30:
                    health_status = 'healthy'
                    healthy_count += 1
                elif margin >= 0:
                    health_status = 'warning'
                    warning_count += 1
                else:
                    health_status = 'critical'
                    critical_count += 1
                    revenue_at_risk += revenue
                
                # Determine action recommendation
                if margin >= 30:
                    action = 'Maintain'
                    message = 'Healthy profit margin - maintain current pricing'
                    recommended_increase = None
                    recommended_increase_pct = None
                elif margin >= 15:
                    action = 'Monitor'
                    # Calculate increase needed to hit 30% margin
                    target_margin = 0.30
                    target_revenue = total_customer_cost / (1 - target_margin)
                    recommended_increase = target_revenue - revenue
                    recommended_increase_pct = (recommended_increase / revenue * 100) if revenue > 0 else 0
                    message = f'Below industry standard (30%) - consider {recommended_increase_pct:.1f}% price increase'
                elif margin >= 0:
                    action = 'Raise Prices'
                    target_margin = 0.30
                    target_revenue = total_customer_cost / (1 - target_margin)
                    recommended_increase = target_revenue - revenue
                    recommended_increase_pct = (recommended_increase / revenue * 100) if revenue > 0 else 0
                    message = f'Below acceptable margin - {recommended_increase_pct:.1f}% price increase recommended'
                else:
                    # Unprofitable
                    if revenue >= 10000:
                        action = 'Urgent - Raise Prices'
                        target_margin = 0.30
                        target_revenue = total_customer_cost / (1 - target_margin)
                        recommended_increase = target_revenue - revenue
                        recommended_increase_pct = (recommended_increase / revenue * 100) if revenue > 0 else 0
                        message = f'Losing ${abs(gross_profit):,.2f}/year - immediate {recommended_increase_pct:.1f}% price increase required'
                    else:
                        action = 'Consider Termination'
                        recommended_increase = None
                        recommended_increase_pct = None
                        message = f'Unprofitable small account - losing ${abs(gross_profit):,.2f}/year'
                
                customer_data.append({
                    'customer_number': customer_num,
                    'customer_name': row['customer_name'] or 'Unknown',
                    'invoice_count': int(row['invoice_count'] or 0),
                    'first_invoice': row['first_invoice'].strftime('%Y-%m-%d') if row['first_invoice'] else None,
                    'last_invoice': row['last_invoice'].strftime('%Y-%m-%d') if row['last_invoice'] else None,
                    'total_revenue': round(revenue, 2),
                    'labor_cost': round(labor_cost, 2),
                    'parts_cost': round(parts_cost, 2),
                    'misc_cost': round(misc_cost, 2),
                    'total_cost': round(total_customer_cost, 2),
                    'gross_profit': round(gross_profit, 2),
                    'margin_percent': round(margin, 1),
                    'health_status': health_status,
                    'action': action,
                    'message': message,
                    'recommended_increase': round(recommended_increase, 2) if recommended_increase else None,
                    'recommended_increase_pct': round(recommended_increase_pct, 1) if recommended_increase_pct else None,
                    'total_hours': round(labor_info['hours'], 1)
                })
                
                total_revenue += revenue
                total_cost += total_customer_cost

            # Calculate overall metrics
            total_profit = total_revenue - total_cost
            overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

            summary = {
                'total_customers': len(customer_data),
                'healthy_count': healthy_count,
                'warning_count': warning_count,
                'critical_count': critical_count,
                'total_revenue': round(total_revenue, 2),
                'total_cost': round(total_cost, 2),
                'total_profit': round(total_profit, 2),
                'overall_margin': round(overall_margin, 1),
                'revenue_at_risk': round(revenue_at_risk, 2),
                'healthy_pct': round(healthy_count / len(customer_data) * 100, 1) if customer_data else 0,
                'warning_pct': round(warning_count / len(customer_data) * 100, 1) if customer_data else 0,
                'critical_pct': round(critical_count / len(customer_data) * 100, 1) if customer_data else 0
            }

            # Filter for "fire list" - unprofitable small accounts
            fire_list = [c for c in customer_data if c['margin_percent'] < 0 and c['total_revenue'] < 10000]
            fire_list.sort(key=lambda x: x['gross_profit'])  # Sort by worst losses first

            return jsonify({
                'success': True,
                'summary': summary,
                'customers': customer_data,
                'fire_list': fire_list,
                'notes': {
                    'revenue': 'All invoice revenue (all sale codes)',
                    'costs': 'Labor + Parts + Misc from Work Orders',
                    'health_healthy': 'Margin >= 30%',
                    'health_warning': 'Margin 0-30%',
                    'health_critical': 'Margin < 0% (unprofitable)',
                    'fire_list_criteria': 'Margin < 0% AND Revenue < $10,000'
                }
            })

        except Exception as e:
            logger.error(f"Error getting customer profitability: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
