"""Unify restaurant health inspections from structurally-different sources.

A proof-of-concept ETL package for USA TODAY. Three sources (a REST API, a pair
of CSV flat files, and a weekly PDF) are normalized into one schema. See the
top-level README.md and documentation/ for the full story.
"""

__version__ = "0.1.0"

# The unified-schema version records emit. Bump in lockstep with
# schema/inspection_schema.yaml -> schema.version.
SCHEMA_VERSION = "0.1.0"
