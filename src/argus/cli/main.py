"""ARGUS CLI — Orchestration commands."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from argus import __version__
from argus.core import get_logger, setup_logging
from argus.core.config import load_config
from argus.data import ArtifactCache, RasterImageLoader, create_thumbnail
from argus.vision import SAMRoadExtractor, VisionConfig

app = typer.Typer(
    name="argus",
    help="ARGUS — Satellite Road Graph Extraction for Urban Mobility Resilience",
    add_completion=False,
)
console = Console()
log = get_logger(__name__)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    log_file: str | None = typer.Option(None, "--log-file", help="Log file path"),
):
    """ARGUS — Decision Support for Urban Mobility."""
    setup_logging(
        level="DEBUG" if verbose else "INFO",
        log_file=Path(log_file) if log_file else None,
    )
    log.info(f"ARGUS v{__version__} starting")


@app.command()
def info():
    """Print project information."""
    table = Table(title="ARGUS Project Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Version", __version__)
    table.add_row("Description", "Satellite Road Graph Extraction for Urban Mobility Resilience")
    table.add_row(
        "Architecture",
        "7-Layer Pipeline: Data → Vision → Graph → Analytics → Simulation → Routing → Dashboard",
    )
    console.print(table)


@app.command()
def ingest(
    source: str = typer.Argument(..., help="Path to satellite image (GeoTIFF, PNG, JPEG)"),
    output: str = typer.Option(None, "--output", "-o", help="Output path for preview thumbnail"),
    cache: bool = typer.Option(True, "--cache/--no-cache", help="Cache the loaded image"),
):
    """Load and inspect satellite imagery."""
    console.print(f"[bold green]Loading image:[/bold green] {source}")

    try:
        # Load config for target CRS
        config = load_config("data")
        target_crs = config.target_crs if hasattr(config, "target_crs") else "EPSG:4326"

        # Load image
        loader = RasterImageLoader(target_crs=target_crs)
        img = loader.load_and_reproject(source)

        # Print metadata table
        table = Table(title=f"RasterImage: {Path(source).name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Shape", f"{img.height} x {img.width} x {img.channels}")
        table.add_row("CRS", img.crs)
        table.add_row("Bounds", f"{img.bounds}")
        table.add_row("Transform", str(img.transform))
        table.add_row("Data type", str(img.data.dtype))
        table.add_row("Data range", f"{img.data.min():.3f} - {img.data.max():.3f}")
        console.print(table)

        # Cache if requested
        if cache:
            cache_obj = ArtifactCache()
            cache_obj.save(f"raster_{Path(source).stem}", img, format="npz")
            console.print(f"[dim]Cached to {cache_obj.cache_dir}[/dim]")

        # Generate and save thumbnail
        if output:
            thumb = create_thumbnail(img, max_size=256)
            from PIL import Image

            thumb_img = Image.fromarray((thumb * 255).astype(np.uint8))
            thumb_img.save(output)
            console.print(f"[bold green]Thumbnail saved:[/bold green] {output}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def extract(
    source: str = typer.Argument(..., help="Path to satellite image"),
    output: str = typer.Option("mask.png", "--output", "-o", help="Output mask path"),
    model: str = typer.Option(
        "sam_road", "--model", "-m", help="Model to use (sam_road, dlinknet)"
    ),
    device: str = typer.Option("auto", "--device", "-d", help="Device (auto, cpu, cuda)"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Threshold for binarization"),
    tile_size: int = typer.Option(512, "--tile-size", help="Tile size for large images"),
    overlap: int = typer.Option(64, "--overlap", help="Overlap between tiles"),
    postprocess: bool = typer.Option(
        True, "--postprocess/--no-postprocess", help="Apply post-processing"
    ),
):
    """Extract road segmentation mask from satellite image."""
    console.print(f"[bold green]Extracting roads from:[/bold green] {source}")
    console.print(f"[bold blue]Model:[/bold blue] {model}, [bold blue]Device:[/bold blue] {device}")

    try:
        # Load image
        config = load_config("data")
        target_crs = config.target_crs if hasattr(config, "target_crs") else "EPSG:4326"
        loader = RasterImageLoader(target_crs=target_crs)
        img = loader.load_and_reproject(source)

        # Configure vision
        vision_config = VisionConfig(
            model_type=model,
            device=device,
            threshold=threshold,
            tile_size=tile_size,
            overlap=overlap,
        )

        # Create extractor
        if model == "sam_road":
            extractor = SAMRoadExtractor(vision_config)
        elif model == "dlinknet":
            from argus.vision import DLinkNetExtractor

            extractor = DLinkNetExtractor(vision_config)
        else:
            raise ValueError(f"Unknown model: {model}")

        # Extract mask
        console.print("[bold green]Running inference...[/bold green]")
        road_mask = extractor.extract(img)

        # Save mask as PNG
        from PIL import Image

        mask_img = Image.fromarray((road_mask.mask * 255).astype(np.uint8))
        mask_img.save(output)
        console.print(f"[bold green]Mask saved:[/bold green] {output}")

        # Print metadata
        table = Table(title=f"RoadMask: {Path(source).name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Shape", f"{road_mask.mask.shape[0]} x {road_mask.mask.shape[1]}")
        table.add_row("CRS", road_mask.crs)
        table.add_row("Bounds", str(road_mask.bounds))
        table.add_row("Road pixels", f"{road_mask.mask.sum():,}")
        table.add_row("Road ratio", f"{road_mask.mask.mean():.4f}")
        table.add_row("Model", road_mask.model_name)
        table.add_row("Threshold", str(vision_config.threshold))
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def build_graph(
    source: str = typer.Argument(..., help="Path to road mask (PNG, NPY, NPZ)"),
    output: str = typer.Option("graph.graphml", "--output", "-o", help="Output graph path"),
    format: str = typer.Option(
        "graphml", "--format", "-f", help="Output format (graphml, geojson, pickle)"
    ),
    crs: str = typer.Option("EPSG:4326", "--crs", help="CRS of the mask (e.g. EPSG:4326)"),
):
    """Build road graph from segmentation mask."""
    console.print(f"[bold green]Building graph from:[/bold green] {source}")

    try:
        from argus.graph import (
            RoadGraphBuilderImpl,
            export_geojson,
            export_graphml,
            export_pickle,
        )
        from argus.graph.loader import load_mask_from_file

        cfg_dict = load_config("graph")
        from omegaconf import OmegaConf

        cfg_dict = OmegaConf.to_container(cfg_dict, resolve=True)  # type: ignore[union-attr, call-overload]
        builder = RoadGraphBuilderImpl(config=cfg_dict)

        mask = load_mask_from_file(source, crs=crs)
        console.print(
            f"[dim]Loaded mask: {mask.mask.shape} — {mask.mask.sum():,} road pixels[/dim]"
        )

        road_graph = builder.build(mask)

        output_path = Path(output)

        if format == "geojson":
            export_geojson(road_graph, output_path)
        elif format == "pickle":
            export_pickle(road_graph, output_path)
        else:
            export_graphml(road_graph, output_path)

        table = Table(title="RoadGraph Summary")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Nodes", str(road_graph.node_count))
        table.add_row("Edges", str(road_graph.edge_count))
        table.add_row("CRS", road_graph.crs)
        table.add_row("Bounds", str(tuple(round(b, 6) for b in road_graph.bounds)))
        table.add_row("Output", str(output_path))
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def preview(
    source: str = typer.Argument(
        ..., help="Path to road graph (pickle file) or mask (PNG) to build + preview"
    ),
    output: str = typer.Option("preview.html", "--output", "-o", help="Output HTML path"),
):
    """Render an interactive map preview of a road graph."""
    console.print(f"[bold green]Previewing:[/bold green] {source}")

    try:
        import folium  # pyright: ignore[reportMissingImports]

        from argus.graph.export import load_pickle
        from argus.graph.loader import load_mask_from_file

        source_path = Path(source)

        if source_path.suffix == ".pkl" or source_path.suffix == ".pickle":
            road_graph = load_pickle(source_path)
        else:
            # Load mask and build graph on-the-fly
            from argus.graph.builder import RoadGraphBuilderImpl

            cfg_dict = load_config("graph")
            from omegaconf import OmegaConf

            cfg_dict = OmegaConf.to_container(cfg_dict, resolve=True)  # type: ignore[union-attr, call-overload]
            builder = RoadGraphBuilderImpl(config=cfg_dict)
            mask = load_mask_from_file(source)
            road_graph = builder.build(mask)

        # Compute map center from bounds
        bounds = road_graph.bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # Add nodes
        for _, data in road_graph.graph.nodes(data=True):
            lat = data.get("lat", 0)
            lon = data.get("lon", 0)
            deg = data.get("degree", 0)
            color = "red" if deg <= 1 else "orange" if deg == 2 else "green"
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=f"degree={deg}",
            ).add_to(m)

        # Add edges
        for u, v, _key, data in road_graph.graph.edges(data=True, keys=True):
            path_pixels = data.get("path_pixels", [])
            if path_pixels and len(path_pixels) >= 2:
                from argus.graph.export import _get_affine

                a, b, c, d, e, f = _get_affine(road_graph)
                coords = [(d * px + e * py + f, a * px + b * py + c) for px, py in path_pixels]
            else:
                u_lat = road_graph.graph.nodes[u].get("lat", 0)
                u_lon = road_graph.graph.nodes[u].get("lon", 0)
                v_lat = road_graph.graph.nodes[v].get("lat", 0)
                v_lon = road_graph.graph.nodes[v].get("lon", 0)
                coords = [(u_lat, u_lon), (v_lat, v_lon)]

            folium.PolyLine(
                locations=coords,
                color="blue",
                weight=2,
                opacity=0.6,
            ).add_to(m)

        m.save(output)
        console.print(f"[bold green]Preview saved:[/bold green] {output}")
        console.print(f"[dim]Open {output} in your browser to view.[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def analyze(
    graph: str = typer.Argument(..., help="Path to road graph (pickle file)"),
    output: str = typer.Option(
        "outputs/analytics", "--output", "-o", help="Output directory for reports"
    ),
    metrics: str = typer.Option(
        "all",
        "--metrics",
        help="Metrics to compute (comma-separated: betweenness,closeness,degree,articulation,bridges or 'all')",
    ),
    format: str = typer.Option("both", "--format", "-f", help="Output format (json, csv, both)"),
    top_n: int = typer.Option(
        10, "--top-n", "-n", help="Number of top critical elements to report"
    ),
):
    """Compute criticality metrics on road graph."""
    console.print(f"[bold green]Analyzing graph:[/bold green] {graph}")

    try:
        from argus.analytics.analyzer import (
            AnalyticsConfig,
            CriticalityAnalyzerImpl,
        )
        from argus.analytics.report import generate_report
        from argus.graph.export import load_pickle

        source_path = Path(graph)
        road_graph = load_pickle(source_path)

        metrics_list = _parse_metrics_list(metrics)

        cfg = AnalyticsConfig(
            metrics=metrics_list,
            top_n=top_n,
        )
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(road_graph)

        output_dir = Path(output)
        _generated = generate_report(result, output_dir, format=format)

        # Print summary table
        table = Table(title="Criticality Analysis")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Nodes", str(result.summary["graph_stats"]["nodes"]))
        table.add_row("Edges", str(result.summary["graph_stats"]["edges"]))
        table.add_row("Components", str(result.summary["graph_stats"]["connected_components"]))
        table.add_row("Metrics", ", ".join(result.summary["metrics_computed"]))
        table.add_row("Art. Points", str(result.summary["resilience"]["articulation_points_count"]))
        table.add_row("Bridges", str(result.summary["resilience"]["bridges_count"]))

        resilience = result.summary.get("resilience", {})
        if resilience.get("avg_path_length") is not None:
            table.add_row("Avg Path Len", f"{resilience['avg_path_length']:.2f}")
        if resilience.get("diameter") is not None:
            table.add_row("Diameter", str(resilience["diameter"]))
        if resilience.get("vulnerability_ratio") is not None:
            table.add_row("Vulnerability", f"{resilience['vulnerability_ratio']:.4f}")

        table.add_row("Output", str(output_dir))
        console.print(table)

        # Show top-3 critical nodes
        if "top_nodes_betweenness" in result.report:
            top = result.report["top_nodes_betweenness"][:3]
            console.print("\n[bold]Top-3 Critical Nodes (Betweenness):[/bold]")
            for nid, score in top:
                console.print(f"  Node {nid}: {score:.4f}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


def _parse_metrics_list(raw: str) -> list[str]:
    """Parse comma-separated or shorthand metric list."""
    from argus.analytics.analyzer import CriticalityAnalyzerImpl

    if raw.lower() == "all":
        return sorted(CriticalityAnalyzerImpl.ALL_METRICS)
    entries = [m.strip().lower() for m in raw.split(",") if m.strip()]
    valid = set(CriticalityAnalyzerImpl.ALL_METRICS)
    return [m for m in entries if m in valid]


def _parse_latlon(raw: str) -> tuple[float, float]:
    """Parse 'lat,lon' string into (lat, lon) float tuple."""
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        raise ValueError(f"Expected 'lat,lon' format, got '{raw}'")
    return float(parts[0]), float(parts[1])


@app.command()
def simulate(
    graph: str = typer.Argument(..., help="Path to road graph"),
    scenario: str = typer.Argument(..., help="Path to scenario YAML"),
    output_dir: str = typer.Option(
        "outputs/simulation", "--output-dir", "-o", help="Output directory"
    ),
):
    """Run disaster simulation scenario on road graph."""
    console.print(f"[bold green]Simulating scenario:[/bold green] {scenario} on {graph}")

    try:
        from argus.graph.export import export_pickle, load_pickle
        from argus.simulation import DisasterSimulatorImpl, load_scenario

        graph_path = Path(graph)
        road_graph = load_pickle(graph_path)
        console.print(f"[dim]Graph: {road_graph.node_count}N, {road_graph.edge_count}E[/dim]")

        scen = load_scenario(scenario)
        console.print(f"[dim]Scenario: {scen.scenario_id} ({scen.scenario_type})[/dim]")

        simulator = DisasterSimulatorImpl()
        result = simulator.simulate(road_graph, scen)

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Save modified graph
        modified_path = out / "modified_graph.pkl"
        export_pickle(result.modified_graph, modified_path)

        # Save impact report
        import json

        from argus.analytics.report import serialise_value

        report_path = out / "impact_report.json"
        report_data = {
            "scenario_metadata": result.scenario_metadata,
            "impact_report": result.impact_report,
        }
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2, default=serialise_value)

        # Summary table
        impact = result.impact_report
        table = Table(title="Simulation Results")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Scenario", scen.scenario_id)
        table.add_row("Type", scen.scenario_type)
        table.add_row(
            "Nodes (before→after)", f"{impact['original_nodes']} → {impact['modified_nodes']}"
        )
        table.add_row(
            "Edges (before→after)", f"{impact['original_edges']} → {impact['modified_edges']}"
        )
        table.add_row(
            "Components (before→after)",
            f"{impact['original_components']} → {impact['modified_components']}",
        )
        table.add_row("Removed Nodes", str(len(impact["removed_nodes"])))
        table.add_row("Removed Edges", str(len(impact["removed_edges"])))
        table.add_row("Reweighted Edges", str(len(impact["reweighted_edges"])))
        table.add_row("Isolated Components", str(impact["new_isolated_components"]))
        table.add_row("Output", str(out))
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def route(
    graph: str = typer.Argument(..., help="Path to road graph"),
    origin: str = typer.Option(..., "--origin", help="Origin as 'lat,lon'"),
    destination: str = typer.Option(..., "--destination", "-d", help="Destination as 'lat,lon'"),
    algorithm: str = typer.Option(
        "dijkstra", "--algorithm", "-a", help="Algorithm (dijkstra, astar, k_shortest)"
    ),
    k: int = typer.Option(1, "--k", help="Number of alternative routes (k_shortest only)"),
    output: str = typer.Option("route.geojson", "--output", "-o", help="Output route path"),
    compare_graph: str = typer.Option(
        None, "--compare-graph", "-c", help="Modified graph pickle for before/after comparison"
    ),
):
    """Compute route on road graph, with optional before/after comparison."""
    console.print(f"[bold green]Routing on:[/bold green] {graph}")
    console.print(
        f"[bold blue]Origin:[/bold blue] {origin}, [bold blue]Destination:[/bold blue] {destination}"
    )

    try:
        from argus.graph.export import load_pickle
        from argus.routing.router import (
            RouteQuery,
            RouterImpl,
            export_route_geojson,
        )

        orig_lat, orig_lon = _parse_latlon(origin)
        dest_lat, dest_lon = _parse_latlon(destination)

        graph_path = Path(graph)
        road_graph = load_pickle(graph_path)
        console.print(f"[dim]Graph: {road_graph.node_count}N, {road_graph.edge_count}E[/dim]")

        router = RouterImpl()
        query = RouteQuery(
            origin=(orig_lat, orig_lon),
            destination=(dest_lat, dest_lon),
            algorithm=algorithm,
            k=k,
        )
        result = router.find_route(road_graph, query)

        routes = result.routes
        out_path = Path(output)
        export_route_geojson(routes, out_path)

        table = Table(title="Route Results")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        if routes:
            primary = routes[0]
            table.add_row("Routes Found", str(len(routes)))
            table.add_row("Length", f"{primary['properties']['length_m']:.0f} m")
            table.add_row(
                "Travel Time",
                f"{primary['properties']['travel_time_s']:.0f} s "
                f"({primary['properties']['speed_kmh']:.0f} km/h)",
            )
            table.add_row("Nodes", str(len(primary["properties"]["nodes"])))
        else:
            table.add_row("Status", "[red]No route found[/red]")
        table.add_row("Output", str(out_path))

        # Before/after comparison
        if compare_graph:
            mod_graph = load_pickle(Path(compare_graph))
            mod_result = router.find_route(mod_graph, query)
            comparison = router.compare_routes(routes, mod_result.routes)
            table.add_row(
                "Baseline Length",
                f"{comparison['baseline_length_m']:.0f} m"
                if comparison["baseline_length_m"]
                else "N/A",
            )
            table.add_row(
                "Modified Length",
                f"{comparison['modified_length_m']:.0f} m"
                if comparison["modified_length_m"]
                else "N/A",
            )
            table.add_row(
                "Status",
                comparison.get("status", "unknown"),
            )

            # Also save the modified route
            if mod_result.routes:
                mod_path = out_path.with_name(out_path.stem + "_modified.geojson")
                export_route_geojson(mod_result.routes, mod_path)
                table.add_row("Modified Route", str(mod_path))

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@app.command()
def dashboard(
    graph: str = typer.Option(None, "--graph", "-g", help="Path to pre-loaded graph (pickle)"),
    port: int = typer.Option(8501, "--port", "-p", help="Streamlit port"),
):
    """Launch interactive dashboard."""
    console.print("[bold green]Starting dashboard...[/bold green]")

    if graph:
        # Load graph and pass via streamlit bootstrap
        from argus.graph.export import load_pickle

        graph_path = Path(graph)
        rg = load_pickle(graph_path)
        # Store to a temp pickle the dashboard can load
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            from argus.graph.export import export_pickle

            export_pickle(rg, Path(tmp.name))
            st_graph_path = tmp.name

        console.print(f"[dim]Pre-loaded graph: {rg.node_count}N, {rg.edge_count}E[/dim]")
        console.print(f"[bold green]Dashboard:[/bold green] http://localhost:{port}")
        console.print(
            "[dim]Note: pre-loading via CLI argument is not persisted "
            "in the Streamlit session. Use the file uploader in the "
            "dashboard sidebar for persistent loading.[/dim]"
        )
        # Cleanup temp file (graph won't persist in streamlit session anyway)
        Path(st_graph_path).unlink(missing_ok=True)
    else:
        console.print(f"[bold green]Dashboard:[/bold green] http://localhost:{port}")

    # Actually launch streamlit
    import subprocess
    import sys

    # Determine the project root (3 levels up from cli/main.py: cli -> argus -> src -> root)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    app_path = Path(__file__).resolve().parent.parent / "dashboard" / "app.py"

    # Propagate current env and override Arrow memory pool to prevent mimalloc segfaults on macOS threads
    import os

    env = os.environ.copy()
    env["ARROW_DEFAULT_MEMORY_POOL"] = "system"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            str(port),
        ],
        cwd=str(project_root),
        env=env,
        check=False,
    )


@app.command()
def run(
    image: str = typer.Argument(..., help="Path to satellite image"),
    scenario: str = typer.Option(None, "--scenario", "-s", help="Disaster scenario YAML"),
    output_dir: str = typer.Option("results", "--output-dir", "-o", help="Output directory"),
):
    """Run full pipeline: ingest → extract → build → analyze → simulate (M1–M5)."""
    console.print("[bold green]Running pipeline stages M1→M2→M3→M4...[/bold green]")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    has_graph = False
    road_graph = None

    try:
        # M1: Ingest
        console.print("\n[bold]Stage 1: Data Ingest[/bold]")
        _cfg = load_config("data")
        target_crs = "EPSG:4326"

        loader = RasterImageLoader(target_crs=target_crs)
        img = loader.load_and_reproject(image)
        console.print(f"  Loaded: {img.height}x{img.width} ({img.channels} bands)")

        # M2: Extract
        console.print("\n[bold]Stage 2: Road Extraction[/bold]")
        from argus.vision import SAMRoadExtractor, VisionConfig

        vcfg = VisionConfig(model_type="sam_road", device="cpu", tile_size=256)
        extractor = SAMRoadExtractor(vcfg)
        mask = extractor.extract(img)
        console.print(f"  Mask: {mask.mask.sum():,} road pixels")

        # Save mask
        mask_png = out / "mask.png"
        from PIL import Image

        mask_img = Image.fromarray((mask.mask * 255).astype(np.uint8))
        mask_img.save(mask_png)

        # M3: Build graph
        console.print("\n[bold]Stage 3: Graph Construction[/bold]")
        from omegaconf import OmegaConf

        from argus.graph.builder import RoadGraphBuilderImpl

        graph_cfg_dict = OmegaConf.to_container(
            load_config("graph"),
            resolve=True,  # type: ignore[arg-type]
        )  # type: ignore[union-attr, call-overload]
        builder = RoadGraphBuilderImpl(config=graph_cfg_dict)
        road_graph = builder.build(mask)
        console.print(f"  Graph: {road_graph.node_count}N, {road_graph.edge_count}E")

        graph_pkl = out / "graph.pkl"
        from argus.graph.export import export_pickle

        export_pickle(road_graph, graph_pkl)
        has_graph = road_graph.node_count > 0

        # M4: Analyze
        console.print("\n[bold]Stage 4: Criticality Analysis[/bold]")
        table = Table(title="Pipeline Results")
        table.add_column("Stage", style="cyan")
        table.add_column("Output", style="green")
        table.add_row("M1 Ingest", str(img.height) + "x" + str(img.width))
        table.add_row("M2 Extract", f"{mask.mask.sum():,} road pixels → {mask_png}")
        table.add_row(
            "M3 Build",
            f"{road_graph.node_count} nodes, {road_graph.edge_count} edges → {graph_pkl}",
        )

        if not has_graph:
            console.print("[dim]Skipping analysis — graph has no nodes.[/dim]")
            table.add_row("M4 Analyze", "Skipped (empty graph)")
        else:
            from argus.analytics.analyzer import AnalyticsConfig, CriticalityAnalyzerImpl
            from argus.analytics.report import generate_report

            cfg = AnalyticsConfig()
            analyzer = CriticalityAnalyzerImpl(cfg)
            result = analyzer.analyze(road_graph)

            report_dir = out / "analytics"
            _ = generate_report(result, report_dir, format="both")
            table.add_row("M4 Analyze", f"Report → {report_dir}")

        # M5: Simulate
        if scenario and has_graph:
            console.print("\n[bold]Stage 5: Disaster Simulation[/bold]")
            from argus.simulation import DisasterSimulatorImpl, load_scenario

            scen = load_scenario(scenario)
            sim = DisasterSimulatorImpl()
            sim_result = sim.simulate(road_graph, scen)

            sim_dir = out / "simulation"
            sim_dir.mkdir(parents=True, exist_ok=True)
            export_pickle(sim_result.modified_graph, sim_dir / "modified_graph.pkl")

            import json

            from argus.analytics.report import serialise_value

            with open(sim_dir / "impact_report.json", "w") as f:
                json.dump(sim_result.impact_report, f, indent=2, default=serialise_value)

            impact = sim_result.impact_report
            table.add_row(
                "M5 Simulate",
                f"{scen.scenario_id}: {impact['original_nodes']}→{impact['modified_nodes']} N, "
                f"{impact['original_edges']}→{impact['modified_edges']} E → {sim_dir}",
            )
        elif scenario and not has_graph:
            table.add_row("M5 Simulate", "Skipped (empty graph)")
        elif not scenario:
            table.add_row("M5 Simulate", "Skipped (no --scenario flag)")

        console.print(table)
        console.print(f"\n[bold green]Pipeline complete. Results in {out}/[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error at stage:[/bold red] {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
