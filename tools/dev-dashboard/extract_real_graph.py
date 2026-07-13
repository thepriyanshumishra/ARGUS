#!/usr/bin/env python3
"""
Real ARGUS codebase graph extractor using AST parsing.
Generates actual nodes/edges from the source code.
"""
import ast
import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Optional

ROOT = Path("/Users/thedarkpcm/Desktop/Priyanshu/ARGUS")
SRC_DIRS = [ROOT / "src", ROOT / "tools" / "dev-dashboard"]

@dataclass
class Node:
    id: str
    label: str
    type: str
    module: str
    layer: str
    file: str
    line: int
    in_degree: int = 0
    out_degree: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class Edge:
    id: str
    source: str
    target: str
    type: str

class GraphExtractor(ast.NodeVisitor):
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.imports = defaultdict(set)  # file -> set of imported modules
        self.current_file = ""
        self.current_module = ""
        self.current_layer = ""
        self.class_stack = []
        self.function_stack = []
        
    def get_layer(self, filepath: Path) -> str:
        """Determine architecture layer from path."""
        parts = filepath.parts
        if 'vision' in parts: return 'core'
        if 'graph' in parts: return 'core'
        if 'analytics' in parts: return 'core'
        if 'simulation' in parts: return 'data'
        if 'routing' in parts: return 'core'
        if 'dashboard' in parts: return 'dashboard'
        if 'cli' in parts: return 'api'
        if 'core' in parts: return 'core'
        if 'tests' in parts: return 'test'
        return 'unknown'
    
    def get_module(self, filepath: Path) -> str:
        """Determine module from path."""
        parts = filepath.parts
        for i, p in enumerate(parts):
            if p == 'argus' and i + 1 < len(parts):
                return parts[i + 1]
        return 'argus'
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports[self.current_file].add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports[self.current_file].add(node.module)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        node_id = f"{self.current_file}:{node.name}"
        self.nodes[node_id] = Node(
            id=node_id,
            label=node.name,
            type='class',
            module=self.current_module,
            layer=self.current_layer,
            file=self.current_file,
            line=node.lineno
        )
        self.class_stack.append(node_id)
        
        # Inheritance edges
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_id = f"{self.current_file}:{base.id}"
                self.edges.append(Edge(
                    id=f"{node_id}->inherits->{base_id}",
                    source=node_id,
                    target=base_id,
                    type='inherits'
                ))
        
        self.generic_visit(node)
        self.class_stack.pop()
    
    def visit_FunctionDef(self, node):
        parent = self.class_stack[-1] if self.class_stack else None
        prefix = parent if parent else self.current_file
        node_id = f"{prefix}:{node.name}"
        
        node_type = 'method' if parent else 'function'
        self.nodes[node_id] = Node(
            id=node_id,
            label=node.name,
            type=node_type,
            module=self.current_module,
            layer=self.current_layer,
            file=self.current_file,
            line=node.lineno
        )
        
        if parent:
            self.edges.append(Edge(
                id=f"{parent}->contains->{node_id}",
                source=parent,
                target=node_id,
                type='contains'
            ))
        
        self.function_stack.append(node_id)
        self.generic_visit(node)
        self.function_stack.pop()
    
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
    
    def visit_Call(self, node):
        # Track function calls
        if isinstance(node.func, ast.Name):
            callee = node.func.id
            caller = self.function_stack[-1] if self.function_stack else self.class_stack[-1] if self.class_stack else self.current_file
            if caller and callee:
                self.edges.append(Edge(
                    id=f"{caller}->calls->{callee}",
                    source=caller,
                    target=f"{self.current_file}:{callee}",
                    type='calls'
                ))
        elif isinstance(node.func, ast.Attribute):
            # method calls
            caller = self.function_stack[-1] if self.function_stack else self.class_stack[-1] if self.class_stack else self.current_file
            if caller:
                self.edges.append(Edge(
                    id=f"{caller}->calls->{node.func.attr}",
                    source=caller,
                    target=f"{self.current_file}:{node.func.attr}",
                    type='calls'
                ))
        self.generic_visit(node)

def extract_graph():
    extractor = GraphExtractor()
    python_files = list(ROOT.rglob("*.py"))
    
    # Filter out venv, node_modules, __pycache__
    python_files = [f for f in python_files if '.venv' not in str(f) and '__pycache__' not in str(f) and 'node_modules' not in str(f)]
    
    print(f"Found {len(python_files)} Python files")
    
    for filepath in python_files:
        try:
            rel_path = filepath.relative_to(ROOT)
            extractor.current_file = str(rel_path)
            extractor.current_module = extractor.get_module(filepath)
            extractor.current_layer = extractor.get_layer(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(filepath))
            extractor.visit(tree)
            
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    # Add import edges
    for file, imports in extractor.imports.items():
        file_node_id = f"{file}:__module__"
        if file_node_id not in extractor.nodes:
            extractor.nodes[file_node_id] = Node(
                id=file_node_id,
                label=Path(file).name,
                type='file',
                module=extractor.get_module(Path(file)),
                layer=extractor.get_layer(Path(file)),
                file=file,
                line=1
            )
        
        for imp in imports:
            # Find matching module nodes
            for node_id, node in extractor.nodes.items():
                if node.module == imp or node.label == imp.split('.')[-1]:
                    extractor.edges.append(Edge(
                        id=f"{file_node_id}->imports->{node_id}",
                        source=file_node_id,
                        target=node_id,
                        type='imports'
                    ))
                    break
    
    # Calculate degrees
    for edge in extractor.edges:
        if edge.source in extractor.nodes:
            extractor.nodes[edge.source].out_degree += 1
        if edge.target in extractor.nodes:
            extractor.nodes[edge.target].in_degree += 1
    
    # Assign positions using force-directed layout (simple version)
    assign_positions(list(extractor.nodes.values()), extractor.edges)
    
    # Convert to dict
    nodes_list = list(extractor.nodes.values())
    edges_list = extractor.edges
    
    # Filter to unique edges
    seen_edges = set()
    unique_edges = []
    for e in edges_list:
        key = (e.source, e.target, e.type)
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)
    
    return nodes_list, unique_edges

def assign_positions(nodes, edges):
    """Simple force-directed layout."""
    import random
    import math
    
    # Initialize random positions in sphere
    for node in nodes:
        r = 100 + random.random() * 150
        theta = random.random() * 2 * math.pi
        phi = math.acos(2 * random.random() - 1)
        node.x = r * math.sin(phi) * math.cos(theta)
        node.y = r * math.sin(phi) * math.sin(theta)
        node.z = r * math.cos(phi)
    
    # Build adjacency
    adj = defaultdict(list)
    for edge in edges:
        if edge.source in [n.id for n in nodes] and edge.target in [n.id for n in nodes]:
            adj[edge.source].append(edge.target)
            adj[edge.target].append(edge.source)
    
    # Force-directed iterations
    k = 50  # ideal spring length
    for iteration in range(50):
        forces = {n.id: [0.0, 0.0, 0.0] for n in nodes}
        
        # Repulsion
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                dx = n1.x - n2.x
                dy = n1.y - n2.y
                dz = n1.z - n2.z
                dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
                force = k * k / dist
                fx = force * dx / dist
                fy = force * dy / dist
                fz = force * dz / dist
                forces[n1.id][0] += fx
                forces[n1.id][1] += fy
                forces[n1.id][2] += fz
                forces[n2.id][0] -= fx
                forces[n2.id][1] -= fy
                forces[n2.id][2] -= fz
        
        # Attraction (edges)
        for edge in edges:
            if edge.source not in forces or edge.target not in forces:
                continue
            n1 = next(n for n in nodes if n.id == edge.source)
            n2 = next(n for n in nodes if n.id == edge.target)
            dx = n2.x - n1.x
            dy = n2.y - n1.y
            dz = n2.z - n1.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
            force = dist * dist / k
            fx = force * dx / dist
            fy = force * dy / dist
            fz = force * dz / dist
            forces[edge.source][0] += fx
            forces[edge.source][1] += fy
            forces[edge.source][2] += fz
            forces[edge.target][0] -= fx
            forces[edge.target][1] -= fy
            forces[edge.target][2] -= fz
        
        # Apply forces with cooling
        temp = 10.0 * (1 - iteration / 50)
        for node in nodes:
            fx, fy, fz = forces[node.id]
            node.x += fx * temp * 0.01
            node.y += fy * temp * 0.01
            node.z += fz * temp * 0.01

if __name__ == "__main__":
    nodes, edges = extract_graph()
    
    output = {
        "metadata": {
            "project": "ARGUS",
            "lastIndexed": __import__('datetime').datetime.now().isoformat(),
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "modules": list(set(n.module for n in nodes)),
            "layers": list(set(n.layer for n in nodes))
        },
        "nodes": [asdict(n) for n in nodes],
        "edges": [asdict(e) for e in edges]
    }
    
    out_path = ROOT / "tools" / "dev-dashboard" / "real_graph_data.json"
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Extracted {len(nodes)} nodes, {len(edges)} edges")
    print(f"Saved to {out_path}")
    
    # Print summary by type
    type_counts = defaultdict(int)
    for n in nodes:
        type_counts[n.type] += 1
    print("\nNode types:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    
    layer_counts = defaultdict(int)
    for n in nodes:
        layer_counts[n.layer] += 1
    print("\nLayers:")
    for l, c in sorted(layer_counts.items(), key=lambda x: -x[1]):
        print(f"  {l}: {c}")
