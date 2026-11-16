#!/usr/bin/env python3
"""
PathPilot AI — O*NET Database Loader
=====================================
Ingests the official O*NET database CSV files into PostgreSQL/Supabase.

Usage:
    python onet_loader.py --data-dir data/onet/ --env .env

Download O*NET data from:
    https://www.onetcenter.org/database.html
    → O*NET 29.0 Database → Download All Files (ZIP)

Expected files in data-dir:
    - Occupation Data.txt
    - Skills.txt
    - Knowledge.txt
    - Abilities.txt
    - Interests.txt
    - Education, Training, and Experience.txt
    - Technology Skills.txt
    - Work Activities.txt
    - Job Zones.txt
    - Occupation Level Metadata.txt

Attribution:
    This product uses O*NET data under license from the U.S. Department of Labor,
    Employment and Training Administration (USDOL/ETA).
    O*NET® is a trademark of USDOL/ETA.
"""

import os
import sys
import argparse
import csv
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_supabase_client(env_path: str = ".env") -> Client:
    """Initialize Supabase client from environment."""
    load_dotenv(env_path)
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env\n"
            "Or use --database-url for direct PostgreSQL connection."
        )
    
    return create_client(supabase_url, supabase_key)


def read_onet_file(filepath: Path, delimiter: str = "\t") -> list[dict]:
    """Read an O*NET tab-delimited file and return list of dicts."""
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return []
    
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append({k.strip(): v.strip() for k, v in row.items()})
    
    logger.info(f"Read {len(rows)} rows from {filepath.name}")
    return rows


def load_occupations(client: Client, data_dir: Path, batch_size: int = 100) -> int:
    """Load occupation data from 'Occupation Data.txt'."""
    rows = read_onet_file(data_dir / "Occupation Data.txt")
    if not rows:
        return 0
    
    inserted = 0
    batch = []
    
    for row in rows:
        onet_code = row.get("O*NET-SOC Code", "")
        if not onet_code:
            continue
        
        batch.append({
            "onet_code": onet_code,
            "title": row.get("Title", ""),
            "description": row.get("Description", ""),
        })
        
        if len(batch) >= batch_size:
            try:
                client.table("onet_occupations").upsert(batch, on_conflict="onet_code").execute()
                inserted += len(batch)
                logger.info(f"Inserted {inserted} occupations...")
            except Exception as e:
                logger.error(f"Error inserting batch: {e}")
            batch = []
    
    if batch:
        client.table("onet_occupations").upsert(batch, on_conflict="onet_code").execute()
        inserted += len(batch)
    
    logger.info(f"✓ Loaded {inserted} occupations")
    return inserted


def load_job_zones(client: Client, data_dir: Path) -> int:
    """Update occupations with job zone data from 'Job Zones.txt'."""
    rows = read_onet_file(data_dir / "Job Zones.txt")
    if not rows:
        return 0
    
    updated = 0
    for row in rows:
        onet_code = row.get("O*NET-SOC Code", "")
        job_zone = row.get("Job Zone", "")
        if not onet_code or not job_zone:
            continue
        
        try:
            client.table("onet_occupations").update({
                "job_zone": int(job_zone)
            }).eq("onet_code", onet_code).execute()
            updated += 1
        except Exception as e:
            logger.debug(f"Could not update job zone for {onet_code}: {e}")
    
    logger.info(f"✓ Updated {updated} job zones")
    return updated


def load_skills(client: Client, data_dir: Path, batch_size: int = 500) -> int:
    """Load skills data from 'Skills.txt'."""
    rows = read_onet_file(data_dir / "Skills.txt")
    if not rows:
        return 0
    
    # Get valid onet codes
    result = client.table("onet_occupations").select("onet_code").execute()
    valid_codes = {r["onet_code"] for r in result.data}
    
    inserted = 0
    batch = []
    
    for row in rows:
        onet_code = row.get("O*NET-SOC Code", "")
        if onet_code not in valid_codes:
            continue
        
        scale = row.get("Scale ID", "")
        # Only import LV (level) and IM (importance) scales
        if scale not in ("LV", "IM"):
            continue
        
        try:
            importance = float(row.get("Data Value", 0)) * (100/7) if scale == "IM" else None
            level = float(row.get("Data Value", 0)) if scale == "LV" else None
        except ValueError:
            continue
        
        # Find existing entry or create new
        element_name = row.get("Element Name", "")
        element_id = row.get("Element ID", "")
        
        batch.append({
            "onet_code": onet_code,
            "skill_name": element_name,
            "skill_id": element_id,
            "importance": importance,
            "level": level,
            "skill_category": "technical",
        })
        
        if len(batch) >= batch_size:
            try:
                client.table("onet_skills").insert(batch).execute()
                inserted += len(batch)
                logger.info(f"Inserted {inserted} skill records...")
            except Exception as e:
                logger.error(f"Skill batch insert error: {e}")
            batch = []
    
    if batch:
        try:
            client.table("onet_skills").insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            logger.error(f"Final skill batch error: {e}")
    
    logger.info(f"✓ Loaded {inserted} skill records")
    return inserted


def load_technology_skills(client: Client, data_dir: Path, batch_size: int = 500) -> int:
    """Load technology skills from 'Technology Skills.txt'."""
    rows = read_onet_file(data_dir / "Technology Skills.txt")
    if not rows:
        return 0
    
    result = client.table("onet_occupations").select("onet_code").execute()
    valid_codes = {r["onet_code"] for r in result.data}
    
    inserted = 0
    batch = []
    
    for row in rows:
        onet_code = row.get("O*NET-SOC Code", "")
        if onet_code not in valid_codes:
            continue
        
        commodity_title = row.get("Commodity Title", "")
        example = row.get("Example", "")
        hot_tech = row.get("Hot Technology", "").lower() == "y"
        in_demand = row.get("In Demand", "").lower() == "y"
        
        name = example if example else commodity_title
        if not name:
            continue
        
        batch.append({
            "onet_code": onet_code,
            "technology_name": name,
            "technology_category": commodity_title,
            "is_hot_technology": hot_tech,
            "is_in_demand": in_demand,
        })
        
        if len(batch) >= batch_size:
            try:
                client.table("onet_technology").insert(batch).execute()
                inserted += len(batch)
                logger.info(f"Inserted {inserted} technology records...")
            except Exception as e:
                logger.error(f"Technology batch error: {e}")
            batch = []
    
    if batch:
        try:
            client.table("onet_technology").insert(batch).execute()
            inserted += len(batch)
        except Exception:
            pass
    
    logger.info(f"✓ Loaded {inserted} technology skill records")
    return inserted


def load_work_activities(client: Client, data_dir: Path, batch_size: int = 500) -> int:
    """Load work activities from 'Work Activities.txt'."""
    rows = read_onet_file(data_dir / "Work Activities.txt")
    if not rows:
        return 0
    
    result = client.table("onet_occupations").select("onet_code").execute()
    valid_codes = {r["onet_code"] for r in result.data}
    
    inserted = 0
    batch = []
    
    for row in rows:
        onet_code = row.get("O*NET-SOC Code", "")
        if onet_code not in valid_codes:
            continue
        
        scale = row.get("Scale ID", "")
        if scale not in ("IM",):
            continue
        
        try:
            importance = float(row.get("Data Value", 0)) * (100/7)
        except ValueError:
            continue
        
        batch.append({
            "onet_code": onet_code,
            "activity_name": row.get("Element Name", ""),
            "activity_id": row.get("Element ID", ""),
            "importance": importance,
        })
        
        if len(batch) >= batch_size:
            try:
                client.table("onet_work_activities").insert(batch).execute()
                inserted += len(batch)
            except Exception:
                pass
            batch = []
    
    if batch:
        try:
            client.table("onet_work_activities").insert(batch).execute()
            inserted += len(batch)
        except Exception:
            pass
    
    logger.info(f"✓ Loaded {inserted} work activity records")
    return inserted


def load_interests(client: Client, data_dir: Path, batch_size: int = 500) -> int:
    """Load Holland Code interests from 'Interests.txt'."""
    rows = read_onet_file(data_dir / "Interests.txt")
    if not rows:
        return 0
    
    result = client.table("onet_occupations").select("onet_code").execute()
    valid_codes = {r["onet_code"] for r in result.data}
    
    inserted = 0
    batch = []
    
    for row in rows:
        onet_code = row.get("O*NET-SOC Code", "")
        if onet_code not in valid_codes:
            continue
        
        scale = row.get("Scale ID", "OI")  # Occupational Interest
        if scale != "OI":
            continue
        
        try:
            score = float(row.get("Data Value", 0)) * (100/7)
        except ValueError:
            continue
        
        batch.append({
            "onet_code": onet_code,
            "interest_area": row.get("Element Name", ""),
            "score": score,
        })
        
        if len(batch) >= batch_size:
            try:
                client.table("onet_interests").insert(batch).execute()
                inserted += len(batch)
            except Exception:
                pass
            batch = []
    
    if batch:
        try:
            client.table("onet_interests").insert(batch).execute()
            inserted += len(batch)
        except Exception:
            pass
    
    logger.info(f"✓ Loaded {inserted} interest records")
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Load O*NET data into PathPilot AI database")
    parser.add_argument("--data-dir", required=True, help="Directory containing O*NET CSV files")
    parser.add_argument("--env", default=".env", help="Path to .env file")
    parser.add_argument("--tables", nargs="+", 
                       choices=["occupations", "job_zones", "skills", "technology", "activities", "interests", "all"],
                       default=["all"],
                       help="Which tables to load (default: all)")
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    logger.info("🚀 Starting O*NET data ingestion...")
    logger.info(f"Data directory: {data_dir.absolute()}")
    
    try:
        client = get_supabase_client(args.env)
        logger.info("✓ Connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        sys.exit(1)
    
    load_all = "all" in args.tables
    total = 0
    
    if load_all or "occupations" in args.tables:
        total += load_occupations(client, data_dir)
    
    if load_all or "job_zones" in args.tables:
        total += load_job_zones(client, data_dir)
    
    if load_all or "skills" in args.tables:
        total += load_skills(client, data_dir)
    
    if load_all or "technology" in args.tables:
        total += load_technology_skills(client, data_dir)
    
    if load_all or "activities" in args.tables:
        total += load_work_activities(client, data_dir)
    
    if load_all or "interests" in args.tables:
        total += load_interests(client, data_dir)
    
    logger.info(f"\n✅ O*NET data ingestion complete! Total records loaded: {total}")
    logger.info("\nAttribution: This product uses O*NET data under license from the U.S. Department of Labor.")
    logger.info("O*NET® is a trademark of USDOL/ETA. Source: https://www.onetcenter.org")


if __name__ == "__main__":
    main()
