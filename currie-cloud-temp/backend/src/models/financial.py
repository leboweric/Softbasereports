"""
Currie Cloud Platform - Normalized Financial Data Models

These models store financial data extracted from various ERP/DMS systems
in a standardized format, enabling cross-dealer reporting and benchmarking.
"""
from datetime import datetime
from .database import db


class ReportingPeriod(db.Model):
    """
    A reporting period for a dealer (typically monthly).
    All financial data is associated with a reporting period.
    """
    __tablename__ = 'reporting_periods'

    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)

    # Period definition
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.String(20), default='monthly')  # monthly, quarterly, annual

    # Status
    status = db.Column(db.String(20), default='draft')  # draft, submitted, approved, locked

    # Submission tracking
    submitted_at = db.Column(db.DateTime)
    submitted_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(100))

    # Data source
    data_source = db.Column(db.String(50))  # 'auto_sync', 'manual_entry', 'file_upload'
    sync_job_id = db.Column(db.Integer, db.ForeignKey('data_sync_jobs.id'))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department_financials = db.relationship('DepartmentFinancial', backref='reporting_period', lazy='dynamic')
    expense_allocations = db.relationship('ExpenseAllocation', backref='reporting_period', lazy='dynamic')
    operational_metrics = db.relationship('OperationalMetric', backref='reporting_period', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'dealer_id': self.dealer_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'period_type': self.period_type,
            'status': self.status,
            'data_source': self.data_source
        }


class DepartmentFinancial(db.Model):
    """
    Financial data by department for a reporting period.
    This is the core P&L data normalized across all ERP systems.
    """
    __tablename__ = 'department_financials'

    id = db.Column(db.Integer, primary_key=True)
    reporting_period_id = db.Column(db.Integer, db.ForeignKey('reporting_periods.id'), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)

    # Department classification
    department = db.Column(db.String(50), nullable=False)
    # 'new_equipment', 'used_equipment', 'rental', 'service', 'parts', 'trucking', 'other'

    # Revenue
    gross_sales = db.Column(db.Numeric(15, 2), default=0)
    discounts = db.Column(db.Numeric(15, 2), default=0)
    net_sales = db.Column(db.Numeric(15, 2), default=0)

    # Cost
    cost_of_goods_sold = db.Column(db.Numeric(15, 2), default=0)

    # Gross Profit (calculated)
    gross_profit = db.Column(db.Numeric(15, 2), default=0)
    gross_profit_margin = db.Column(db.Numeric(8, 4), default=0)

    # Units (where applicable)
    units_sold = db.Column(db.Integer, default=0)
    average_sale_price = db.Column(db.Numeric(15, 2), default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_derived_fields(self):
        """Calculate gross profit and margin from raw data."""
        self.net_sales = (self.gross_sales or 0) - (self.discounts or 0)
        self.gross_profit = self.net_sales - (self.cost_of_goods_sold or 0)
        if self.net_sales and self.net_sales > 0:
            self.gross_profit_margin = self.gross_profit / self.net_sales
        else:
            self.gross_profit_margin = 0

    def to_dict(self):
        return {
            'id': self.id,
            'department': self.department,
            'gross_sales': float(self.gross_sales) if self.gross_sales else 0,
            'discounts': float(self.discounts) if self.discounts else 0,
            'net_sales': float(self.net_sales) if self.net_sales else 0,
            'cost_of_goods_sold': float(self.cost_of_goods_sold) if self.cost_of_goods_sold else 0,
            'gross_profit': float(self.gross_profit) if self.gross_profit else 0,
            'gross_profit_margin': float(self.gross_profit_margin) if self.gross_profit_margin else 0,
            'units_sold': self.units_sold,
            'average_sale_price': float(self.average_sale_price) if self.average_sale_price else 0
        }


class ExpenseAllocation(db.Model):
    """
    Expense allocations by department and category.
    """
    __tablename__ = 'expense_allocations'

    id = db.Column(db.Integer, primary_key=True)
    reporting_period_id = db.Column(db.Integer, db.ForeignKey('reporting_periods.id'), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)

    # Expense classification
    expense_category = db.Column(db.String(50), nullable=False)
    # 'personnel', 'operating', 'occupancy', 'ga', 'other'

    department = db.Column(db.String(50))  # Which department this expense is allocated to

    # Amount
    amount = db.Column(db.Numeric(15, 2), default=0)

    # Allocation method
    allocation_method = db.Column(db.String(50))  # 'direct', 'headcount', 'revenue', 'sqft', 'custom'

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'expense_category': self.expense_category,
            'department': self.department,
            'amount': float(self.amount) if self.amount else 0,
            'allocation_method': self.allocation_method
        }


class OperationalMetric(db.Model):
    """
    Operational KPIs and metrics for a reporting period.
    Flexible key-value storage for various metrics.
    """
    __tablename__ = 'operational_metrics'

    id = db.Column(db.Integer, primary_key=True)
    reporting_period_id = db.Column(db.Integer, db.ForeignKey('reporting_periods.id'), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)

    # Metric definition
    metric_name = db.Column(db.String(100), nullable=False)
    metric_category = db.Column(db.String(50))  # 'service', 'parts', 'rental', 'ar', 'inventory'
    metric_value = db.Column(db.Numeric(15, 4))
    metric_unit = db.Column(db.String(50))  # 'count', 'dollars', 'percent', 'days', etc.

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_category': self.metric_category,
            'metric_value': float(self.metric_value) if self.metric_value else 0,
            'metric_unit': self.metric_unit
        }


# Common metrics that should be captured
STANDARD_METRICS = {
    'service': [
        ('technician_count', 'count', 'Number of service technicians'),
        ('service_calls_per_day', 'count', 'Average service calls per day'),
        ('labor_efficiency', 'percent', 'Labor efficiency rate'),
        ('work_orders_open', 'count', 'Open work orders'),
        ('work_orders_completed', 'count', 'Completed work orders this period'),
    ],
    'parts': [
        ('parts_inventory_value', 'dollars', 'Total parts inventory value'),
        ('parts_turnover_rate', 'ratio', 'Parts inventory turnover'),
        ('fill_rate', 'percent', 'Parts fill rate'),
    ],
    'rental': [
        ('fleet_size', 'count', 'Total rental fleet units'),
        ('utilization_rate', 'percent', 'Fleet utilization rate'),
        ('units_on_rent', 'count', 'Units currently on rent'),
    ],
    'ar': [
        ('ar_total', 'dollars', 'Total accounts receivable'),
        ('ar_current', 'dollars', 'AR current (0-30 days)'),
        ('ar_30_60', 'dollars', 'AR 31-60 days'),
        ('ar_60_90', 'dollars', 'AR 61-90 days'),
        ('ar_over_90', 'dollars', 'AR over 90 days'),
        ('dso', 'days', 'Days sales outstanding'),
    ],
}
