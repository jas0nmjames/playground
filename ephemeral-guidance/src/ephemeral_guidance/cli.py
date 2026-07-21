from __future__ import annotations

from pathlib import Path

import typer

from .analytics import build_rollups
from .features import build_features
from .insights import build_insight_candidates, export_insights_json
from .paths import default_paths
from .warehouse import build_warehouse, connect

app = typer.Typer(add_completion=False)


@app.command("build-warehouse")
def cmd_build_warehouse(
    db: Path | None = typer.Option(None, help="Path to DuckDB file."),
    assets_dir: Path | None = typer.Option(None, help="Directory containing JSON assets."),
) -> None:
    paths = default_paths()
    db_path = db or paths.duckdb_path
    assets = assets_dir or paths.assets_dir
    con = connect(db_path)
    try:
        build_warehouse(con=con, assets_dir=assets)
    finally:
        con.close()


@app.command("build-rollups")
def cmd_build_rollups(db: Path | None = typer.Option(None, help="Path to DuckDB file.")) -> None:
    paths = default_paths()
    db_path = db or paths.duckdb_path
    con = connect(db_path)
    try:
        build_rollups(con=con)
    finally:
        con.close()


@app.command("build-features")
def cmd_build_features(db: Path | None = typer.Option(None, help="Path to DuckDB file.")) -> None:
    paths = default_paths()
    db_path = db or paths.duckdb_path
    con = connect(db_path)
    try:
        build_features(con=con)
    finally:
        con.close()


@app.command("build-insights")
def cmd_build_insights(
    db: Path | None = typer.Option(None, help="Path to DuckDB file."),
    out: Path | None = typer.Option(None, help="Path to insights.json output."),
    limit: int = typer.Option(60, help="Max number of insight cards to export."),
) -> None:
    paths = default_paths()
    db_path = db or paths.duckdb_path
    out_path = out or paths.insights_json_path
    con = connect(db_path)
    try:
        build_insight_candidates(con=con)
        export_insights_json(con=con, out_path=out_path, limit=limit)
    finally:
        con.close()


@app.command("build-all")
def cmd_build_all(
    db: Path | None = typer.Option(None, help="Path to DuckDB file."),
    assets_dir: Path | None = typer.Option(None, help="Directory containing JSON assets."),
    out: Path | None = typer.Option(None, help="Path to insights.json output."),
    limit: int = typer.Option(60, help="Max number of insight cards to export."),
) -> None:
    paths = default_paths()
    db_path = db or paths.duckdb_path
    assets = assets_dir or paths.assets_dir
    out_path = out or paths.insights_json_path
    con = connect(db_path)
    try:
        build_warehouse(con=con, assets_dir=assets)
        build_rollups(con=con)
        build_features(con=con)
        build_insight_candidates(con=con)
        export_insights_json(con=con, out_path=out_path, limit=limit)
    finally:
        con.close()


@app.command("top-insights")
def cmd_top_insights(
    db: Path | None = typer.Option(None, help="Path to DuckDB file."),
    n: int = typer.Option(10, help="Number of cards to print."),
) -> None:
    from .contracts import Tables

    paths = default_paths()
    db_path = db or paths.duckdb_path
    con = connect(db_path)
    try:
        rows = con.execute(
            f"""
            SELECT insight_id, kind, score, severity, title, one_liner
            FROM {Tables.insights_candidates}
            ORDER BY score DESC, severity DESC
            LIMIT ?
            """,
            [n],
        ).fetchall()
        for r in rows:
            typer.echo(f"{r[0]}  [{r[1]}] score={r[2]:.2f} sev={r[3]:.2f} — {r[4]}\n  {r[5]}\n")
    finally:
        con.close()


@app.command("show-evidence")
def cmd_show_evidence(
    insight_id: str = typer.Argument(..., help="Insight id to display evidence for."),
    db: Path | None = typer.Option(None, help="Path to DuckDB file."),
) -> None:
    from .contracts import Tables

    paths = default_paths()
    db_path = db or paths.duckdb_path
    con = connect(db_path)
    try:
        row = con.execute(
            f"""
            SELECT evidence::VARCHAR
            FROM {Tables.insights_candidates}
            WHERE insight_id = ?
            """,
            [insight_id],
        ).fetchone()
        if not row:
            raise typer.Exit(code=1)
        typer.echo(row[0])
    finally:
        con.close()

