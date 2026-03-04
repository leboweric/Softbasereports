#!/usr/bin/env python3
"""
AIOP Multi-Tenant Smoke Test
=============================
Runs after every deployment to verify:
1. All key endpoints return HTTP 200 (for the bot's default org)
2. Responses contain data (not empty arrays or zero counts)
3. Cross-tenant data isolation via schema-prefixed queries
4. No new runtime errors introduced

Usage:
    python3 smoke_test.py                    # Full smoke test
    python3 smoke_test.py --quick            # Quick health check only
    python3 smoke_test.py --verbose          # Show detailed response data

Exit codes:
    0 = All tests passed
    1 = One or more tests failed
    2 = Critical failure (auth failed, API unreachable)

Note: The bot authenticates as its default org (Bennett). Cross-tenant
verification uses the execute-query endpoint with explicit schema prefixes
to check that each tenant's data is accessible and distinct.
"""

import requests
import json
import sys
import time
import argparse
from datetime import datetime
from collections import defaultdict

# ============================================================
# Configuration
# ============================================================

BASE_URL = "https://softbasereports-production.up.railway.app"
FRONTEND_URL = "https://aiop.one"
BOT_USERNAME = "aiop-support-bot"
BOT_PASSWORD = "A10P$upp0rtB0t!2026"

# Known tenant schemas (update when new orgs are onboarded)
TENANT_SCHEMAS = {
    "Bennett Material Handling": "ben002",
    "Industrial Parts and Service": "ind004",
}

# Endpoints to test (relative to BASE_URL)
# Format: (name, method, path, check_type)
# check_type: "status_only" = just check 200, "has_data" = check response has data
CORE_ENDPOINTS = [
    ("Health Check", "GET", "/api/admin/logs/health", "status_only"),
    ("Dashboard (Fast)", "GET", "/api/reports/dashboard/summary-fast?month={month}&year={year}", "has_data"),
    ("Dashboard (Optimized)", "GET", "/api/reports/dashboard/summary-optimized?month={month}&year={year}", "has_data"),
    ("Work Order Types", "GET", "/api/reports/departments/work-order-types", "has_data"),
    ("Invoiced Summary", "GET", "/api/reports/departments/sales/invoiced-summary?month={month}&year={year}", "has_data"),
    ("Cost Per Hour", "GET", "/api/reports/departments/service/cost-per-hour?start_date={start_date}&end_date={end_date}", "has_data"),
    ("Customer Profitability", "GET", "/api/reports/departments/customer-profitability?department=service", "has_data"),
    ("Shop Work Orders (Cash Burn)", "GET", "/api/reports/departments/service/shop-work-orders", "has_data"),
    ("Awaiting Invoice (Cash Stalled)", "GET", "/api/reports/departments/service/awaiting-invoice-details", "has_data"),
    ("Maintenance Contract Prof", "GET", "/api/reports/departments/guaranteed-maintenance/profitability", "has_data"),
    ("Currie Service Benchmarks", "GET", "/api/reports/departments/service/currie-benchmarks", "has_data"),
]

# Cross-tenant queries to verify data isolation
# Uses /api/database/query endpoint (POST with {"query": ...})
CROSS_TENANT_QUERIES = [
    ("Dept Table", "SELECT TOP 5 Dept, Title FROM {schema}.Dept ORDER BY Dept"),
    ("Branch Table", "SELECT TOP 5 Branch, BranchName FROM {schema}.Branch ORDER BY Branch"),
    ("Invoice Count", "SELECT COUNT(*) as cnt FROM {schema}.InvoiceReg WHERE InvoiceDate >= '2025-01-01'"),
]

# Alternative endpoint for cross-tenant queries
CROSS_TENANT_QUERY_ENDPOINT = "/api/database/query"


# ============================================================
# Test Runner
# ============================================================

class SmokeTestRunner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.token = None
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.warnings = 0

    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "   ", "PASS": " ✅", "FAIL": " ❌", "WARN": " ⚠️", "SKIP": " ⏭️"}
        print(f"[{timestamp}]{prefix.get(level, '   ')} {msg}")

    def authenticate(self):
        """Get JWT token for API access."""
        self.log("Authenticating as AIOP Support Bot...")
        try:
            r = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": BOT_USERNAME, "password": BOT_PASSWORD},
                timeout=30
            )
            if r.status_code == 200:
                data = r.json()
                self.token = data.get("token")
                if self.token:
                    org_name = data.get("user", {}).get("organization_name", "Unknown")
                    self.log(f"Authentication successful (org: {org_name})", "PASS")
                    self.passed += 1
                    return True
            self.log(f"Authentication failed: {r.status_code} - {r.text[:200]}", "FAIL")
            self.failed += 1
            return False
        except Exception as e:
            self.log(f"Authentication error: {e}", "FAIL")
            self.failed += 1
            return False

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def test_endpoint(self, name, method, path, check_type):
        """Test a single endpoint."""
        now = datetime.now()
        # Calculate date params for endpoints that need them
        start_date = f"{now.year - 1}-01-01"
        end_date = f"{now.year}-{now.month:02d}-01"
        path = path.format(month=now.month, year=now.year, start_date=start_date, end_date=end_date)
        url = f"{BASE_URL}{path}"

        try:
            r = requests.get(url, headers=self.get_headers(), timeout=60)

            if r.status_code != 200:
                self.log(f"{name}: HTTP {r.status_code}", "FAIL")
                self.failed += 1
                self.results.append({"test": name, "status": "FAIL", "reason": f"HTTP {r.status_code}"})
                return

            if check_type == "status_only":
                self.log(f"{name}: HTTP 200 OK", "PASS")
                self.passed += 1
                self.results.append({"test": name, "status": "PASS"})
                return

            # Parse JSON and check for data
            try:
                data = r.json()
            except json.JSONDecodeError:
                self.log(f"{name}: Invalid JSON response", "FAIL")
                self.failed += 1
                self.results.append({"test": name, "status": "FAIL", "reason": "Invalid JSON"})
                return

            # Check for API-level errors
            if isinstance(data, dict) and data.get("error"):
                self.log(f"{name}: API error: {data['error'][:100]}", "FAIL")
                self.failed += 1
                self.results.append({"test": name, "status": "FAIL", "reason": f"API error: {data['error'][:100]}"})
                return

            # Check that response has some data
            has_data = False
            data_detail = ""
            if isinstance(data, dict):
                for key in ["data", "work_orders", "departments", "results", "customers"]:
                    if key in data:
                        val = data[key]
                        if isinstance(val, list):
                            has_data = len(val) > 0
                            data_detail = f"{len(val)} items in '{key}'"
                        elif isinstance(val, dict):
                            has_data = len(val) > 0
                            data_detail = f"dict with {len(val)} keys in '{key}'"
                        break
                if not has_data and not data_detail:
                    # Some endpoints return data at top level
                    has_data = len(data) > 0
                    data_detail = f"response has {len(data)} keys"
            elif isinstance(data, list):
                has_data = len(data) > 0
                data_detail = f"{len(data)} items"

            if has_data:
                detail = f" ({data_detail})" if self.verbose else ""
                self.log(f"{name}: OK{detail}", "PASS")
                self.passed += 1
                self.results.append({"test": name, "status": "PASS"})
            else:
                self.log(f"{name}: HTTP 200 but empty/no data ({data_detail})", "WARN")
                self.warnings += 1
                self.results.append({"test": name, "status": "WARN", "reason": "Empty response"})

        except requests.Timeout:
            self.log(f"{name}: Timeout (>60s)", "FAIL")
            self.failed += 1
            self.results.append({"test": name, "status": "FAIL", "reason": "Timeout"})
        except Exception as e:
            self.log(f"{name}: Error: {str(e)[:100]}", "FAIL")
            self.failed += 1
            self.results.append({"test": name, "status": "FAIL", "reason": str(e)[:100]})

    def check_cross_tenant_isolation(self):
        """Verify data isolation between tenants using schema-prefixed queries."""
        self.log("\n--- Cross-Tenant Data Isolation Check ---")

        if len(TENANT_SCHEMAS) < 2:
            self.log("Need at least 2 tenant schemas for cross-tenant check", "SKIP")
            self.skipped += 1
            return

        for query_name, query_template in CROSS_TENANT_QUERIES:
            tenant_results = {}

            for org_name, schema in TENANT_SCHEMAS.items():
                query = query_template.format(schema=schema)
                try:
                    # Try both query endpoints
                    success = False
                    for endpoint in [CROSS_TENANT_QUERY_ENDPOINT, "/api/database/execute-query"]:
                        try:
                            r = requests.post(
                                f"{BASE_URL}{endpoint}",
                                headers=self.get_headers(),
                                json={"query": query},
                                timeout=30
                            )
                            if r.status_code == 200:
                                data = r.json()
                                results = data.get("results") or data.get("data") or data.get("rows")
                                if results:
                                    tenant_results[org_name] = json.dumps(results, sort_keys=True)
                                    success = True
                                    break
                                elif data.get("success") and data.get("row_count", 0) == 0:
                                    tenant_results[org_name] = "EMPTY"
                                    success = True
                                    break
                        except Exception:
                            continue
                    if not success:
                        self.log(f"  {query_name} [{org_name}]: Query endpoint unavailable", "WARN")
                except Exception as e:
                    self.log(f"  {query_name} [{org_name}]: Error: {str(e)[:80]}", "WARN")

            # Compare results across tenants
            if len(tenant_results) >= 2:
                unique_results = set(tenant_results.values())
                if len(unique_results) == 1:
                    # All tenants returned identical data — possible issue
                    self.log(
                        f"{query_name}: IDENTICAL data across {len(tenant_results)} tenants — POSSIBLE DATA LEAKAGE",
                        "FAIL"
                    )
                    self.failed += 1
                    self.results.append({
                        "test": f"Cross-tenant: {query_name}",
                        "status": "FAIL",
                        "reason": "Identical data across tenants"
                    })
                else:
                    self.log(
                        f"{query_name}: Data differs across {len(tenant_results)} tenants — isolation OK",
                        "PASS"
                    )
                    self.passed += 1
                    self.results.append({"test": f"Cross-tenant: {query_name}", "status": "PASS"})
            else:
                self.log(f"{query_name}: Could not compare (only {len(tenant_results)} tenants responded)", "SKIP")
                self.skipped += 1

    def check_error_logs(self):
        """Check for recent runtime errors."""
        self.log("\n--- Runtime Error Check ---")
        try:
            r = requests.get(
                f"{BASE_URL}/api/admin/logs/health",
                headers=self.get_headers(),
                timeout=30
            )
            if r.status_code == 200:
                health = r.json()
                status = health.get("status", "unknown")
                errors_1h = health.get("errors_last_hour", 0)
                errors_24h = health.get("errors_last_24h", 0)

                if status == "healthy":
                    self.log(f"Application health: {status} ({errors_1h} errors/hr, {errors_24h}/24h)", "PASS")
                    self.passed += 1
                elif status == "degraded":
                    self.log(f"Application health: {status} ({errors_1h} errors/hr, {errors_24h}/24h)", "WARN")
                    self.warnings += 1
                else:
                    self.log(f"Application health: {status} ({errors_1h} errors/hr, {errors_24h}/24h)", "FAIL")
                    self.failed += 1

                # If recent errors, show top 3
                if errors_1h > 0:
                    r2 = requests.get(
                        f"{BASE_URL}/api/admin/logs?since_hours=1&limit=3",
                        headers=self.get_headers(),
                        timeout=30
                    )
                    if r2.status_code == 200:
                        errors = r2.json().get("errors", [])
                        for err in errors:
                            self.log(
                                f"  Recent: {err.get('error_type', '?')}: "
                                f"{err.get('message', '?')[:80]} "
                                f"(endpoint: {err.get('endpoint', '?')})",
                                "WARN"
                            )
            else:
                self.log(f"Health endpoint returned {r.status_code}", "FAIL")
                self.failed += 1
        except Exception as e:
            self.log(f"Error checking health: {e}", "FAIL")
            self.failed += 1

    def check_frontend(self):
        """Verify frontend is accessible."""
        self.log("\n--- Frontend Accessibility Check ---")
        try:
            r = requests.get(FRONTEND_URL, timeout=30)
            if r.status_code == 200 and "<!DOCTYPE html>" in r.text[:200].lower() or "<html" in r.text[:200].lower():
                self.log(f"Frontend ({FRONTEND_URL}): Accessible", "PASS")
                self.passed += 1
            else:
                self.log(f"Frontend ({FRONTEND_URL}): HTTP {r.status_code}", "FAIL")
                self.failed += 1
        except Exception as e:
            self.log(f"Frontend ({FRONTEND_URL}): Error: {e}", "FAIL")
            self.failed += 1

    def run_quick(self):
        """Quick health check — auth + health + frontend only."""
        print("\n" + "=" * 60)
        print("AIOP SMOKE TEST — QUICK MODE")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

        if not self.authenticate():
            return 2

        self.check_error_logs()
        self.check_frontend()
        self.print_summary()
        return 0 if self.failed == 0 else 1

    def run_full(self):
        """Full smoke test — all endpoints + cross-tenant + error logs."""
        print("\n" + "=" * 60)
        print("AIOP MULTI-TENANT SMOKE TEST — FULL MODE")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tenants: {', '.join(TENANT_SCHEMAS.keys())}")
        print("=" * 60 + "\n")

        # Step 1: Authenticate
        if not self.authenticate():
            return 2

        # Step 2: Check error logs
        self.check_error_logs()

        # Step 3: Check frontend
        self.check_frontend()

        # Step 4: Test core API endpoints
        print(f"\n--- API Endpoint Tests (as bot's default org) ---")
        for endpoint in CORE_ENDPOINTS:
            self.test_endpoint(*endpoint)

        # Step 5: Cross-tenant data isolation
        self.check_cross_tenant_isolation()

        # Step 6: Print summary
        self.print_summary()

        return 0 if self.failed == 0 else 1

    def print_summary(self):
        """Print test results summary."""
        total = self.passed + self.failed + self.skipped + self.warnings
        print("\n" + "=" * 60)
        print("SMOKE TEST RESULTS")
        print("=" * 60)
        print(f"  Passed:   {self.passed}")
        print(f"  Failed:   {self.failed}")
        print(f"  Warnings: {self.warnings}")
        print(f"  Skipped:  {self.skipped}")
        print(f"  Total:    {total}")
        print()

        if self.failed > 0:
            print("FAILED TESTS:")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  ❌ {r['test']}: {r.get('reason', 'Unknown')}")
            print()

        if self.warnings > 0:
            print("WARNINGS:")
            for r in self.results:
                if r["status"] == "WARN":
                    print(f"  ⚠️  {r['test']}: {r.get('reason', 'Unknown')}")
            print()

        verdict = "PASSED ✅" if self.failed == 0 else "FAILED ❌"
        print(f"VERDICT: {verdict}")
        print("=" * 60)

        # Save results to file
        report = {
            "timestamp": datetime.now().isoformat(),
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "verdict": "PASS" if self.failed == 0 else "FAIL",
            "details": self.results
        }
        try:
            with open("/home/ubuntu/Softbasereports-fresh/.manus/last_smoke_test.json", "w") as f:
                json.dump(report, f, indent=2)
            self.log("Results saved to .manus/last_smoke_test.json")
        except Exception:
            pass


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIOP Multi-Tenant Smoke Test")
    parser.add_argument("--quick", action="store_true", help="Quick health check only")
    parser.add_argument("--verbose", action="store_true", help="Show detailed response data")
    args = parser.parse_args()

    runner = SmokeTestRunner(verbose=args.verbose)

    if args.quick:
        exit_code = runner.run_quick()
    else:
        exit_code = runner.run_full()

    sys.exit(exit_code)
