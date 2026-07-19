"""Pipeline orchestration + CLI.

    inspections extract   [--source KEY]
    inspections transform [--source KEY]
    inspections load
    inspections run       [--source KEY]     # extract -> transform -> load

Design notes:
  * Each stage records per-source state (data/state/) and routes data-quality problems to
    a loud ErrorSink (data/errors/). Bad records are quarantined, not silently dropped.
  * A non-zero exit code signals that errors occurred, so a CI step "fails" and downstream
    stages (wired via workflow_run: on success) don't build on bad data.
  * Transform is skipped for a source whose extract detected upstream drift — we never
    normalize data we already know is off-shape.
"""

from __future__ import annotations

import argparse
import json

from . import __version__, paths
from .config import PipelineConfig, SourceConfig, load_config
from .errors import ErrorSink
from .extractors import get_extractor
from .loaders import combine
from .logkit import event
from .state import read_state, record_stage
from .transformers import get_transformer
from .validation import validate_records


def _selected(cfg: PipelineConfig, source: str | None) -> list[SourceConfig]:
    return [cfg.get(source)] if source else cfg.enabled_sources()


def stage_extract(cfg: PipelineConfig, sources: list[SourceConfig]) -> bool:
    had_error = False
    for s in sources:
        event("extract.start", source=s.key, method=s.extraction_method.value)
        try:
            result = get_extractor(s, cfg).extract()
        except Exception as exc:  # noqa: BLE001 — surface any extractor failure as state+error
            record_stage(s.key, "extract", "failed", {"error": repr(exc)})
            event("extract.error", level="error", source=s.key, error=repr(exc))
            had_error = True
            continue

        sink = ErrorSink("extract", s.key)
        for missing in result.missing_expected:
            sink.record(s.key, "expected field missing (upstream drift)", missing)
        report = sink.flush()

        status = "success" if result.ok else "failed"
        record_stage(s.key, "extract", status, {
            "records": result.record_count,
            "fingerprint": result.fingerprint,
            "missing_expected": result.missing_expected,
            "error_report": str(report) if report else None,
            **result.notes,
        })
        event("extract.done", source=s.key, records=result.record_count, status=status)
        had_error = had_error or not result.ok
    return had_error


def stage_transform(cfg: PipelineConfig, sources: list[SourceConfig]) -> bool:
    had_error = False
    paths.ensure_data_dirs()
    for s in sources:
        extract_state = read_state(s.key).get("stages", {}).get("extract", {})
        if extract_state.get("status") == "failed":
            event("transform.skip", level="warn", source=s.key, reason="extract failed/drift")
            had_error = True
            continue

        event("transform.start", source=s.key)
        try:
            raw_records = get_transformer(s, cfg).transform()
        except Exception as exc:  # noqa: BLE001
            record_stage(s.key, "transform", "failed", {"error": repr(exc)})
            event("transform.error", level="error", source=s.key, error=repr(exc))
            had_error = True
            continue

        valid, errors = validate_records(raw_records)
        sink = ErrorSink("transform", s.key)
        for idx, msg in errors:
            sink.record(f"row#{idx}", "post-transform validation failed", msg)
        report = sink.flush()

        out = [m.model_dump(mode="json") for m in valid]
        (paths.STAGING_DIR / f"{s.key}.json").write_text(json.dumps(out, indent=2) + "\n")

        status = "success" if not errors else "partial"
        record_stage(s.key, "transform", status, {
            "records_in": len(raw_records),
            "records_out": len(out),
            "validation_errors": len(errors),
            "error_report": str(report) if report else None,
        })
        event("transform.done", source=s.key, records_in=len(raw_records),
              records_out=len(out), validation_errors=len(errors), status=status)
        had_error = had_error or bool(errors)
    return had_error


def stage_load(cfg: PipelineConfig) -> bool:
    event("load.start")
    result = combine(cfg)
    for s in cfg.enabled_sources():
        record_stage(s.key, "load", "success" if result.written else "failed",
                     {"contributed": result.per_source.get(s.key, 0)})
    event("load.done", level="info" if result.written else "error",
          total=result.total, written=result.written, schema_errors=result.schema_errors,
          result_breakdown=result.result_breakdown)
    if not result.written:
        event("load.refused", level="error",
              reason="pre-load JSON Schema violations; production left unchanged",
              schema_errors=result.schema_errors, report=result.error_report)
    return not result.written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inspections", description=__doc__)
    parser.add_argument("--version", action="version", version=f"inspections {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("extract", "transform", "run"):
        sp = sub.add_parser(name, help=f"{name} stage")
        sp.add_argument("--source", help="limit to one source key (default: all enabled)")
    sub.add_parser("load", help="combine staging -> production")

    args = parser.parse_args(argv)
    paths.ensure_data_dirs()
    cfg = load_config()

    if args.command == "extract":
        had_error = stage_extract(cfg, _selected(cfg, args.source))
    elif args.command == "transform":
        had_error = stage_transform(cfg, _selected(cfg, args.source))
    elif args.command == "load":
        had_error = stage_load(cfg)
    else:  # run
        sources = _selected(cfg, args.source)
        e = stage_extract(cfg, sources)
        t = stage_transform(cfg, sources)
        load_err = stage_load(cfg)
        had_error = e or t or load_err

    if had_error:
        event("pipeline.done", level="error", command=args.command,
              note="completed WITH errors — see data/errors/ and data/state/")
        return 1
    event("pipeline.done", command=args.command, note="completed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
