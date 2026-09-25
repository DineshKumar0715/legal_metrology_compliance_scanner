"""
Official Legal Metrology Case Repository & Database Subsystem.
Manages inspection history, violation records, physical verification logs, and role-based accounts.
"""

import sqlite3
import json
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "metrology_cases.db")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    """Initializes schema and seeds initial accounts and historical inspection data."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        district TEXT NOT NULL,
        badge_number TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Products Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        brand TEXT,
        category TEXT,
        declared_qty TEXT,
        declared_mrp REAL,
        manufacturer TEXT,
        country_of_origin TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Inspections Table (with Supervisor Approval Workflow fields)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inspections (
        inspection_id TEXT PRIMARY KEY,
        product_id TEXT,
        product_name TEXT NOT NULL,
        brand TEXT,
        category TEXT,
        inspector_id TEXT NOT NULL,
        inspector_name TEXT NOT NULL,
        district TEXT NOT NULL,
        location_details TEXT,
        status TEXT NOT NULL,
        compliance_score REAL NOT NULL,
        violations_count INTEGER NOT NULL,
        physical_status TEXT NOT NULL,
        raw_text TEXT,
        declarations_json TEXT,
        pdf_path TEXT,
        timestamp TEXT NOT NULL,
        approval_status TEXT DEFAULT 'PENDING_REVIEW',
        supervisor_notes TEXT,
        compounding_fine REAL DEFAULT 0.0
    );
    """)

    # Violations Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        violation_id TEXT NOT NULL,
        inspection_id TEXT NOT NULL,
        rule_number TEXT NOT NULL,
        field_name TEXT NOT NULL,
        severity TEXT NOT NULL,
        description TEXT NOT NULL,
        observed_value TEXT,
        expected_condition TEXT,
        statutory_citation TEXT,
        evidence_crop TEXT,
        FOREIGN KEY (inspection_id) REFERENCES inspections (inspection_id)
    );
    """)

    # Physical Verification Records
    cur.execute("""
    CREATE TABLE IF NOT EXISTS physical_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id TEXT NOT NULL,
        declared_net_quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        measured_actual_quantity REAL NOT NULL,
        tare_weight REAL,
        deficit_or_excess REAL NOT NULL,
        deficit_percentage REAL NOT NULL,
        mpe_allowed REAL NOT NULL,
        is_within_mpe_limit INTEGER NOT NULL,
        status TEXT NOT NULL,
        remarks TEXT,
        instrument_id TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (inspection_id) REFERENCES inspections (inspection_id)
    );
    """)

    # Dynamic schema migration for existing database files
    cur.execute("PRAGMA table_info(inspections)")
    existing_cols = {row["name"] for row in cur.fetchall()}
    if "approval_status" not in existing_cols:
        cur.execute("ALTER TABLE inspections ADD COLUMN approval_status TEXT DEFAULT 'PENDING_REVIEW'")
    if "supervisor_notes" not in existing_cols:
        cur.execute("ALTER TABLE inspections ADD COLUMN supervisor_notes TEXT")
    if "compounding_fine" not in existing_cols:
        cur.execute("ALTER TABLE inspections ADD COLUMN compounding_fine REAL DEFAULT 0.0")

    conn.commit()

    # Seed Default Users if none exist
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        seed_users = [
            ("USR-INSP-01", "inspector", hash_password("inspector123"), "R. K. Sharma (Inspector)", "INSPECTOR", "Salem District", "LM-INSP-401", datetime.now().isoformat()),
            ("USR-SUP-01", "supervisor", hash_password("supervisor123"), "Dr. Anita Desai (Deputy Controller)", "SUPERVISOR", "State Enforcement HQ", "LM-SUP-102", datetime.now().isoformat()),
            ("USR-ADM-01", "admin", hash_password("admin123"), "National Metrology Admin", "ADMIN", "Central Metrology Directorate", "LM-DIR-001", datetime.now().isoformat()),
        ]
        cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)", seed_users)

    # Seed Sample Historical Enforcement Cases
    cur.execute("SELECT COUNT(*) FROM inspections")
    if cur.fetchone()[0] == 0:
        sample_inspections = [
            (
                "INSP-2026-0811",
                "PROD-101",
                "Nutri Delight Whole Wheat Biscuits 500g",
                "Nutri Delight",
                "Food & Bakery",
                "USR-INSP-01",
                "R. K. Sharma (Inspector)",
                "Salem District",
                "Central Supermarket, Salem",
                "COMPLIANT",
                100.0,
                0,
                "VERIFIED_COMPLIANT",
                "COMMODITY: Biscuits | NET QTY: 500 g | MRP Rs 95.00 (inclusive of all taxes) | Mfd by Golden Bake, Pune | Country of Origin: India",
                "{}",
                None,
                "2026-09-20T10:30:00",
                "APPROVED",
                "Verified and approved for standard distribution.",
                0.0
            ),
            (
                "INSP-2026-0812",
                "PROD-102",
                "Crispy Munchies Potato Chips 150gm",
                "Crispy Munchies",
                "Packaged Snacks",
                "USR-INSP-01",
                "R. K. Sharma (Inspector)",
                "Salem District",
                "Green Valley Hypermarket, Salem",
                "NON_COMPLIANT",
                66.7,
                2,
                "NOT_VERIFIED",
                "NET WT: 150 gm | MRP: Rs. 40 | Mfd by SnackTech Ltd | Best Before 6 months",
                "{}",
                None,
                "2026-09-21T14:15:00",
                "NOTICE_ISSUED",
                "Show-Cause Notice issued under Section 36(1). Compounding proposed.",
                25000.0
            ),
            (
                "INSP-2026-0813",
                "PROD-103",
                "Pure Glow Almond Body Lotion 400ml",
                "Pure Glow",
                "Personal Care & Cosmetics",
                "USR-INSP-01",
                "R. K. Sharma (Inspector)",
                "Pune District",
                "Aura Retail Hub, Pune",
                "PHYSICAL_VERIFICATION_REQUIRED",
                100.0,
                0,
                "NOT_VERIFIED",
                "NET VOL: 400 ml | MRP: Rs. 350 (incl of all taxes) | Mfd by GlowCare Ltd | Care: 1800-444-1111 | Country of Origin: India",
                "{}",
                None,
                "2026-09-22T16:45:00",
                "PENDING_REVIEW",
                "Awaiting field officer physical tare/net volume measurement report.",
                0.0
            ),
        ]
        cur.executemany("INSERT INTO inspections (inspection_id, product_id, product_name, brand, category, inspector_id, inspector_name, district, location_details, status, compliance_score, violations_count, physical_status, raw_text, declarations_json, pdf_path, timestamp, approval_status, supervisor_notes, compounding_fine) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_inspections)

        # Seed sample violation for 0812
        sample_violations = [
            ("VIOL-001", "INSP-2026-0812", "Rule 6(1)(c) & Rule 13", "Net Quantity Unit", "MAJOR", "Non-standard unit 'gm' used instead of standard 'g'.", "150 gm", "150 g", "PCR 2011 Rule 13", None),
            ("VIOL-002", "INSP-2026-0812", "Rule 6(1)(e)", "Maximum Retail Price (MRP)", "MAJOR", "MRP suffix 'inclusive of all taxes' absent.", "Rs. 40", "MRP Rs. 40 (inclusive of all taxes)", "PCR 2011 Rule 6(1)(e)", None),
        ]
        cur.executemany("INSERT INTO violations (violation_id, inspection_id, rule_number, field_name, severity, description, observed_value, expected_condition, statutory_citation, evidence_crop) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_violations)

    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

def authenticate_user(username: str, password: str, required_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Authenticates username & password against hashed store with optional role constraint."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, hash_password(password)))
    row = cur.fetchone()
    conn.close()
    if row:
        user_dict = dict(row)
        if required_role and user_dict.get("role") != required_role:
            return None
        return user_dict
    return None

def register_user(username: str, password: str, full_name: str, role: str, district: str, badge_number: str) -> Dict[str, Any]:
    """Registers a new officer account."""
    conn = get_db_connection()
    cur = conn.cursor()
    user_id = f"USR-{role[:3]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cur.execute("""
    INSERT INTO users (user_id, username, password_hash, full_name, role, district, badge_number, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, hash_password(password), full_name, role, district, badge_number, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "username": username,
        "full_name": full_name,
        "role": role,
        "district": district,
        "badge_number": badge_number
    }

def get_all_users() -> List[Dict[str, Any]]:
    """Fetches all registered officers for Admin management."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, full_name, role, district, badge_number, created_at FROM users ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_case_action(inspection_id: str, action: str, supervisor_notes: str, compounding_fine: float = 0.0) -> bool:
    """Updates supervisor decision on an inspection case."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE inspections
    SET approval_status = ?, supervisor_notes = ?, compounding_fine = ?
    WHERE inspection_id = ?
    """, (action, supervisor_notes, compounding_fine, inspection_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def save_inspection(
    inspection_id: str,
    product_name: str,
    brand: Optional[str],
    category: Optional[str],
    inspector_id: str,
    inspector_name: str,
    district: str,
    location_details: Optional[str],
    status: str,
    compliance_score: float,
    violations_count: int,
    physical_status: str,
    raw_text: str,
    declarations_dict: Dict[str, Any],
    violations_list: List[Any],
    physical_record: Optional[Any] = None,
    pdf_path: Optional[str] = None
) -> str:
    """Saves a complete inspection case into the repository."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO inspections (
        inspection_id, product_name, brand, category, inspector_id, inspector_name,
        district, location_details, status, compliance_score, violations_count,
        physical_status, raw_text, declarations_json, pdf_path, timestamp, approval_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW')
    """, (
        inspection_id, product_name, brand or "General Brand", category or "General Commodity",
        inspector_id, inspector_name, district, location_details or "Inspected on site",
        status, compliance_score, violations_count, physical_status, raw_text,
        json.dumps(declarations_dict, default=str), pdf_path, datetime.now().isoformat()
    ))

    # Save Violations
    for v in violations_list:
        v_dict = v if isinstance(v, dict) else v.model_dump()
        cur.execute("""
        INSERT INTO violations (
            violation_id, inspection_id, rule_number, field_name, severity,
            description, observed_value, expected_condition, statutory_citation, evidence_crop
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v_dict.get("violation_id", "VIOL-UNKNOWN"),
            inspection_id,
            v_dict.get("rule_number", "PCR 2011"),
            v_dict.get("field_name", "Statutory Field"),
            str(v_dict.get("severity", "MAJOR")),
            v_dict.get("description", "Non-compliant declaration"),
            v_dict.get("observed_value"),
            v_dict.get("expected_condition", "Statutory Format"),
            v_dict.get("statutory_citation", "Legal Metrology Act, 2009"),
            v_dict.get("evidence_crop_base64")
        ))

    # Save Physical Verification if present
    if physical_record:
        p_dict = physical_record if isinstance(physical_record, dict) else physical_record.model_dump()
        cur.execute("""
        INSERT INTO physical_verifications (
            inspection_id, declared_net_quantity, unit, measured_actual_quantity,
            tare_weight, deficit_or_excess, deficit_percentage, mpe_allowed,
            is_within_mpe_limit, status, remarks, instrument_id, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inspection_id,
            p_dict.get("declared_net_quantity", 0.0),
            p_dict.get("unit", "g"),
            p_dict.get("measured_actual_quantity", 0.0),
            p_dict.get("tare_weight", 0.0),
            p_dict.get("deficit_or_excess", 0.0),
            p_dict.get("deficit_percentage", 0.0),
            p_dict.get("max_permissible_error_allowed", 0.0),
            1 if p_dict.get("is_within_mpe_limit", True) else 0,
            p_dict.get("status", "VERIFIED"),
            p_dict.get("remarks", ""),
            p_dict.get("instrument_id", "STANDARD-CALIBRATED-SCALE-01"),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()
    return inspection_id

def get_inspections(
    query: Optional[str] = None,
    district: Optional[str] = None,
    status: Optional[str] = None,
    inspector_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Searches and filters inspection cases."""
    conn = get_db_connection()
    cur = conn.cursor()

    sql = "SELECT * FROM inspections WHERE 1=1"
    params: List[Any] = []

    if query:
        sql += " AND (product_name LIKE ? OR brand LIKE ? OR inspection_id LIKE ?)"
        q_param = f"%{query}%"
        params.extend([q_param, q_param, q_param])

    if district and district != "All Districts":
        sql += " AND district = ?"
        params.append(district)

    if status and status != "All Statuses":
        sql += " AND status = ?"
        params.append(status)

    if inspector_id:
        sql += " AND inspector_id = ?"
        params.append(inspector_id)

    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_inspection_details(inspection_id: str) -> Optional[Dict[str, Any]]:
    """Fetches complete inspection record including violations and physical verification data."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    insp = dict(row)

    # Fetch Violations
    cur.execute("SELECT * FROM violations WHERE inspection_id = ?", (inspection_id,))
    insp["violations"] = [dict(v) for v in cur.fetchall()]

    # Fetch Physical Verification
    cur.execute("SELECT * FROM physical_verifications WHERE inspection_id = ?", (inspection_id,))
    phys_row = cur.fetchone()
    insp["physical_verification"] = dict(phys_row) if phys_row else None

    conn.close()
    return insp

def get_dashboard_analytics() -> Dict[str, Any]:
    """Computes aggregated executive compliance metrics for enforcement dashboard."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM inspections")
    total_inspections = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inspections WHERE status = 'COMPLIANT'")
    compliant_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inspections WHERE status = 'NON_COMPLIANT'")
    non_compliant_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inspections WHERE status = 'PHYSICAL_VERIFICATION_REQUIRED'")
    physical_req_count = cur.fetchone()[0]

    # Violation Categories breakdown
    cur.execute("""
    SELECT field_name, COUNT(*) as cnt 
    FROM violations 
    GROUP BY field_name 
    ORDER BY cnt DESC 
    LIMIT 10
    """)
    violation_categories = [{"category": row[0], "count": row[1]} for row in cur.fetchall()]

    # District Distribution
    cur.execute("""
    SELECT district, COUNT(*) as cnt, SUM(CASE WHEN status = 'NON_COMPLIANT' THEN 1 ELSE 0 END) as violations
    FROM inspections 
    GROUP BY district
    """)
    district_data = [{"district": r[0], "total": r[1], "violations": r[2]} for r in cur.fetchall()]

    conn.close()

    compliance_rate = round((compliant_count / total_inspections) * 100.0, 1) if total_inspections > 0 else 0.0

    return {
        "total_inspections": total_inspections,
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
        "physical_verification_required_count": physical_req_count,
        "overall_compliance_rate": compliance_rate,
        "violation_categories": violation_categories,
        "district_distribution": district_data,
    }
