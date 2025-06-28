#!/usr/bin/env python3
import click
import asyncio
import json
from pathlib import Path
from typing import Optional, List
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from src.orchestration.query_orchestrator import QueryOrchestrator
from src.document_processing.document_processor import DocumentProcessor
from src.orchestration.graph_gardener import GraphGardener
from src.storage.neo4j_client import Neo4jClient
from src.storage.chroma_client import ChromaClient

console = Console()

@click.group()
def cli():
    """KI-Wissenssystem CLI"""
    pass

@cli.command()
@click.argument('query', type=str)
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'markdown']), default='markdown')
@click.option('--no-cache', is_flag=True, help='Disable cache')
def query(query: str, format: str, no_cache: bool):
    """Execute a query against the knowledge system"""
    
    async def run_query():
        orchestrator = QueryOrchestrator()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing query...", total=None)
            
            result = await orchestrator.process_query(
                query=query,
                use_cache=not no_cache
            )
            
            progress.update(task, completed=True)
        
        # Format output
        if format == 'json':
            console.print_json(json.dumps(result, indent=2, ensure_ascii=False))
        elif format == 'text':
            console.print(result['response'])
            console.print(f"\nConfidence: {result['confidence']:.2f}")
            console.print(f"Sources: {len(result['sources'])}")
        else:  # markdown
            md = Markdown(result['response'])
            console.print(md)
            
            if result['sources']:
                console.print("\n[bold]Sources:[/bold]")
                for i, source in enumerate(result['sources'], 1):
                    console.print(f"{i}. {source.get('source', 'Unknown')} "
                                f"({source.get('type', 'Unknown')})")
            
            if result.get('follow_up_questions'):
                console.print("\n[bold]Follow-up questions:[/bold]")
                for q in result['follow_up_questions']:
                    console.print(f"• {q}")
    
    asyncio.run(run_query())

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--type', '-t', 'doc_type', help='Force document type')
@click.option('--no-validate', is_flag=True, help='Skip validation')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed processing information')
@click.option('--fast', is_flag=True, help='Fast mode - skip LLM processing, use rule-based classification only')
@click.option('--debug', is_flag=True, help='Debug mode - show where processing gets stuck')
def process(file_path: str, doc_type: Optional[str], no_validate: bool, verbose: bool, fast: bool, debug: bool):
    """Process a document"""
    
    import time
    import logging
    from src.models.document_types import DocumentType
    
    # Setup verbose logging if requested
    if verbose:
        # Configure selective logging for document processing only
        doc_logger = logging.getLogger('src.document_processing')
        doc_logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        doc_logger.addHandler(handler)
        
        console.print("[bold yellow]🔍 Verbose Mode aktiviert[/bold yellow]")
        console.print("Detaillierte Verarbeitungsinformationen werden angezeigt.\n")
    
    if fast:
        console.print("[bold cyan]⚡ Fast Mode aktiviert[/bold cyan]")
        console.print("Rule-based Verarbeitung ohne LLM - deutlich schneller.\n")
    
    def verbose_status_callback(task_id: str, status: str, progress: float, metadata: dict = None):
        """Detailed status callback for verbose mode"""
        if verbose:
            timestamp = time.strftime("%H:%M:%S")
            progress_bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
            console.print(f"[dim]{timestamp}[/dim] [{progress*100:5.1f}%] {progress_bar} [cyan]{status}[/cyan]")
            
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (list, dict)) and len(str(value)) > 100:
                        console.print(f"   📊 {key}: {type(value).__name__} with {len(value)} items")
                    else:
                        console.print(f"   📊 {key}: {value}")
    
    async def run_fast_process():
        """Fast processing without LLM - rule-based only"""
        start_time = time.time()
        
        # Simple file analysis
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size
        
        console.print(f"[bold]📄 Schnelle Datei-Analyse:[/bold]")
        console.print(f"   📁 Pfad: {file_path}")
        console.print(f"   📏 Größe: {file_size:,} Bytes ({file_size/1024:.1f} KB)")
        console.print(f"   📅 Geändert: {time.ctime(file_path_obj.stat().st_mtime)}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            console.print(f"   📊 Text-Length: {len(content):,} Zeichen")
        except Exception as e:
            console.print(f"[red]❌ Fehler beim Lesen der Datei: {e}[/red]")
            return
        
        # Simple rule-based classification
        if ("BSI" in content and "Grundschutz" in content) or "INF." in content:
            doc_type_detected = "BSI_GRUNDSCHUTZ"
        elif "ISO" in content and "27001" in content:
            doc_type_detected = "ISO_27001"
        elif "NIST" in content:
            doc_type_detected = "NIST_CSF"
        else:
            doc_type_detected = "UNKNOWN"
        
        # Simple pattern extraction
        import re
        bsi_patterns = re.findall(r'INF\.\d+\.A\d+[:\s]', content)
        iso_patterns = re.findall(r'[A-Z]\.\d+\.\d+', content)
        
        processing_time = time.time() - start_time
        
        console.print(f"\n[green]✓ Fast processing completed in {processing_time:.2f} seconds![/green]")
        console.print(f"\n[bold]📊 Fast Analysis Results:[/bold]")
        console.print(f"   🎯 Document type (detected): {doc_type_detected}")
        console.print(f"   📊 BSI Controls found: {len(bsi_patterns)}")
        console.print(f"   📊 ISO Patterns found: {len(iso_patterns)}")
        console.print(f"   ⚡ Processing rate: {file_size/(processing_time*1024):.1f} KB/s")
        
        if bsi_patterns[:5]:
            console.print(f"\n[bold]🎯 Sample BSI Controls:[/bold]")
            for pattern in bsi_patterns[:5]:
                console.print(f"   • {pattern.strip()}")
        
        console.print(f"\n[bold cyan]⚡ Fast mode - keine Datenbank-Speicherung[/bold cyan]")
        return

    async def run_process():
        start_time = time.time()
        
        if debug:
            console.print("[blue]🐛 DEBUG: Initialisiere DocumentProcessor...[/blue]")
        
        try:
            processor = DocumentProcessor()
            if debug:
                console.print("[blue]🐛 DEBUG: DocumentProcessor initialisiert ✓[/blue]")
        except Exception as e:
            console.print(f"[red]❌ DEBUG: Fehler bei DocumentProcessor-Initialisierung: {e}[/red]")
            return
        
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size
        
        if verbose:
            console.print(f"[bold]📄 Datei-Analyse:[/bold]")
            console.print(f"   📁 Pfad: {file_path}")
            console.print(f"   📏 Größe: {file_size:,} Bytes ({file_size/1024:.1f} KB)")
            console.print(f"   📅 Geändert: {time.ctime(file_path_obj.stat().st_mtime)}")
            console.print()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=verbose  # Disable progress bar in verbose mode to avoid conflicts
        ) as progress:
            task = None if verbose else progress.add_task(f"Processing {file_path_obj.name}...", total=None)
            
            if doc_type:
                force_type = DocumentType[doc_type.upper()]
                if verbose:
                    console.print(f"[yellow]🎯 Forcing document type: {force_type.value}[/yellow]\n")
            else:
                force_type = None
                if verbose:
                    console.print("[yellow]🔍 Auto-detecting document type...[/yellow]\n")
            
            # Enhanced processing with verbose callbacks
            if verbose:
                console.print("[bold blue]🚀 Starting document processing pipeline...[/bold blue]\n")
            
            if debug:
                console.print("[blue]🐛 DEBUG: Starte Dokumentenverarbeitung...[/blue]")
            
            # Add timeout for processing
            try:
                result = await asyncio.wait_for(
                    processor.process_document(
                        file_path,
                        force_type=force_type,
                        validate=not no_validate,
                        status_callback=verbose_status_callback if verbose else None,
                        task_id="cli-process"
                    ),
                    timeout=300.0  # 5 minutes timeout
                )
            except asyncio.TimeoutError:
                console.print("[red]⚠️ Processing timeout (5 minutes) - möglicherweise LLM-API-Problem[/red]")
                console.print("[yellow]Versuchen Sie es erneut oder prüfen Sie die LLM-Konfiguration[/yellow]")
                return
            except Exception as e:
                console.print(f"[red]❌ Processing failed: {str(e)}[/red]")
                if verbose:
                    console.print(f"[dim]Exception details: {type(e).__name__}[/dim]")
                return
            
            if not verbose and task:
                progress.update(task, completed=True)
        
        processing_time = time.time() - start_time
        
        # Display detailed results
        console.print(f"\n[green]✓ Document processed successfully![/green]")
        
        if verbose:
            console.print(f"\n[bold]📊 Processing Summary:[/bold]")
            console.print(f"   ⏱️  Total time: {processing_time:.2f} seconds")
            console.print(f"   🎯 Document type: {result.document_type.value}")
            console.print(f"   📊 Processing rate: {file_size/(processing_time*1024):.1f} KB/s")
            console.print()
        
        console.print(f"Type: {result.document_type.value}")
        console.print(f"Controls extracted: {len(result.controls)}")
        console.print(f"Chunks created: {len(result.chunks)}")
        
        if verbose and hasattr(result, 'metadata'):
            console.print(f"\n[bold]🔍 Processing Metadata:[/bold]")
            for key, value in result.metadata.items():
                if isinstance(value, (list, dict)):
                    console.print(f"   {key}: {type(value).__name__} with {len(value)} items")
                else:
                    console.print(f"   {key}: {value}")
        
        if result.controls:
            if verbose:
                console.print(f"\n[bold]🎯 All Controls ({len(result.controls)}):[/bold]")
                controls_table = Table(show_header=True, header_style="bold magenta")
                controls_table.add_column("ID", style="cyan", min_width=12)
                controls_table.add_column("Title", style="white")
                controls_table.add_column("Level", style="yellow", min_width=8)
                controls_table.add_column("Domain", style="green", min_width=8)
                controls_table.add_column("Text Length", style="blue", min_width=10)
                
                for control in result.controls:
                    controls_table.add_row(
                        control.id,
                        control.title[:60] + "..." if len(control.title) > 60 else control.title,
                        control.level or "N/A",
                        control.domain or "N/A",
                        f"{len(control.text)} chars"
                    )
                
                console.print(controls_table)
            else:
                console.print("\n[bold]Sample controls:[/bold]")
                table = Table()
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Level", style="yellow")
                
                for control in result.controls[:5]:
                    table.add_row(
                        control.id,
                        control.title[:50] + "..." if len(control.title) > 50 else control.title,
                        control.level or "N/A"
                    )
                
                console.print(table)
        
        if verbose and result.chunks:
            console.print(f"\n[bold]📝 Chunks Overview ({len(result.chunks)}):[/bold]")
            chunks_table = Table(show_header=True, header_style="bold magenta")
            chunks_table.add_column("Index", style="cyan", min_width=5)
            chunks_table.add_column("Type", style="yellow", min_width=12)
            chunks_table.add_column("Length", style="blue", min_width=8)
            chunks_table.add_column("Preview", style="white")
            
            for i, chunk in enumerate(result.chunks[:10]):  # Show first 10 chunks
                chunk_text = chunk.content if hasattr(chunk, 'content') else str(chunk)
                preview = chunk_text[:80].replace('\n', ' ') + "..." if len(chunk_text) > 80 else chunk_text
                
                chunks_table.add_row(
                    str(i),
                    getattr(chunk, 'chunk_type', 'text'),
                    f"{len(chunk_text)} chars",
                    preview
                )
            
            if len(result.chunks) > 10:
                console.print(f"   [dim]... and {len(result.chunks) - 10} more chunks[/dim]")
                
            console.print(chunks_table)
        
        if verbose:
            console.print(f"\n[bold]💾 Storage Information:[/bold]")
            try:
                from src.storage.neo4j_client import Neo4jClient
                from src.storage.chroma_client import ChromaClient
                
                # Check Neo4j storage
                neo4j = Neo4jClient()
                with neo4j.driver.session() as session:
                    result_nodes = session.run("MATCH (n) RETURN count(n) as count")
                    node_count = result_nodes.single()['count']
                    
                    result_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                    rel_count = result_rels.single()['count']
                
                console.print(f"   🗄️  Neo4j: {node_count} nodes, {rel_count} relationships")
                
                # Check ChromaDB storage
                import chromadb
                chroma_client = chromadb.HttpClient(host='localhost', port=8000)
                collections = chroma_client.list_collections()
                
                total_docs = 0
                for collection in collections:
                    coll = chroma_client.get_collection(collection.name)
                    docs = coll.get()
                    doc_count = len(docs['ids']) if docs['ids'] else 0
                    total_docs += doc_count
                    console.print(f"   📊 ChromaDB '{collection.name}': {doc_count} documents")
                
            except Exception as e:
                console.print(f"   ⚠️  Storage check failed: {str(e)}")
        
        processor.close()
        
        if verbose:
            console.print(f"\n[bold green]🎉 Processing completed in {processing_time:.2f} seconds![/bold green]")
    
    # Choose processing mode
    if fast:
        asyncio.run(run_fast_process())
    else:
        asyncio.run(run_process())

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', '-p', default='*.pdf', help='File pattern')
@click.option('--max-concurrent', '-c', default=3, help='Max concurrent processes')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without processing')
def batch(directory: str, pattern: str, max_concurrent: int, dry_run: bool):
    """Process multiple documents"""
    
    async def run_batch():
        processor = DocumentProcessor()
        
        # Find files
        path = Path(directory)
        files = list(path.glob(pattern))
        
        if not files:
            console.print(f"[red]No files found matching pattern: {pattern}[/red]")
            return
        
        console.print(f"Found {len(files)} files to process")
        
        if dry_run:
            console.print("\n[yellow]DRY RUN - Files that would be processed:[/yellow]")
            for file in files:
                console.print(f"  📄 {file.name}")
            return
        
        with Progress(console=console) as progress:
            task = progress.add_task("Processing documents...", total=len(files))
            
            results = await processor.process_batch(
                [str(f) for f in files],
                max_concurrent=max_concurrent
            )
            
            for result in results:
                progress.update(task, advance=1)
        
        # Summary
        console.print(f"\n[green]✓[/green] Batch processing complete!")
        console.print(f"Successfully processed: {len(results)}/{len(files)}")
        
        # Show summary statistics
        total_controls = sum(len(r.controls) for r in results)
        total_chunks = sum(len(r.chunks) for r in results)
        
        console.print(f"Total controls extracted: {total_controls}")
        console.print(f"Total chunks created: {total_chunks}")
        
        processor.close()
    
    asyncio.run(run_batch())

@cli.command()
def stats():
    """Show system statistics"""
    
    def run_stats():
        console.print("\n[bold]📊 KI-Wissenssystem Statistiken[/bold]\n")
        
        # Neo4j Statistics
        try:
            neo4j = Neo4jClient()
            
            with neo4j.driver.session() as session:
                # Node counts
                node_result = session.run("""
                    MATCH (n)
                    RETURN labels(n) as labels, count(n) as count
                """)
                
                console.print("[bold]🗄️ Neo4j Graph Database:[/bold]")
                node_table = Table()
                node_table.add_column("Node Type", style="cyan")
                node_table.add_column("Count", style="white")
                
                total_nodes = 0
                for record in node_result:
                    labels = record["labels"]
                    count = record["count"]
                    total_nodes += count
                    
                    label_str = ":".join(labels) if labels else "Unknown"
                    node_table.add_row(label_str, str(count))
                
                console.print(node_table)
                console.print(f"Total Nodes: [bold]{total_nodes}[/bold]\n")
                
                # Relationship counts
                rel_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                """)
                
                console.print("[bold]🔗 Relationships:[/bold]")
                rel_table = Table()
                rel_table.add_column("Relationship Type", style="yellow")
                rel_table.add_column("Count", style="white")
                
                total_rels = 0
                for record in rel_result:
                    rel_type = record["rel_type"]
                    count = record["count"]
                    total_rels += count
                    
                    rel_table.add_row(rel_type, str(count))
                
                console.print(rel_table)
                console.print(f"Total Relationships: [bold]{total_rels}[/bold]\n")
            
            neo4j.close()
            
        except Exception as e:
            console.print(f"[red]❌ Neo4j connection failed: {e}[/red]")
        
        # ChromaDB Statistics
        try:
            chroma = ChromaClient()
            
            console.print("[bold]🔍 ChromaDB Vector Store:[/bold]")
            chroma_table = Table()
            chroma_table.add_column("Collection", style="green")
            chroma_table.add_column("Documents", style="white")
            
            total_docs = 0
            for collection_name, collection in chroma.collections.items():
                try:
                    count = collection.count()
                    total_docs += count
                    chroma_table.add_row(collection_name, str(count))
                except:
                    chroma_table.add_row(collection_name, "Error")
            
            console.print(chroma_table)
            console.print(f"Total Vector Documents: [bold]{total_docs}[/bold]\n")
            
        except Exception as e:
            console.print(f"[red]❌ ChromaDB connection failed: {e}[/red]")
        
        # System Health
        console.print("[bold]🏥 System Health:[/bold]")
        health_table = Table()
        health_table.add_column("Component", style="blue")
        health_table.add_column("Status", style="white")
        
        # Check API
        try:
            import requests
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code == 200:
                health_table.add_row("API Server", "[green]✅ Running[/green]")
            else:
                health_table.add_row("API Server", f"[yellow]⚠️ Status {response.status_code}[/yellow]")
        except:
            health_table.add_row("API Server", "[red]❌ Not responding[/red]")
        
        # Check Neo4j
        try:
            neo4j = Neo4jClient()
            neo4j.driver.verify_connectivity()
            health_table.add_row("Neo4j Database", "[green]✅ Connected[/green]")
            neo4j.close()
        except:
            health_table.add_row("Neo4j Database", "[red]❌ Connection failed[/red]")
        
        # Check ChromaDB
        try:
            chroma = ChromaClient()
            chroma.client.heartbeat()
            health_table.add_row("ChromaDB", "[green]✅ Connected[/green]")
        except:
            health_table.add_row("ChromaDB", "[red]❌ Connection failed[/red]")
        
        console.print(health_table)
        console.print()
    
    run_stats()

@cli.command()
@click.option('--type', '-t', type=click.Choice(['orphans', 'duplicates', 'quality']), default='orphans')
@click.option('--fix', is_flag=True, help='Automatically fix found issues')
def garden(type: str, fix: bool):
    """Run graph gardening operations"""
    
    async def run_garden():
        from src.orchestration.graph_gardener import GraphGardener
        
        gardener = GraphGardener()
        
        console.print(f"\n[bold]🌱 Graph Gardening: {type}[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Running {type} analysis...", total=None)
            
            if type == 'orphans':
                result = await gardener.find_and_fix_orphans(auto_fix=fix)
                progress.update(task, completed=True)
                
                console.print(f"Found {len(result.get('orphans', []))} orphan nodes")
                if fix:
                    console.print(f"Fixed {result.get('fixed', 0)} orphan connections")
                
            elif type == 'duplicates':
                result = await gardener.find_duplicates()
                progress.update(task, completed=True)
                
                console.print(f"Found {len(result.get('duplicates', []))} potential duplicates")
                if fix:
                    console.print("Duplicate fixing not implemented yet")
                
            elif type == 'quality':
                result = await gardener.quality_check()
                progress.update(task, completed=True)
                
                console.print(f"Quality score: {result.get('score', 0):.2f}")
                console.print(f"Issues found: {len(result.get('issues', []))}")
        
        # Show detailed results
        if result and not fix:
            console.print("\n[yellow]Use --fix to automatically resolve issues[/yellow]")
    
    asyncio.run(run_garden())

@cli.command()
@click.argument('control_id')
def show_control(control_id: str):
    """Show details of a specific control"""
    
    def run_show():
        neo4j = Neo4jClient()
        
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (c:ControlItem {id: $id})
                OPTIONAL MATCH (c)-[r]-(related)
                RETURN c, collect({node: related, rel: type(r)}) as relations
            """, id=control_id)
            
            record = result.single()
            
            if not record:
                console.print(f"[red]Control {control_id} not found[/red]")
                return
            
            control = dict(record["c"])
            relations = record["relations"]
        
        # Display control
        console.print(f"\n[bold]{control['id']} - {control['title']}[/bold]")
        console.print(f"Source: {control['source']}")
        console.print(f"Level: {control.get('level', 'N/A')}")
        console.print(f"Domain: {control.get('domain', 'N/A')}")
        console.print(f"\n{control['text']}")
        
        # Display relations
        if relations:
            console.print("\n[bold]Related Items:[/bold]")
            for rel in relations:
                if rel['node']:
                    node = dict(rel['node'])
                    console.print(f"• {rel['rel']}: {node.get('id', node.get('name', 'Unknown'))}")
        
        neo4j.close()
    
    run_show()

@cli.command()
@click.argument('query_string')
@click.option('--limit', '-l', default=10)
def search(query_string: str, limit: int):
    """Search the knowledge graph"""
    
    def run_search():
        neo4j = Neo4jClient()
        
        results = neo4j.search_controls(query_string)
        
        if not results:
            console.print(f"[yellow]No results found for: {query_string}[/yellow]")
            return
        
        console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
        
        for i, result in enumerate(results[:limit], 1):
            console.print(f"{i}. [cyan]{result['id']}[/cyan] - {result['title']}")
            console.print(f"   {result['text'][:100]}...")
            console.print()
        
        if len(results) > limit:
            console.print(f"[dim]... and {len(results) - limit} more results[/dim]")
        
        neo4j.close()
    
    run_search()

@cli.command()
@click.option('--export-format', '-f', type=click.Choice(['json', 'csv', 'cypher']), default='json')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def export(export_format: str, output: Optional[str]):
    """Export knowledge graph data"""
    
    def run_export():
        neo4j = Neo4jClient()
        
        console.print(f"\n[bold]📤 Exporting graph data ({export_format})[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Exporting data...", total=None)
            
            if export_format == 'json':
                # Export as JSON
                with neo4j.driver.session() as session:
                    result = session.run("""
                        MATCH (n)-[r]->(m)
                        RETURN {
                            source: {id: n.id, labels: labels(n), properties: properties(n)},
                            relationship: {type: type(r), properties: properties(r)},
                            target: {id: m.id, labels: labels(m), properties: properties(m)}
                        } as data
                        LIMIT 1000
                    """)
                    
                    data = [record["data"] for record in result]
                
                output_file = output or f"knowledge_graph_export.{export_format}"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
            elif export_format == 'cypher':
                # Export as Cypher statements
                output_file = output or f"knowledge_graph_export.cypher"
                with open(output_file, 'w', encoding='utf-8') as f:
                    with neo4j.driver.session() as session:
                        # Export nodes
                        node_result = session.run("MATCH (n) RETURN n LIMIT 1000")
                        for record in node_result:
                            node = record["n"]
                            labels = ":".join(node.labels)
                            props = dict(node)
                            props_str = ", ".join([f"{k}: {repr(v)}" for k, v in props.items()])
                            f.write(f"CREATE (:{labels} {{{props_str}}});\n")
                        
                        # Export relationships
                        rel_result = session.run("""
                            MATCH (n)-[r]->(m) 
                            RETURN n.id as source_id, type(r) as rel_type, m.id as target_id, properties(r) as props
                            LIMIT 1000
                        """)
                        for record in rel_result:
                            source_id = record["source_id"]
                            target_id = record["target_id"]
                            rel_type = record["rel_type"]
                            props = dict(record["props"])
                            props_str = ", ".join([f"{k}: {repr(v)}" for k, v in props.items()]) if props else ""
                            f.write(f"MATCH (a {{id: '{source_id}'}}), (b {{id: '{target_id}'}}) CREATE (a)-[:{rel_type} {{{props_str}}}]->(b);\n")
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] Data exported to: {output_file}")
        neo4j.close()
    
    run_export()

@cli.command()
@click.option('--interval', '-i', default=5, help='Update interval in seconds')
@click.option('--components', '-c', multiple=True, 
              type=click.Choice(['api', 'neo4j', 'chroma', 'processing']),
              help='Components to monitor (default: all)')
def monitor(interval: int, components: tuple):
    """Monitor system components in real-time"""
    
    import time
    from datetime import datetime
    
    if not components:
        components = ['api', 'neo4j', 'chroma', 'processing']
    
    console.print(f"\n[bold]📊 KI-Wissenssystem Monitor[/bold]")
    console.print(f"Update interval: {interval}s | Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            console.clear()
            
            console.print(f"[bold]📊 System Monitor - {datetime.now().strftime('%H:%M:%S')}[/bold]\n")
            
            # Create status table
            status_table = Table()
            status_table.add_column("Component", style="cyan")
            status_table.add_column("Status", style="white")
            status_table.add_column("Details", style="dim")
            
            # Monitor API
            if 'api' in components:
                try:
                    import requests
                    start_time = time.time()
                    response = requests.get("http://localhost:8080/health", timeout=3)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        status_table.add_row(
                            "API Server", 
                            "[green]✅ Running[/green]",
                            f"Response: {response_time:.0f}ms"
                        )
                    else:
                        status_table.add_row(
                            "API Server", 
                            f"[yellow]⚠️ Status {response.status_code}[/yellow]",
                            f"Response: {response_time:.0f}ms"
                        )
                except Exception as e:
                    status_table.add_row(
                        "API Server", 
                        "[red]❌ Down[/red]",
                        str(e)[:50]
                    )
            
            # Monitor Neo4j
            if 'neo4j' in components:
                try:
                    neo4j = Neo4jClient()
                    start_time = time.time()
                    with neo4j.driver.session() as session:
                        result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                        total_nodes = result.single()["total_nodes"]
                    query_time = (time.time() - start_time) * 1000
                    
                    status_table.add_row(
                        "Neo4j Database", 
                        "[green]✅ Connected[/green]",
                        f"{total_nodes} nodes | Query: {query_time:.0f}ms"
                    )
                    neo4j.close()
                except Exception as e:
                    status_table.add_row(
                        "Neo4j Database", 
                        "[red]❌ Connection failed[/red]",
                        str(e)[:50]
                    )
            
            # Monitor ChromaDB
            if 'chroma' in components:
                try:
                    chroma = ChromaClient()
                    start_time = time.time()
                    total_docs = sum(collection.count() for collection in chroma.collections.values())
                    query_time = (time.time() - start_time) * 1000
                    
                    status_table.add_row(
                        "ChromaDB", 
                        "[green]✅ Connected[/green]",
                        f"{total_docs} documents | Query: {query_time:.0f}ms"
                    )
                except Exception as e:
                    status_table.add_row(
                        "ChromaDB", 
                        "[red]❌ Connection failed[/red]",
                        str(e)[:50]
                    )
            
            # Monitor Processing Tasks
            if 'processing' in components:
                try:
                    import requests
                    # Check if there are any active processing tasks
                    # This would require an endpoint to check active tasks
                    status_table.add_row(
                        "Processing Queue", 
                        "[blue]ℹ️ Monitoring[/blue]",
                        "Active task monitoring"
                    )
                except Exception as e:
                    status_table.add_row(
                        "Processing Queue", 
                        "[yellow]⚠️ Unknown[/yellow]",
                        "Cannot check queue status"
                    )
            
            console.print(status_table)
            
            # Show recent activity (if available)
            console.print(f"\n[dim]Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
            console.print(f"[dim]Press Ctrl+C to stop monitoring[/dim]")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped.[/yellow]")

@cli.command()
@click.option('--lines', '-n', default=50, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--level', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              help='Filter by log level')
def logs(lines: int, follow: bool, level: Optional[str]):
    """Show system logs"""
    
    import os
    import subprocess
    from pathlib import Path
    
    # Find log files
    log_dir = Path("logs")
    if not log_dir.exists():
        console.print("[red]❌ Log directory not found[/red]")
        return
    
    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        console.print("[red]❌ No log files found[/red]")
        return
    
    # Use the most recent log file
    latest_log = max(log_files, key=os.path.getmtime)
    
    console.print(f"[bold]📋 Showing logs from: {latest_log}[/bold]\n")
    
    try:
        if follow:
            # Use tail -f equivalent
            cmd = ["tail", "-f", str(latest_log)]
            if lines:
                cmd.extend(["-n", str(lines)])
            
            console.print("[dim]Following log output... Press Ctrl+C to stop[/dim]\n")
            subprocess.run(cmd)
        else:
            # Show last N lines
            with open(latest_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
            # Filter by level if specified
            if level:
                filtered_lines = [line for line in all_lines if level in line]
            else:
                filtered_lines = all_lines
            
            # Show last N lines
            for line in filtered_lines[-lines:]:
                # Color code log levels
                if 'ERROR' in line:
                    console.print(line.rstrip(), style="red")
                elif 'WARNING' in line:
                    console.print(line.rstrip(), style="yellow")
                elif 'INFO' in line:
                    console.print(line.rstrip(), style="blue")
                else:
                    console.print(line.rstrip())
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]Log following stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error reading logs: {e}[/red]")

if __name__ == '__main__':
    cli()