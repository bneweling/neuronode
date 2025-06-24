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
from rich.syntax import Syntax

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
def process(file_path: str, doc_type: Optional[str], no_validate: bool):
    """Process a document"""
    
    async def run_process():
        processor = DocumentProcessor()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Processing {Path(file_path).name}...", total=None)
            
            if doc_type:
                from src.models.document_types import DocumentType
                force_type = DocumentType[doc_type.upper()]
            else:
                force_type = None
            
            result = await processor.process_document(
                file_path,
                force_type=force_type,
                validate=not no_validate
            )
            
            progress.update(task, completed=True)
        
        # Display results
        console.print(f"\n[green]✓[/green] Document processed successfully!")
        console.print(f"Type: {result.document_type.value}")
        console.print(f"Controls extracted: {len(result.controls)}")
        console.print(f"Chunks created: {len(result.chunks)}")
        
        if result.controls:
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
        
        processor.close()
    
    asyncio.run(run_process())

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', '-p', default='*.pdf', help='File pattern')
@click.option('--max-concurrent', '-c', default=3, help='Max concurrent processes')
def batch(directory: str, pattern: str, max_concurrent: int):
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
        
        processor.close()
    
    asyncio.run(run_batch())

@cli.command()
def stats():
    """Show knowledge graph statistics"""
    
    def run_stats():
        neo4j = Neo4jClient()
        chroma = ChromaClient()
        
        # Neo4j stats
        with neo4j.driver.session() as session:
            # Node counts
            node_counts = {}
            for label in ["ControlItem", "KnowledgeChunk", "Technology", "Entity"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                node_counts[label] = result.single()["count"]
            
            # Relationship counts
            rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            rel_counts = {record["type"]: record["count"] for record in rel_result}
        
        # Display Neo4j stats
        console.print("\n[bold]Neo4j Knowledge Graph:[/bold]")
        
        table = Table(title="Nodes")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")
        
        for node_type, count in node_counts.items():
            table.add_row(node_type, str(count))
        
        console.print(table)
        
        table = Table(title="Relationships")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")
        
        for rel_type, count in rel_counts.items():
            table.add_row(rel_type, str(count))
        
        console.print(table)
        
        # ChromaDB stats
        console.print("\n[bold]ChromaDB Vector Store:[/bold]")
        
        table = Table(title="Collections")
        table.add_column("Collection", style="cyan")
        table.add_column("Documents", justify="right")
        
        for name, collection in chroma.collections.items():
            table.add_row(name, str(collection.count()))
        
        console.print(table)
        
        neo4j.close()
    
    run_stats()

@cli.command()
@click.option('--focus', '-f', type=click.Choice(['orphans', 'technologies', 'cross_reference']), 
              default='orphans')
def garden(focus: str):
    """Run graph gardening cycle"""
    
    async def run_garden():
        gardener = GraphGardener()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Running {focus} gardening...", total=None)
            
            result = await gardener.run_gardening_cycle(focus)
            
            progress.update(task, completed=True)
        
        if 'error' in result:
            console.print(f"[red]Error: {result['error']}[/red]")
        else:
            console.print(f"\n[green]✓[/green] Gardening complete!")
            console.print(f"Duration: {result['duration']:.2f}s")
            
            if 'stats' in result:
                for key, value in result['stats'].items():
                    console.print(f"{key}: {value}")
    
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

if __name__ == '__main__':
    cli()